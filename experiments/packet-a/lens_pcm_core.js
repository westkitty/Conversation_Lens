/* Conversation Lens — bounded, sample-indexed PCM edit core. No DOM or network dependencies.
 * Browser: global LensPCM. Node: require('./lens_pcm_core.js').
 * Segment boundaries are half-open [start, end) and are exact 16 kHz frame indices.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.LensPCM = api;
})(typeof globalThis !== 'undefined' ? globalThis : undefined, function () {
  'use strict';
  const INT16_MAX = 32767;
  const SUPPORTED_SAMPLE_RATE = 16000;
  const MAX_RENDER_MS = 10000;
  const isSafeInt = value => Number.isSafeInteger(value) && value >= 0;
  const assert = (ok, message) => { if (!ok) throw new RangeError(message); };
  const secondsToFrames = (rate, seconds) => Math.round(rate * seconds);
  const clampInt16 = x => Math.max(-32768, Math.min(INT16_MAX, Math.round(x * (x < 0 ? 32768 : 32767))));

  class StreamingResampler {
    constructor(inputRate, outputRate = SUPPORTED_SAMPLE_RATE) {
      assert(Number.isFinite(inputRate) && inputRate >= outputRate && inputRate <= 192000,
        'Input sample rate must be between output rate and 192 kHz');
      assert(outputRate === SUPPORTED_SAMPLE_RATE, 'Conversation Lens WAV input is 16 kHz');
      this.inputRate = inputRate;
      this.outputRate = outputRate;
      this.interval = inputRate / outputRate;
      this.nextOutputAt = 0;
      this.inputFrames = 0;
      this.prev = 0;
      // Streaming two-stage low pass for downsampling. Continuous across chunk boundaries.
      this.filterCoefficient = inputRate === outputRate ? 1 :
        Math.min(1, 1 - Math.exp(-2 * Math.PI * (outputRate * 0.32) / inputRate));
      this.low1 = 0;
      this.low2 = 0;
    }
    push(samples) {
      assert(samples instanceof Float32Array, 'Expected Float32Array mic samples');
      assert(samples.length <= 32768, 'Oversized incoming capture block');
      const output = new Int16Array(Math.ceil(samples.length / this.interval) + 3);
      let out = 0;
      for (let i = 0; i < samples.length; i++) {
        const v = Number.isFinite(samples[i]) ? Math.max(-1, Math.min(1, samples[i])) : 0;
        this.low1 += this.filterCoefficient * (v - this.low1);
        this.low2 += this.filterCoefficient * (this.low1 - this.low2);
        const current = this.low2;
        const frame = this.inputFrames++;
        if (!frame) this.prev = current;
        while (this.nextOutputAt <= frame + 1e-9) {
          const t = frame ? Math.max(0, Math.min(1, this.nextOutputAt - (frame - 1))) : 1;
          output[out++] = clampInt16(this.prev * (1 - t) + current * t);
          this.nextOutputAt += this.interval;
        }
        this.prev = current;
      }
      return output.subarray(0, out);
    }
  }

  class PCM16Ring {
    constructor({ sampleRate = SUPPORTED_SAMPLE_RATE, maxSeconds = 45 } = {}) {
      assert(sampleRate === SUPPORTED_SAMPLE_RATE, 'Ring requires 16 kHz PCM');
      assert(Number.isFinite(maxSeconds) && maxSeconds >= 10 && maxSeconds <= 120,
        'Ring duration must be 10–120 s');
      this.sampleRate = sampleRate;
      this.capacity = secondsToFrames(sampleRate, maxSeconds);
      this.data = new Int16Array(this.capacity);
      this.end = 0;
      this.length = 0;
    }
    get start() { return this.end - this.length; }
    get bytes() { return this.data.byteLength; }
    contains(start, end) {
      return isSafeInt(start) && isSafeInt(end) && start <= end &&
        start >= this.start && end <= this.end;
    }
    append(samples) {
      assert(samples instanceof Int16Array, 'Expected Int16Array resampled speech');
      assert(this.end + samples.length <= Number.MAX_SAFE_INTEGER, 'PCM frame position overflow');
      const oldEnd = this.end;
      const skip = Math.max(0, samples.length - this.capacity);
      for (let i = skip; i < samples.length; i++) {
        this.data[(oldEnd + i) % this.capacity] = samples[i];
      }
      this.end += samples.length;
      this.length = Math.min(this.capacity, this.length + samples.length);
      return { start: oldEnd, end: this.end, evictedBefore: this.start };
    }
    slice(start, end) {
      assert(this.contains(start, end), 'Audio was evicted or frame bounds are invalid');
      const output = new Int16Array(end - start);
      for (let i = 0; i < output.length; i++) output[i] = this.data[(start + i) % this.capacity];
      return output;
    }
    erase() { this.data.fill(0); this.end = 0; this.length = 0; }
  }

  function wavBytes(pcm, sampleRate = SUPPORTED_SAMPLE_RATE) {
    assert(pcm instanceof Int16Array, 'WAV requires PCM16');
    assert(sampleRate === SUPPORTED_SAMPLE_RATE, 'WAV output must be mono 16 kHz');
    assert(pcm.length > 0 && pcm.length <= secondsToFrames(sampleRate, MAX_RENDER_MS / 1000),
      'WAV must contain 1 frame to at most 10 s');
    const bytes = new Uint8Array(44 + pcm.length * 2);
    const data = new DataView(bytes.buffer);
    for (const [offset, token] of [[0, 'RIFF'], [8, 'WAVE'], [12, 'fmt '], [36, 'data']]) {
      for (let j = 0; j < token.length; j++) bytes[offset + j] = token.charCodeAt(j);
    }
    data.setUint32(4, 36 + pcm.length * 2, true);
    data.setUint32(16, 16, true);
    data.setUint16(20, 1, true);
    data.setUint16(22, 1, true);
    data.setUint32(24, sampleRate, true);
    data.setUint32(28, sampleRate * 2, true);
    data.setUint16(32, 2, true);
    data.setUint16(34, 16, true);
    data.setUint32(40, pcm.length * 2, true);
    for (let i = 0; i < pcm.length; i++) data.setInt16(44 + i * 2, pcm[i], true);
    return bytes;
  }

  class WindowTimeline {
    constructor(ring, { minEditMs = 250, maxRenderMs = MAX_RENDER_MS } = {}) {
      assert(ring instanceof PCM16Ring, 'Timeline must share PCM ring');
      assert(Number.isFinite(minEditMs) && minEditMs >= 100 && minEditMs <= 1000,
        'Minimum edit span outside 100–1000 ms');
      assert(Number.isFinite(maxRenderMs) && maxRenderMs >= 2000 && maxRenderMs <= MAX_RENDER_MS,
        'Server WAV cap outside 2–10 seconds');
      this.ring = ring;
      this.minFrames = secondsToFrames(ring.sampleRate, minEditMs / 1000);
      this.maxFrames = secondsToFrames(ring.sampleRate, maxRenderMs / 1000);
      this.segments = [];
      this.nextID = 0;
      this.captureID = '';
    }
    setCaptureID(captureID) {
      assert(typeof captureID === 'string' && captureID.length > 0, 'Capture ID required');
      this.captureID = captureID;
    }
    register(start, end, { reason = 'silence', possibleOverlap = false, speaker = null } = {}) {
      assert(this.captureID.length > 0, 'Capture ID not selected');
      assert(this.ring.contains(start, end), 'New clip not present in PCM buffer');
      assert(end - start >= this.minFrames && end - start <= this.maxFrames,
        'Clip outside allowed duration');
      assert(this.segments.length === 0 || this.segments[this.segments.length - 1].end <= start,
        'A recording window must not overlap a prior window');
      const item = { id: 'w' + (++this.nextID), start, end, captureID: this.captureID,
        reason, possibleOverlap: !!possibleOverlap, speaker, edited: false,
        learningBlocked: !!possibleOverlap, status: 'buffered' };
      this.segments.push(item);
      return { ...item };
    }
    get(id) {
      const s = this.segments.find(item => item.id === id);
      assert(!!s, 'Unknown window ID');
      return s;
    }
    editable(s) {
      assert(this.ring.contains(s.start, s.end), 'Audio was evicted; edits no longer possible');
      assert(s.status === 'buffered', 'Cannot edit a submitted, processing or discarded clip');
    }
    split(id, at) {
      const s = this.get(id); this.editable(s);
      assert(isSafeInt(at) && at - s.start >= this.minFrames && s.end - at >= this.minFrames,
        'Split requires usable audio on both sides');
      const index = this.segments.indexOf(s), beforeEnd = s.end;
      s.end = at;
      s.edited = true;
      s.learningBlocked = true;
      s.reason = 'manual split';
      const right = { ...s, id: 'w' + (++this.nextID), start: at, end: beforeEnd,
        reason: 'manual split' };
      this.segments.splice(index + 1, 0, right);
      return [ { ...s }, { ...right } ];
    }
    merge(leftID, rightID) {
      const l = this.get(leftID), r = this.get(rightID);
      this.editable(l); this.editable(r);
      assert(this.segments.indexOf(r) === this.segments.indexOf(l) + 1,
        'Only ordered adjacent windows can be merged');
      assert(l.end === r.start && l.captureID === r.captureID,
        'Merge requires exactly contiguous samples from one capture');
      assert(r.end - l.start <= this.maxFrames, 'Merged clip exceeds WAV/backend cap');
      const twoSpeakers = !!(l.speaker && r.speaker && l.speaker !== r.speaker);
      l.end = r.end;
      l.possibleOverlap ||= r.possibleOverlap || twoSpeakers;
      l.learningBlocked = true;
      l.edited = true;
      l.speaker = twoSpeakers ? 'Mixed' : l.speaker || r.speaker;
      l.reason = 'manual merge';
      this.segments.splice(this.segments.indexOf(r), 1);
      return { ...l };
    }
    moveBoundary(leftID, rightID, at) {
      const l = this.get(leftID), r = this.get(rightID);
      this.editable(l); this.editable(r);
      assert(this.segments.indexOf(r) === this.segments.indexOf(l) + 1 && l.end === r.start,
        'Boundary must belong to adjacent contiguous segments');
      assert(isSafeInt(at) && at - l.start >= this.minFrames && r.end - at >= this.minFrames,
        'New boundary would create a segment shorter than minimum');
      assert(at - l.start <= this.maxFrames && r.end - at <= this.maxFrames,
        'New segment longer than backend cap');
      l.end = at; r.start = at;
      for (const s of [l,r]) { s.edited = true; s.learningBlocked = true; s.reason = 'manual boundary'; }
      return [{ ...l }, { ...r }];
    }
    setStatus(id, status) {
      assert(['buffered','processing','done','dropped'].includes(status), 'Invalid window status');
      const s = this.get(id);
      assert(s.status !== 'dropped' && s.status !== 'done', 'A terminal window cannot be reopened');
      if (status === 'processing') assert(s.status === 'buffered', 'Window already submitted');
      if (status === 'buffered') assert(s.status === 'buffered', 'Cannot unsubmit window');
      s.status = status;
      return { ...s };
    }
    render(id, { preRollMs = 0, postRollMs = 0, forDrain = false } = {}) {
      const s = this.get(id);
      if (forDrain) {
        assert(s.status === 'processing' || s.status === 'buffered',
          'Only live or queued windows can be resubmitted after STOP');
        assert(this.ring.contains(s.start, s.end), 'Audio was evicted; cannot finish after STOP');
      } else this.editable(s);
      for (const v of [preRollMs,postRollMs])
        assert(Number.isFinite(v) && v >= 0 && v <= 500, 'Context roll must be 0–500 ms');
      const pre = secondsToFrames(this.ring.sampleRate, preRollMs / 1000);
      const post = secondsToFrames(this.ring.sampleRate, postRollMs / 1000);
      const start = Math.max(this.ring.start, s.start - pre);
      const end = Math.min(this.ring.end, s.end + post);
      assert(end - start <= this.maxFrames, 'Rendered WAV plus context exceeds 10-second limit');
      const pcm = this.ring.slice(start, end);
      return { id: s.id, captureID: s.captureID, start, end, primaryStart: s.start,
        primaryEnd: s.end, pcm, wav: wavBytes(pcm, this.ring.sampleRate),
        edited: s.edited, possibleOverlap: s.possibleOverlap,
        // Context from a different window must not be used to train a voice identity.
        forceMixed: s.learningBlocked || start !== s.start || end !== s.end || s.speaker === 'Mixed',
        sampleRate: this.ring.sampleRate };
    }
    renderForDrain(id, options = {}) {
      return this.render(id, { ...options, forDrain: true });
    }
    stoppable() {
      return this.segments.filter(s => ['buffered','processing'].includes(s.status) &&
        this.ring.contains(s.start,s.end)).map(s => ({ ...s }));
    }
    buffered() { return this.segments.filter(s => s.status === 'buffered' && this.ring.contains(s.start,s.end)).map(s => ({ ...s })); }
    pruneEvicted() {
      for (const s of this.segments) if (s.status === 'buffered' && !this.ring.contains(s.start,s.end)) s.status = 'dropped';
    }
  }

  return { StreamingResampler, PCM16Ring, WindowTimeline, wavBytes,
    SAMPLE_RATE: SUPPORTED_SAMPLE_RATE };
});
