/* AudioWorklet microphone tap for Conversation Lens. Uses LensPCM StreamingResampler.
 * No speaker output: a silent GainNode keeps processing alive without mic feedback.
 * Browsers require a localhost/HTTPS secure context and an AudioWorklet-capable engine.
 */
(function (root, factory) {
  const api = factory(root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.LensPCMCapture = api;
})(typeof globalThis !== 'undefined' ? globalThis : undefined, function (root) {
  'use strict';
  const PROCESSOR_SOURCE = `
  class LensPCMTap extends AudioWorkletProcessor {
    constructor(options){
      super();
      this.active=true;
      this.blockFrames=Math.max(512, Math.min(8192,options.processorOptions?.blockFrames||2048));
      this.chunk=new Float32Array(this.blockFrames);
      this.count=0;
      this.port.onmessage=event=>{
        if(event.data?.type==='freeze'){
          this.active=false;
          this.emit();
          this.port.postMessage({type:'frozen'});
        }
      };
    }
    emit(){
      if(this.count>0){
        const data=this.chunk.slice(0,this.count);
        this.port.postMessage({type:'pcm',frames:this.count,buffer:data.buffer},[data.buffer]);
        this.count=0;
      }
    }
    process(inputs){
      if(!this.active)return true;
      const channels=inputs[0];if(!channels?.length)return true;
      const frames=channels[0].length;
      for(let i=0;i<frames;i++){
        let sample=0;
        for(let c=0;c<channels.length;c++)sample+=channels[c][i];
        this.chunk[this.count++]=sample/channels.length;
        if(this.count>=this.blockFrames)this.emit();
      }
      return true;
    }
  }
  registerProcessor('lens-pcm-tap-v1',LensPCMTap);`;

  class MicCapture {
    constructor({ stream, onPCM, onError = () => {}, blockFrames = 2048,
                  contextFactory, resamplerClass, stopTracks = true } = {}) {
      if (!stream || typeof stream.getAudioTracks !== 'function')
        throw new TypeError('An active microphone MediaStream is required');
      if (typeof onPCM !== 'function') throw new TypeError('onPCM callback required');
      this.stream = stream;
      this.onPCM = onPCM;
      this.onError = onError;
      this.blockFrames = blockFrames;
      this.contextFactory = contextFactory || (() => new (root.AudioContext || root.webkitAudioContext)({latencyHint:'interactive'}));
      this.resamplerClass = resamplerClass || root.LensPCM?.StreamingResampler;
      if (!this.resamplerClass) throw new Error('Load lens_pcm_core.js first');
      this.stopTracks = stopTracks;
      this.state = 'idle';
      this.inputFrames = 0;
      this.outputFrames = 0;
      this._nodes = [];
      this._sourceUrl = null;
      this._closeOnce = null;
    }

    async start() {
      if (this.state !== 'idle') throw new Error('Capture already started');
      if (!root.AudioWorkletNode || !root.Blob || !root.URL?.createObjectURL)
        throw new Error('This browser does not support AudioWorklet PCM capture');
      this.state = 'starting';
      try {
        const context = this.context = this.contextFactory();
        if (!context.audioWorklet?.addModule) throw new Error('AudioWorklet is unavailable');
        const blob = new Blob([PROCESSOR_SOURCE],{type:'text/javascript'});
        this._sourceUrl = URL.createObjectURL(blob);
        try {await context.audioWorklet.addModule(this._sourceUrl)}
        finally {URL.revokeObjectURL(this._sourceUrl);this._sourceUrl=null}
        if (this.state !== 'starting') throw new Error('Capture cancelled');
        this.resampler = new this.resamplerClass(context.sampleRate);
        const source=context.createMediaStreamSource(this.stream);
        const node=new AudioWorkletNode(context,'lens-pcm-tap-v1',{processorOptions:{blockFrames:this.blockFrames}});
        const silent=context.createGain();silent.gain.value=0;
        source.connect(node);node.connect(silent);silent.connect(context.destination);
        this._nodes=[source,node,silent];this.node=node;
        node.port.onmessage = event => {
          if(event.data?.type==='pcm'){
            const float = new Float32Array(event.data.buffer);
            this.inputFrames += float.length;
            const pcm = this.resampler.push(float);
            this.outputFrames += pcm.length;
            if(this.state!=='closed' && pcm.length)try{this.onPCM(pcm)}catch(err){this.onError(err)}
          } else if (event.data?.type==='frozen') {
            this._resolveFreeze?.();this._resolveFreeze=null;
          }
        };
        node.onprocessorerror = () => this.onError(new Error('AudioWorklet PCM processor failed'));
        await context.resume();
        this.state = 'recording';
        return this;
      } catch(err){
        await this._cleanup();
        throw err;
      }
    }

    async stop() {
      if (this._closeOnce) return this._closeOnce;
      this._closeOnce = this._stopImpl();
      return this._closeOnce;
    }

    async _stopImpl() {
      if (this.state==='closed') return {inputFrames:this.inputFrames,outputFrames:this.outputFrames};
      this.state = 'stopping';
      // Stop mic immediately; the processor flushes buffered 0–2047 source samples.
      if(this.stopTracks)for(const track of this.stream.getTracks()){try{track.stop()}catch(e){}}
      if(this.node){
        await new Promise(resolve=>{
          let finished=false;
          const done=()=>{if(finished)return;finished=true;clearTimeout(timer);resolve()};
          const timer=setTimeout(done,1200);
          this._resolveFreeze=done;
          try{this.node.port.postMessage({type:'freeze'})}catch(e){done()}
        });
      }
      await this._cleanup();
      return {inputFrames:this.inputFrames,outputFrames:this.outputFrames};
    }

    async _cleanup() {
      this.state='closed';
      for (const node of this._nodes){try{node.disconnect()}catch(e){}}
      this._nodes.length=0;
      try{this.node?.port?.close()}catch(e){}
      if(this._sourceUrl){try{URL.revokeObjectURL(this._sourceUrl)}catch(e){}this._sourceUrl=null}
      if(this.context){try{await this.context.close()}catch(e){}}
      this.context=null;this.node=null;
    }
  }
  return { MicCapture };
});
