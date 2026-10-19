'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { StreamingResampler, PCM16Ring, WindowTimeline, wavBytes, SAMPLE_RATE } = require('../lens_pcm_core');

function sine(length, rate) {
  return Float32Array.from({length},(_,i)=>Math.sin(2*Math.PI*410*i/rate)*0.45);
}
function pcm(length,offset=0) {return Int16Array.from({length},(_,i)=>((i+offset)*47%60001)-30000)}
function hash(ints){return createHash('sha256').update(Buffer.from(ints.buffer,ints.byteOffset,ints.byteLength)).digest('hex')}

for(const srcRate of [16000,44100,48000,96000]){
 test('streaming resampler invariant to chunk boundaries '+srcRate,()=>{
   const input=sine(srcRate*4+123,srcRate);
   const a=new StreamingResampler(srcRate),b=new StreamingResampler(srcRate);
   const directPieces=[];
   for(let i=0;i<input.length;i+=32768)directPieces.push(a.push(input.subarray(i,i+32768)));
   const direct=new Int16Array(directPieces.reduce((n,part)=>n+part.length,0));
   let directOffset=0;for(const part of directPieces){direct.set(part,directOffset);directOffset+=part.length}
   const portions=[];let offset=0;
   for(const step of [3,1023,55,10001,4,735,4095,810,9999,14999,444,9999999]){
     if(offset>=input.length)break;
     const end=Math.min(input.length,offset+step);let next=offset;
     while(next<end){const n=Math.min(end-next,32768);portions.push(b.push(input.subarray(next,next+n)));next+=n}
     offset=end;
   }
   if(offset<input.length){while(offset<input.length){const n=Math.min(32768,input.length-offset);portions.push(b.push(input.subarray(offset,offset+n)));offset+=n}}
   const joined=new Int16Array(portions.reduce((n,a)=>n+a.length,0));let off=0;
   for(const a of portions){joined.set(a,off);off+=a.length}
   assert.deepEqual(joined,direct);
   assert.equal(direct.length,Math.floor((input.length-1)*16000/srcRate)+1);
   assert.ok(direct.some(x=>x>1000),'should retain a non-zero speech signal');
 });
}

test('ring preserves exact PCM samples through wraparound and refuses evicted source',()=>{
 const r=new PCM16Ring({maxSeconds:10});
 assert.equal(r.bytes,320000);
 r.append(pcm(96000));
 r.append(pcm(95000,96000));
 assert.equal(r.end,191000);
 assert.equal(r.start,31000);
 assert.deepEqual(r.slice(158000,159000),pcm(1000,158000));
 assert.throws(()=>r.slice(30000,32000),/evicted/);
 assert.throws(()=>r.slice(0,191001),/evicted/);
 assert.throws(()=>r.append(new Float32Array([.5])),/Int16Array/);
 r.erase();
 assert.equal(r.length,0);
 assert.equal(r.end,0);
 assert.ok(r.data.every(x=>x===0));
});

test('ring can ingest more than entire capacity without breaking absolute frame mapping',()=>{
 const ring=new PCM16Ring({maxSeconds:10});
 ring.append(pcm(230000));
 assert.equal(ring.start,70000);
 assert.equal(ring.end,230000);
 assert.deepEqual(ring.slice(210000,211000),pcm(1000,210000));
});

test('WAV encoder writes canonical RIFF, PCM16 mono 16k and payload byte-exactly',()=>{
 const samples=new Int16Array([32767,-32768,0,100,-100]);
 const b=wavBytes(samples),v=new DataView(b.buffer);
 assert.equal(Buffer.from(b.subarray(0,4)).toString(),'RIFF');
 assert.equal(Buffer.from(b.subarray(8,12)).toString(),'WAVE');
 assert.equal(v.getUint32(4,true),36+samples.byteLength);
 assert.equal(v.getUint16(20,true),1);assert.equal(v.getUint16(22,true),1);
 assert.equal(v.getUint32(24,true),16000);assert.equal(v.getUint16(34,true),16);
 assert.equal(v.getUint32(40,true),samples.byteLength);
 assert.deepEqual(Int16Array.from(samples.map((_,i)=>v.getInt16(44+2*i,true))),samples);
 assert.throws(()=>wavBytes(new Int16Array(160001)),/at most 10 s/);
});

test('split, boundary drag and merge conserve exactly every frame; never duplicate or drop',()=>{
 const ring=new PCM16Ring({maxSeconds:20});
 const original=pcm(144000);ring.append(original);
 const timeline=new WindowTimeline(ring);timeline.setCaptureID('session1');
 const clip=timeline.register(0,144000,{reason:'hard cap',speaker:'Dale'});
 const [left,right]=timeline.split(clip.id,48000);
 assert.equal(left.end,right.start);
 assert.equal(left.start,0);
 assert.equal(right.end,144000);
 const startHash=hash(original);
 const moved=timeline.moveBoundary(left.id,right.id,60000);
 assert.equal(moved[0].end,60000);
 assert.equal(moved[1].start,60000);
 const a=timeline.render(left.id),b=timeline.render(right.id);
 const combined=new Int16Array(a.pcm.length+b.pcm.length);
 combined.set(a.pcm);combined.set(b.pcm,a.pcm.length);
 assert.equal(hash(combined),startHash);
 assert.equal(combined.length,original.length);
 assert.ok(a.forceMixed&&b.forceMixed,'any edited window must block voice training');
 const merged=timeline.merge(left.id,right.id);
 assert.equal(merged.end,144000);
 assert.equal(timeline.segments.length,1);
 assert.equal(hash(timeline.render(merged.id).pcm),startHash);
 assert.throws(()=>timeline.split(merged.id,144000-100),/both sides/);
});

test('merge at exactly 10 seconds is valid, but anything larger is refused',()=>{
 const ring=new PCM16Ring({maxSeconds:20});ring.append(pcm(176000));
 const t=new WindowTimeline(ring);t.setCaptureID('capture-one');
 const a=t.register(0,96000),b=t.register(96000,176000);
 assert.throws(()=>t.merge(a.id,b.id),/exceeds/);
 const bounded=new WindowTimeline(ring);bounded.setCaptureID('capture-one');
 const c=bounded.register(0,80000),d=bounded.register(80000,160000);
 assert.equal(bounded.merge(c.id,d.id).end,160000);
});

test('merge contiguous shorter spans preserves mixed identity and stops name learning',()=>{
 const ring=new PCM16Ring({maxSeconds:10});ring.append(pcm(128000));
 const t=new WindowTimeline(ring);t.setCaptureID('same-capture');
 const a=t.register(0,64000,{speaker:'Dale'}),b=t.register(64000,128000,{speaker:'Morgan'});
 const merged=t.merge(a.id,b.id);
 assert.equal(merged.speaker,'Mixed');assert.equal(merged.possibleOverlap,true);
 assert.equal(t.render(merged.id).forceMixed,true);
});

test('pre-roll and post-roll yield real samples without mutating primary boundaries; reject excess',()=>{
 const r=new PCM16Ring({maxSeconds:10});r.append(pcm(128000));
 const t=new WindowTimeline(r);t.setCaptureID('s');
 const first=t.register(0,64000),last=t.register(64000,128000);
 const pad=t.render(last.id,{preRollMs:200,postRollMs:0});
 assert.equal(pad.start,60800);
 assert.equal(pad.primaryStart,64000);
 assert.equal(pad.end,128000);
 assert.equal(pad.pcm.length,67200);
 assert.equal(pad.forceMixed,true,'overlapping context cannot be used to learn names');
 assert.deepEqual(pad.pcm,r.slice(pad.start,pad.end));
 assert.deepEqual(t.render(first.id).pcm,r.slice(0,64000));
 assert.throws(()=>t.render(last.id,{preRollMs:1000}),/Context roll/);
 t.setStatus(last.id,'processing');
 assert.throws(()=>t.render(last.id),/Cannot edit/);
 assert.throws(()=>t.split(last.id,96000),/Cannot edit/);
});

test('STOP can resubmit a frozen inflight clip from the ring without making it editable',()=>{
 const ring=new PCM16Ring({maxSeconds:10}),source=pcm(96000);
 ring.append(source);
 const timeline=new WindowTimeline(ring);timeline.setCaptureID('old-lease');
 const segment=timeline.register(0,96000);
 timeline.setStatus(segment.id,'processing');
 assert.equal(timeline.stoppable().length,1);
 assert.equal(timeline.buffered().length,0);
 assert.deepEqual(timeline.renderForDrain(segment.id).pcm,source);
 assert.throws(()=>timeline.render(segment.id),/Cannot edit/);
 assert.throws(()=>timeline.moveBoundary(segment.id,segment.id,48000),/Cannot edit/);
 timeline.setStatus(segment.id,'done');
 assert.equal(timeline.stoppable().length,0);
 assert.throws(()=>timeline.renderForDrain(segment.id),/Only live or queued/);
});

test('bounded ring evictions make old clips unavailable and visible as dropped',()=>{
 const ring=new PCM16Ring({maxSeconds:10});ring.append(pcm(40000));
 const t=new WindowTimeline(ring);t.setCaptureID('same-capture');
 const a=t.register(0,40000);
 ring.append(pcm(159000,40000));
 t.pruneEvicted();
 assert.equal(t.get(a.id).status,'dropped');
 assert.equal(t.buffered().length,0);
});

test('reject invalid state transitions and noncontiguous capture edits',()=>{
 const ring=new PCM16Ring({maxSeconds:10});ring.append(pcm(112000));
 const t=new WindowTimeline(ring);t.setCaptureID('one');
 const a=t.register(0,32000),b=t.register(40000,80000),c=t.register(80000,112000);
 assert.throws(()=>t.merge(a.id,b.id),/contiguous/);
 assert.throws(()=>t.moveBoundary(a.id,b.id,36000),/contiguous/);
 assert.throws(()=>t.merge(a.id,c.id),/adjacent/);
 t.setStatus(c.id,'dropped');
 assert.throws(()=>t.setStatus(c.id,'buffered'),/terminal/);
 assert.throws(()=>t.register(60000,100000),/overlap/);
});
