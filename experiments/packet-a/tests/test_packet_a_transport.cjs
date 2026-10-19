'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createHash, webcrypto} = require('node:crypto');
const {PCM16Ring, WindowTimeline} = require('../lens_pcm_core.js');
const {PacketATransport} = require('../lens_packet_a_transport.js');
const {digestHex} = require('../lens_stop_client.js');

const wav = (durationMs,add=0) => {
  const samples=new Int16Array(durationMs*16);
  for(let i=0;i<samples.length;i++)samples[i]=Math.round(17000*Math.sin((i+add)/40));
  const ring=new PCM16Ring({maxSeconds:10});ring.append(samples);
  const timeline=new WindowTimeline(ring);timeline.setCaptureID('unit-transport');
  const win=timeline.register(0,samples.length);return timeline.render(win.id).wav;
};
const samples=[wav(1200),wav(1400,12),wav(2000,30)];
function response(status,body){return new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}})}
function fakeServer({rejectIndex=-1,slow=false,freezeFail=false,busyFirst=false,closeFail=false}={}) {
  const log=[],leases={active:'',status:'idle',manifest:[],done:new Set()};
  let count=0;let resolveUpload,busyOnce=busyFirst;
  const fetchImpl=async (path,opts={})=>{
    log.push({path,opts});
    if(path==='/api/status')return response(200,{app:'lens-packet-a',protocol:1,token:'token-safe-for-test-123',engine:'audio-validation-only'});
    if(path==='/api/capture/open'){leases.active='lease-'+(++count)+'-long-enough';leases.status='live';return response(200,{capture:leases.active})}
    if(path==='/api/capture/freeze'){
      if(freezeFail)return response(409,{error:'Freeze rejected'});
      const data=JSON.parse(opts.body);
      if(data.capture!==leases.active||leases.status!=='live')return response(409,{error:'Wrong lease'});
      leases.status='frozen';return response(200,{frozen:true,deadlineSeconds:90});
    }
    if(path==='/api/capture/drain'){
      const data=JSON.parse(opts.body);
      if(data.capture!==leases.active||leases.status!=='frozen')return response(409,{error:'Not frozen'});
      leases.manifest=data.windows;leases.status='draining';leases.active='drain-'+(++count)+'-long-enough';
      return response(200,{capture:leases.active,deadlineSeconds:120});
    }
    if(path==='/api/capture/close'){if(closeFail)return response(503,{error:'Simulated close outage'});leases.status='idle';leases.active='';return response(200,{closed:true});}
    if(path==='/api/transcribe'){
      if(busyOnce){busyOnce=false;return response(429,{error:'Whisper worker busy',retryable:true});}
      if(slow){await new Promise(resolve=>{resolveUpload=resolve});}
      const bytes=Buffer.from(await opts.body.arrayBuffer());
      const digest=createHash('sha256').update(bytes).digest('hex');
      const id=opts.headers['X-Lens-Window-ID'];const descriptor=leases.manifest.find(x=>x.window_id===id);
      if(!descriptor||descriptor.sha256!==digest||opts.headers['X-Lens-Capture-Session']!==leases.active ||
         (opts.headers['X-Lens-Force-Mixed']==='true')!==descriptor.force_mixed||leases.done.has(id))
        return response(422,{error:'Unapproved or duplicated upload'});
      leases.done.add(id);const idx=leases.manifest.findIndex(x=>x.window_id===id);
      if(idx===rejectIndex)return response(503,{error:'Intentional model failure'});
      return response(200,{window_id:id,frames:(bytes.length-44)/2,engine:'audio-validation-only',text:null,discarded:false,forceMixed:descriptor.force_mixed});
    }
    return response(404,{error:'Wrong route'});
  };
  return {log,leases,fetchImpl,release:()=>resolveUpload?.()};
}

function createClient(server,events=[]){return new PacketATransport({
  fetchImpl:server.fetchImpl,
  digest:(bytes)=>digestHex(bytes,webcrypto),
  onWindow:ev=>events.push(ev),
})}

test('real keep/drop client sends only two selected exact WAVs under a fresh drain lease',async()=>{
  const backend=fakeServer();const events=[];const client=createClient(backend,events);
  await client.connect();await client.open();await client.freeze();
  const result=await client.submitSelection([
    {id:'w1',wav:samples[0],forceMixed:false},
    {id:'w3',wav:samples[2],forceMixed:true},
  ]);
  assert.deepEqual([result.kept,result.done,result.failed],[2,2,0]);
  assert.equal(client.phase,'ready');assert.equal(client.queue.bufferBytes,0);
  assert.deepEqual(events.map(x=>x.id),['w1','w3']);
  assert(events.every(x=>x.text===null&&x.ok===true));
  assert.deepEqual(backend.log.filter(x=>x.path==='/api/transcribe').map(x=>x.opts.headers['X-Lens-Window-ID']),['w1','w3']);
  assert.equal(backend.leases.manifest[1].force_mixed,true);
  assert.equal(backend.leases.manifest[1].sha256,createHash('sha256').update(samples[2]).digest('hex'));
  assert.equal(backend.leases.status,'idle');
});

test('drop all revokes frozen lease without any drain token or clip upload',async()=>{
  const backend=fakeServer();const client=createClient(backend);
  await client.connect();await client.open();await client.freeze();
  await client.close();
  assert.equal(backend.log.some(x=>x.path==='/api/capture/drain'),false);
  assert.equal(backend.log.some(x=>x.path==='/api/transcribe'),false);
  assert.equal(client.capture,'');assert.equal(client.phase,'ready');
});

test('failed freeze forbids drain, local client does not claim Stop was confirmed',async()=>{
  const backend=fakeServer({freezeFail:true});const client=createClient(backend);
  await client.connect();await client.open();await assert.rejects(client.freeze(),/Freeze rejected/);
  assert.equal(client.phase,'failed');
  await assert.rejects(client.submitSelection([{id:'w1',wav:samples[0]}]),/acknowledge freeze/);
  assert.equal(backend.leases.status,'idle');
});

test('bad selection is rejected before remote authorization; clip remains selectable after fix',async()=>{
  const backend=fakeServer();const client=createClient(backend);
  await client.connect();await client.open();await client.freeze();
  await assert.rejects(client.submitSelection([{id:'w1',wav:samples[0]},{id:'w1',wav:samples[0]}]),/repeated/);
  assert.equal(backend.log.some(x=>x.path==='/api/capture/drain'),false);
  await assert.rejects(client.submitSelection([{id:'bad',wav:new Uint8Array(400)}]),/Clip must/);
  const good=await client.submitSelection([{id:'w1',wav:samples[0]}]);
  assert.equal(good.done,1);
});

test('server rejects one clip without turning it into a successful transcript',async()=>{
  const backend=fakeServer({rejectIndex:1});const events=[];const client=createClient(backend,events);
  await client.connect();await client.open();await client.freeze();
  const result=await client.submitSelection([{id:'w1',wav:samples[0]}, {id:'w2',wav:samples[1]}]);
  assert.deepEqual([result.done,result.failed],[1,1]);
  assert.equal(events.at(-1).ok,false);assert.match(events.at(-1).reason,/Intentional model failure/);
  assert.equal(client.queue.bufferBytes,0);assert.equal(backend.leases.status,'idle');
});

test('cancel drain invalidates generation and prevents any late result from being surfaced',async()=>{
  const backend=fakeServer({slow:true});const events=[];const client=createClient(backend,events);
  await client.connect();await client.open();await client.freeze();
  const ongoing=client.submitSelection([{id:'w1',wav:samples[0]}]);
  for(let tries=0;tries<40 && !backend.log.some(x=>x.path==='/api/transcribe');tries++)await new Promise(r=>setTimeout(r,2));
  assert(backend.log.some(x=>x.path==='/api/transcribe'),'Upload never started');
  await client.close();backend.release();
  const result=await ongoing;
  assert.equal(events.length,0);
  assert.equal(client.phase,'ready');assert.equal(client.queue.bufferBytes,0);
  assert.equal(result.done,0);
});


test('busy speech worker returns retryable 429 without burning the selected one-use WAV',async()=>{
  const backend=fakeServer({busyFirst:true});const events=[];const client=createClient(backend,events);
  await client.connect();await client.open();await client.freeze();
  const result=await client.submitSelection([{id:'w1',wav:samples[0]}]);
  assert.equal(result.done,1);
  assert.equal(events.length,1);
  assert.equal(backend.log.filter(x=>x.path==='/api/transcribe').length,2);
  assert.equal(backend.leases.done.size,1);
  assert.equal(backend.leases.status,'idle');
});


test('server close failure is shown as unverified and token stays available for retry',async()=>{
  const backend=fakeServer({closeFail:true});const client=createClient(backend);
  await client.connect();await client.open();await client.freeze();
  const old=client.capture;
  const result=await client.submitSelection([{id:'w1',wav:samples[0]}]);
  assert.equal(result.done,1);
  assert.equal(result.leaseClosed,false);
  assert.equal(client.phase,'failed');
  assert.notEqual(client.capture,'');
  assert.equal(backend.leases.status,'draining');
  assert.equal(client.capture,backend.leases.active);
  const second=await client.close();
  assert.equal(second.closed,false);
  assert.equal(client.phase,'failed');
});
