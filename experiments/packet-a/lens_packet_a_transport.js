/* Conversation Lens Packet A — connected Stop/Keep/Drop transport.
 * Source-agnostic controller: the UI owns the microphone and PCM timeline;
 * this module owns localhost lease transitions and exact WAV uploads.
 * No automatic enrollment or speaker-vector mutations.
 */
(function (root, factory) {
  const api = factory(root, typeof module === 'object' && module.exports ? require('./lens_stop_client.js') : root.LensStopClient);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.LensPacketATransport = api;
})(typeof globalThis === 'undefined' ? undefined : globalThis, function (root, StopClient) {
  'use strict';
  const { StopWindowQueue, digestHex } = StopClient;
  const validWindow = /^[A-Za-z0-9_-]{1,40}$/;
  const assert = (ok, message) => {if (!ok) throw Error(message)};

  class PacketATransport {
    constructor({ fetchImpl = (...args) => root.fetch(...args), digest = digestHex,
                  onState = () => {}, onWindow = () => {} } = {}) {
      assert(typeof fetchImpl === 'function' && typeof digest === 'function', 'Fetch and SHA-256 functions required');
      this.fetchImpl = fetchImpl;
      this.digest = digest;
      this.onState = onState;
      this.onWindow = onWindow;
      this.phase = 'offline';
      this.token = '';
      this.capture = '';
      this.engine = '';
      this.queue = null;
      this.lastManifest = [];
      this.results = [];
      this.generation = 0;
      this.controller = null;
    }
    state(phase, details = '') {
      this.phase = phase;
      this.onState({ phase, details, engine: this.engine });
    }
    async _json(path, body, signal) {
      assert(!!this.token, 'Local server token not loaded');
      const response = await this.fetchImpl(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Lens-Token': this.token },
        body: JSON.stringify(body), signal,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = Error(data.error || 'Local request failed (' + response.status + ')');
        error.httpStatus = response.status;
        throw error;
      }
      return data;
    }
    async connect() {
      assert(this.phase === 'offline' || this.phase === 'ready', 'Cannot reconnect during capture');
      try {
        const response = await this.fetchImpl('/api/status', {cache:'no-store'});
        if (!response.ok) throw Error('Local status unavailable');
        const data = await response.json();
        assert(data.app === 'lens-packet-a' && data.protocol === 1 && typeof data.token === 'string' && data.token.length > 12,
          'Not the Packet A validation server');
        this.token = data.token;
        this.engine = data.engine;
        this.state('ready', data.engine === 'whisper-cpp' ? 'Local Whisper configured' : 'Audio validation only — transcription unavailable');
        return data;
      } catch (error) {
        this.token = '';
        this.engine = '';
        this.state('offline', 'No matching local Packet A server: ' + error.message);
        throw error;
      }
    }
    async open({ takeover = false } = {}) {
      assert(this.phase === 'ready', 'Open only from ready state');
      const data = await this._json('/api/capture/open', {takeover});
      assert(typeof data.capture === 'string' && data.capture.length >= 12, 'Malformed capture lease');
      this.capture = data.capture;
      this.generation++;
      this.queue = null;
      this.results = [];
      this.lastManifest = [];
      this.state('live', 'Capture lease active');
      return data;
    }
    async freeze() {
      assert(this.phase === 'live' && this.capture, 'Only an active capture can freeze');
      const revision = ++this.generation;
      this.state('freezing', 'Mic halted; revoking live admission');
      try {
        const result = await this._json('/api/capture/freeze', {capture:this.capture});
        if (revision !== this.generation) throw Error('Stop freeze canceled');
        assert(result.frozen === true, 'Server did not confirm capture freeze');
        this.state('frozen', 'Server intake frozen; select at most four windows');
        return result;
      } catch (error) {
        // Caller must never attempt Keep/Drain against a lease with unknown freeze state.
        if (revision === this.generation) {
          const token=this.capture;
          this.state('failed','Could not verify Stop freeze: '+error.message);
          try {
            const result=await this._json('/api/capture/close',{capture:token});
            if(result.closed===true)this.capture='';
          } catch (_) {
            // Preserve the uncertain token so Erase can retry. TTL remains the
            // server fallback; never silently claim that the lease is closed.
            this.capture=token;
          }
        }
        throw error;
      }
    }
    async submitSelection(selected) {
      assert(this.phase === 'frozen', 'Server must acknowledge freeze before Keep is available');
      assert(Array.isArray(selected) && selected.length >= 0 && selected.length <= 4, 'Select no more than four windows');
      const seen = new Set();
      for (const item of selected) {
        assert(item && validWindow.test(item.id || '') && !seen.has(item.id), 'Invalid or repeated window');
        seen.add(item.id);
      }
      if (selected.length === 0) {
        await this.close();
        return {kept:0, done:0, failed:0, results:[]};
      }
      const revision = this.generation;
      const queue = new StopWindowQueue({maxPending:4, digest:this.digest});
      queue.bindCapture(this.capture);
      for (const item of selected) queue.add(item);
      queue.beginStop();
      queue.confirmFrozen();
      const manifest = await queue.manifest();
      assert(this.phase === 'frozen' && this.generation === revision, 'Selection canceled before authorization');
      // No upload begins until server authorizes every EXACT hash.
      const oldCapture = this.capture;
      const authorized = await this._json('/api/capture/drain', {capture:oldCapture,windows:manifest});
      if (this.generation !== revision || this.phase !== 'frozen') {
        if (authorized.capture) {
          try {await this._json('/api/capture/close',{capture:authorized.capture});} catch (_) {}
        }
        throw Error('Drain canceled after authorization');
      }
      assert(typeof authorized.capture === 'string' && authorized.capture.length >= 12, 'Malformed drain lease');
      assert(Number.isFinite(authorized.deadlineSeconds) && authorized.deadlineSeconds > 0, 'Malformed drain deadline');
      queue.authorizeDrain(authorized.capture,authorized.deadlineSeconds);
      this.capture = authorized.capture;
      this.queue = queue;
      this.lastManifest = manifest.map(item=>({...item}));
      this.state('draining', 'Processing ' + manifest.length + ' approved WAV windows');
      const outcomes = [];
      let leaseClosed=false;
      try {
        let job;
        while (this.generation === revision && (job = queue.nextDrain())) {
          const abort = new AbortController();
          this.controller = abort;
          try {
            let response=null,payload={},busyTries=0;
            const startedAt=Date.now();
            do {
              if (this.generation !== revision || this.phase !== 'draining') break;
              response = await this.fetchImpl('/api/transcribe', {
                method:'POST',signal:abort.signal,
                headers: {
                  'Content-Type':'audio/wav',
                  'X-Lens-Token':this.token,
                  'X-Lens-Capture-Session':job.capture,
                  'X-Lens-Window-ID':job.id,
                  'X-Lens-Force-Mixed':job.forceMixed ? 'true':'false',
                },
                body:new Blob([job.wav],{type:'audio/wav'}),
              });
              payload=await response.json().catch(()=>({}));
              if (response.status !== 429 || payload.retryable !== true ||
                  busyTries>=34 || Date.now()-startedAt>=40000) break;
              busyTries++;
              this.state('draining','Whisper busy; retrying authorized window '+job.id+
                ' (attempt '+(busyTries+1)+')');
              await new Promise(resolve=>setTimeout(resolve,Math.min(1250,250+busyTries*170)));
            } while (true);
            if (this.generation !== revision || this.phase !== 'draining' || !response) break;
            if (!response.ok || payload.discarded) {
              const reason = payload.discarded ? 'Result dropped after capture change' :
                (payload.error || 'WAV upload failed (' + response.status + ')');
              queue.failDrain(job.id,job.nonce,reason);
              const event = {id:job.id,ok:false,reason};
              outcomes.push(event);this.onWindow(event);
              continue;
            }
            const accepted = queue.finishDrain(job.id,job.nonce,payload);
            if (!accepted) continue;
            const event={id:job.id,ok:true,frames:payload.frames,engine:payload.engine,
              text:typeof payload.text === 'string' ? payload.text : null,
              forceMixed:job.forceMixed};
            outcomes.push(event);this.results.push(event);this.onWindow(event);
          } catch(error) {
            if (this.generation !== revision || this.phase !== 'draining') break;
            queue.failDrain(job.id,job.nonce,error.message || 'Upload failed');
            const event={id:job.id,ok:false,reason:error.message || 'Upload failed'};
            outcomes.push(event);this.onWindow(event);
          } finally {
            if (this.controller === abort) this.controller=null;
          }
        }
      } finally {
        if (this.generation === revision) {
          const closeResult=await this.close();
          leaseClosed=closeResult.closed === true;
        }
      }
      return {kept:selected.length,done:outcomes.filter(x=>x.ok).length,
        failed:outcomes.filter(x=>!x.ok).length,results:outcomes,leaseClosed};
    }
    async close() {
      const token = this.capture;
      this.generation++;
      try {this.controller?.abort()} catch (_) {}
      this.controller = null;
      this.queue?.close('Owner closed drain');
      if (!token || !this.token) {
        this.capture='';
        this.state(this.token ? 'ready' : 'offline', 'No outstanding capture lease');
        return {closed:true,alreadyClosed:true};
      }
      this.state('closing','Awaiting server confirmation that the capture lease was revoked');
      try {
        const result=await this._json('/api/capture/close',{capture:token});
        this.capture='';
        if (result.closed !== true) {
          this.state('ready','Capture already superseded; server did not close this token');
          return {closed:false,superseded:true};
        }
        this.state('ready','Server confirmed capture lease closure');
        return {closed:true};
      } catch(error) {
        // Retain the token for an explicit retry, rather than falsely claiming
        // that the server completed Stop while the lease may remain active.
        this.capture=token;
        this.state('failed','Server closure unverified: '+error.message);
        return {closed:false,reason:error.message};
      }
    }
  }
  return {PacketATransport};
});
