'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
const {PCM16Ring,WindowTimeline}=require('../lens_pcm_core');
const {StopWindowQueue,digestHex,isPCM16MonoWav}=require('../lens_stop_client');
function createQueue(now=()=>1000){const q=new StopWindowQueue({now});q.bindCapture('live-lease-0123456789');return q;}
function wavFrames(ms){const ring=new PCM16Ring({maxSeconds:10});const samples=new Int16Array(ms*16);for(let i=0;i<samples.length;i++)samples[i]=(i*11)%8192;ring.append(samples);const t=new WindowTimeline(ring);t.setCaptureID('live-lease-0123456789');const clip=t.register(0,samples.length);return t.render(clip.id).wav;}
const small=wavFrames(1000),medium=wavFrames(2400);
test('PCM WAV format guards and digest exact bytes',async()=>{
 assert.equal(isPCM16MonoWav(small),true);
 assert.equal(small.length,32044);
 assert.equal(isPCM16MonoWav(new Uint8Array(32044)),false);
 const digest=await digestHex(small,webcrypto);
 assert.match(digest,/^[0-9a-f]{64}$/);
 assert.notEqual(digest,await digestHex(medium,webcrypto));
});
test('stop freeze cuts off stale live response then only explicit keep survives',async()=>{
 const q=createQueue();q.add({id:'w1',wav:small});q.add({id:'w2',wav:medium,forceMixed:true});
 const inFlight=q.startLive('w1');
 const freeze=q.beginStop();
 assert.equal(freeze.windows.length,2);assert.equal(q.phase,'freezing');
 assert.equal(q.finishLive('w1',inFlight.nonce,{text:'should never appear'}),false);
 assert.throws(()=>q.choose('w2',true),/after freeze/);
 q.confirmFrozen();q.choose('w1',false);q.choose('w2',true);
 const manifest=await q.manifest();assert.equal(manifest.length,1);
 assert.equal(manifest[0].window_id,'w2');assert.equal(manifest[0].force_mixed,true);
 assert.equal(manifest[0].sha256,await digestHex(medium));
 q.authorizeDrain('drain-lease-987654321',120);
 assert.equal(q.bufferBytes,medium.length);
 const send=q.nextDrain();assert.equal(send.id,'w2');assert.equal(send.autoNamesAllowed,false);
 assert.equal(q.finishDrain('w2',send.nonce,{text:'kept'}),true);
 assert.equal(q.finishDrain('w2',send.nonce,{text:'duplicate'}),false);
 assert.equal(q.nextDrain(),null);q.close();assert.equal(q.bufferBytes,0);
 assert.equal(q.list()[0].state,'dropped');assert.equal(q.list()[1].state,'done');
});
test('do not accept late callbacks from previous drain nonce',async()=>{
 const q=createQueue();q.add({id:'w9',wav:medium});q.beginStop();q.confirmFrozen();q.authorizeDrain('drain-lease-987654321');
 const send=q.nextDrain();assert.equal(q.finishDrain('w9',send.nonce-1,{}),false);
 q.close();assert.equal(q.finishDrain('w9',send.nonce,{}),false);
 assert.equal(q.get('w9').state,'dropped');
});
test('memory cap, no duplicate upload, cannot add new window after stopping',()=>{
 const q=createQueue();for(let i=0;i<4;i++)q.add({id:'w'+i,wav:small});
 assert.throws(()=>q.add({id:'w4',wav:small}),/Pending clip cap/);
 assert.throws(()=>q.add({id:'w1',wav:small}),/Duplicate/);
 q.beginStop();assert.throws(()=>q.add({id:'w5',wav:small}),/not in intake/);
 q.close();assert.equal(q.bufferBytes,0);
});
test('reject editing a transient sending clip or invalid drain choice',async()=>{
 const q=createQueue();q.add({id:'w1',wav:small});
 q.beginStop();q.confirmFrozen();
 assert.throws(()=>q.choose('absent',true),/Unknown/);
 assert.throws(()=>q.choose('w1','yes'),/explicit/);
 assert.equal((await q.manifest()).length,1);
 assert.throws(()=>q.authorizeDrain('long-drain-token-00001',121),/deadline/);
});
test('drain expiry discards remaining audio and prevents later commit',()=>{
 let now=1000;const q=createQueue(()=>now);
 q.add({id:'w1',wav:small});q.beginStop();q.confirmFrozen();q.authorizeDrain('new-drain-00123456789',3);
 const inFlight=q.nextDrain();now=4001;
 assert.equal(q.finishDrain('w1',inFlight.nonce,{text:'late'}),false);
 assert.equal(q.phase,'closed');assert.equal(q.bufferBytes,0);
});
test('rejected drain consumes clip once, no silent retry',()=>{
 const q=createQueue();q.add({id:'w1',wav:small});q.beginStop();q.confirmFrozen();q.authorizeDrain('new-drain-00123456789');
 const inFlight=q.nextDrain();assert.equal(q.failDrain('w1',inFlight.nonce,'Whisper timeout'),true);
 assert.equal(q.nextDrain(),null);assert.equal(q.list()[0].reason,'Whisper timeout');
});
