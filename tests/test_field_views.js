const test=require('node:test'), assert=require('node:assert/strict');
const {index,clock,spectra}=require('../assets/field-evidence.js');
test('recording counts deduplicate observations, and objects follow their own recording',()=>{
 const section={nodes:[{id:'r',type:'recording',recordingId:'session',startedEpoch:0},{id:'b',url:'https://archive.org/details/test'}],edges:[{relation:'located_in',source:'a',target:'county'},{relation:'reviewed_frame_in',source:'obj',target:'r'}],observations:['a','b'].map(id=>({id,recordingIds:['r'],evidence:[{recordingId:'session',nodeId:'b',verifiedEpoch:1,assets:[]}]}))};
 const result=index(section);assert.equal(result.recordings.length,1);assert.equal(result.recordings[0].observations.size,2);assert.equal(result.recordings[0].objects.size,1);assert.equal(result.recordings[0].bundles.size,1);
 assert.equal(clock(result.recordings)[0].minuteOfDial,0);assert.equal(clock(result.recordings,'pm').length,0);assert.equal(clock([{startedEpoch:null}]).length,0);
});
test('RF snapshots deduplicate minutes and preserve missing bins',()=>{
 const row={captured_at:'2026-11-09T00:00:00Z',spectrum:{range_hz:[1590000000,1610000000],average_db:[-50,null,-40],maximum_db:[-40,null,-30]}};
 const s=spectra([row,row].map(JSON.stringify).join('\n'));assert.equal(s.length,1);assert.deepEqual(s[0].average,[-50,null,-40]);assert.deepEqual(spectra(JSON.stringify({spectrum:{range_hz:[2,1],average_db:[0,0]}})),[]);
});
