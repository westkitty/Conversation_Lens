/* Conversation Lens — bounded browser-side Stop window disposition.
 * Drives a two-phase local STOP: freeze on server, choose exact clips, mint a drain-only lease.
 * Browser and Node; no storage, network, DOM, microphone or clock side effects by itself.
 */
(function (root, factory) {
  const exports = factory();
  if (typeof module === 'object' && module.exports) module.exports = exports;
  if (root) root.LensStopClient = exports;
})(typeof globalThis === 'undefined' ? undefined : globalThis, function () {
  'use strict';
  const MAX_AUDIO_BYTES = 320044; // 10 s, 16 kHz mono PCM16 WAV + 44-byte header
  const DEFAULT_MAX_PENDING = 4;
  const VALID_ID = /^[A-Za-z0-9_-]{1,40}$/;
  const check = (condition, message) => { if (!condition) throw new RangeError(message); };

  function isPCM16MonoWav(bytes) {
    if (!(bytes instanceof Uint8Array) || bytes.length < 500 || bytes.length > MAX_AUDIO_BYTES) return false;
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const word = (offset, str) => [...str].every((character,i)=>bytes[offset+i] === character.charCodeAt(0));
    return word(0, 'RIFF') && word(8, 'WAVE') && word(12, 'fmt ') && word(36, 'data') &&
      view.getUint32(4,true) === bytes.length-8 &&
      view.getUint16(20,true) === 1 && view.getUint16(22,true) === 1 &&
      view.getUint32(24,true) === 16000 && view.getUint32(28,true) === 32000 && view.getUint16(34,true) === 16 &&
      view.getUint16(32,true) === 2 && view.getUint32(40,true) === bytes.length-44;
  }
  async function digestHex(bytes, cryptoImpl = globalThis.crypto) {
    check(cryptoImpl?.subtle?.digest, 'SHA-256 must be available in secure localhost context');
    const copy = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const hashed = await cryptoImpl.subtle.digest('SHA-256', copy);
    return [...new Uint8Array(hashed)].map(byte=>byte.toString(16).padStart(2,'0')).join('');
  }

  class StopWindowQueue {
    constructor({ maxPending = DEFAULT_MAX_PENDING, now = () => performance.now(), digest = digestHex } = {}) {
      check(Number.isSafeInteger(maxPending) && maxPending>=1 && maxPending<=4, 'At most four pending clips');
      check(typeof now === 'function' && typeof digest === 'function', 'Clock and digest required');
      this.maxPending=maxPending;this.now=now;this.digest=digest;
      this.phase='live';this.jobs=new Map();this.order=[];
      this.frozenAt=null;this.drainUntil=null;this.drainToken='';this.captureID='';
      this.errors=[];
    }
    bindCapture(token){
      check(this.phase==='live' && this.jobs.size===0, 'Bind capture before audio');
      check(typeof token==='string' && token.length>=12, 'Capture lease missing');
      this.captureID=token;
    }
    add({ id, wav, forceMixed = false, sourceStart = null, sourceEnd = null } = {}) {
      check(this.phase==='live' && this.captureID, 'Capture not in intake state');
      check(VALID_ID.test(id || '') && !this.jobs.has(id), 'Duplicate or invalid window ID');
      check(isPCM16MonoWav(wav), 'Clip must be 16 kHz PCM WAV <=10s');
      check(typeof forceMixed==='boolean', 'Overlap flag required');
      const pending=[...this.jobs.values()].filter(x=>x.state==='ready'||x.state==='sending').length;
      check(pending<this.maxPending,'Pending clip cap; pause intake or drop an old window');
      const job={id,wav:new Uint8Array(wav),forceMixed,sourceStart,sourceEnd,state:'ready',keep:true,
        result:null,reason:null,submittedCapture:null,requestNonce:0};
      this.jobs.set(id,job);this.order.push(id);return this.viewJob(job);
    }
    viewJob(job){return {id:job.id,state:job.state,keep:job.keep,bytes:job.wav?.byteLength||0,
      forceMixed:job.forceMixed,sourceStart:job.sourceStart,sourceEnd:job.sourceEnd,
      reason:job.reason};}
    list(){return this.order.map(id=>this.viewJob(this.jobs.get(id)));}
    get(id){const job=this.jobs.get(id);check(!!job,'Unknown window ID');return job;}
    startLive(id){
      check(this.phase==='live','Capture no longer accepts live uploads');
      const job=this.get(id);check(job.state==='ready','Window is not pending');
      job.state='sending';job.requestNonce++;job.submittedCapture=this.captureID;
      return {wav:new Uint8Array(job.wav),capture:this.captureID,id,forceMixed:job.forceMixed,
        nonce:job.requestNonce,autoNamesAllowed:!job.forceMixed};
    }
    finishLive(id,nonce,response){
      const job=this.jobs.get(id);
      if(this.phase!=='live'||!job||job.state!=='sending'||job.requestNonce!==nonce)return false;
      job.state='done';job.result=response;job.wav=null;return true;
    }
    beginStop(){
      check(this.phase==='live' && this.captureID,'No live capture to stop');
      this.phase='freezing';this.frozenAt=this.now();
      // Caller MUST stop microphone immediately, then POST /api/capture/freeze before
      // granting Keep/Drop controls. In-flight live upload results are ignored hereafter.
      return {capture:this.captureID,windows:this.list().filter(j=>j.state==='ready'||j.state==='sending')};
    }
    confirmFrozen(){
      check(this.phase==='freezing','No freeze awaiting acknowledgement');
      this.phase='choosing';return this.list().filter(x=>x.state==='ready'||x.state==='sending');
    }
    choose(id,keep){
      check(this.phase==='choosing','Window disposition only after freeze acknowledgement');
      check(typeof keep==='boolean','Keep must be explicit true/false');
      const job=this.get(id);check(['ready','sending'].includes(job.state),'Completed window cannot be chosen');
      job.keep=keep;return this.viewJob(job);
    }
    async manifest(){
      check(this.phase==='choosing','Not ready to authorize exact drain');
      const jobs=this.order.map(id=>this.jobs.get(id)).filter(x=>x.keep&&['ready','sending'].includes(x.state));
      check(jobs.length<=this.maxPending,'Too many kept windows');
      return Promise.all(jobs.map(async job=>({window_id:job.id,
        sha256:await this.digest(job.wav),force_mixed:job.forceMixed})));
    }
    authorizeDrain(token,deadlineSeconds=120){
      check(this.phase==='choosing','Capture not frozen');
      check(typeof token==='string'&&token.length>=12,'Drain-only token missing');
      check(Number.isFinite(deadlineSeconds)&&deadlineSeconds>0&&deadlineSeconds<=120,
        'Invalid server drain deadline');
      this.phase='draining';this.drainToken=token;this.drainUntil=this.now()+deadlineSeconds*1000;
      for(const job of this.jobs.values()){
        if(job.state==='done')continue;
        if(job.keep){job.state='ready';job.requestNonce++}
        else{job.state='dropped';job.reason='Dropped at Stop';job.wav=null}
      }
    }
    nextDrain(){
      if(this.phase!=='draining'||this.expire())return null;
      const job=this.order.map(id=>this.jobs.get(id)).find(x=>x.state==='ready'&&x.keep);
      if(!job)return null;
      job.state='sending';job.submittedCapture=this.drainToken;
      const nonce=++job.requestNonce;
      return {wav:new Uint8Array(job.wav),id:job.id,nonce,
        capture:this.drainToken,forceMixed:job.forceMixed,autoNamesAllowed:false};
    }
    finishDrain(id,nonce,response){
      if(this.phase!=='draining'||this.expire())return false;
      const job=this.jobs.get(id);
      if(!job||job.state!=='sending'||job.requestNonce!==nonce||job.submittedCapture!==this.drainToken)return false;
      job.state='done';job.result=response;job.wav=null;
      return true;
    }
    failDrain(id,nonce,reason='Drain failure'){
      if(this.phase!=='draining')return false;
      const job=this.jobs.get(id);
      if(!job||job.state!=='sending'||job.requestNonce!==nonce)return false;
      job.state='dropped';job.reason=reason.slice(0,100);job.wav=null;return true;
    }
    expire(){
      if(this.phase!=='draining'||this.now()<this.drainUntil)return false;
      this.close('Drain time limit exceeded');return true;
    }
    close(reason='Stop complete'){
      for(const job of this.jobs.values())if(job.state!=='done'){
        job.state='dropped';job.reason=reason;job.wav=null;
      }
      this.captureID='';this.drainToken='';this.phase='closed';this.drainUntil=null;
    }
    erase(){this.close('Erased');this.jobs.clear();this.order.length=0;}
    get bufferBytes(){return [...this.jobs.values()].reduce((n,j)=>n+(j.wav?.byteLength||0),0);}
  }
  return {StopWindowQueue,isPCM16MonoWav,digestHex};
});
