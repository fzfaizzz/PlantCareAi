/**
 * Focused regressions for touch capture transfer and variable-height Detect UI.
 * Requires the unchanged demo server on127.0.0.1:5173 and installed Chrome.
 * Runs an owned Vite process on5174 with an explicit Playwright HTTP fixture;
 * no real analysis service or diagnostic result is claimed by this test.
 * Run: node tests/reference-regressions.mjs
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const origin='http://127.0.0.1:5174';
const endpoint=`${origin}/api/analyze`;
const report={fixtureNotice:'Explicit controlled Playwright response only; no real analysis backend exists.',passes:[],failures:[],pageErrors:[]};
const sample=path.join(root,'public/assets/plants/sample-leaf-spotted.webp');
let server,browser,serverOutput='';
await mkdir(path.join(root,'qa'),{recursive:true});
const pass=(label,data)=>{report.passes.push({label,data});console.log(`PASS ${label}${data?' '+JSON.stringify(data):''}`);};
const twoFrames=page=>page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
const recordPageErrors=page=>page.on('pageerror',error=>report.pageErrors.push(error.message));
async function waitForServer(){
 const deadline=Date.now()+30_000;
 while(Date.now()<deadline){
  if(server.exitCode!==null)throw new Error(`Owned test server failed: ${serverOutput}`);
  try{if((await fetch(`${origin}/detect`)).ok)return;}catch{}
  await new Promise(done=>setTimeout(done,150));
 }
 throw new Error(`Owned test server did not become ready: ${serverOutput}`);
}
async function settledUploader(page){
 await page.waitForFunction(()=>{
  const page=document.querySelector('.detect-page'),uploader=document.querySelector('.image-uploader');
  return page&&uploader&&Math.abs(parseFloat(page.style.getPropertyValue('--uploader-height'))-uploader.getBoundingClientRect().height)<.5;
 });
 await twoFrames(page);
}
async function boxes(page){return page.evaluate(()=>{
 const rect=selector=>{const node=document.querySelector(selector);if(!node)return null;const r=node.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
 return{uploader:rect('.image-uploader'),result:rect('.analysis-result'),features:rect('.detect-features'),page:rect('.detect-page'),restart:rect('.start-over'),error:rect('.upload-error'),privacy:rect('.upload-privacy'),demo:rect('.demo-note')};
});}
function assertPageContains(data,label){
 assert.ok(data.features.y>=data.uploader.bottom+29.5,`${label}: feature gap ${data.features.y-data.uploader.bottom}px is below30px`);
 assert.ok(data.features.bottom<=data.page.bottom+.5,`${label}: features exceed page bottom`);
 if(data.restart)assert.ok(data.restart.bottom<=data.page.bottom+.5,`${label}: restart control exceeds page bottom`);
}

try{
 server=spawn(process.execPath,[path.join(root,'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5174','--strictPort'],{cwd:root,env:{...process.env,VITE_ANALYSIS_ENDPOINT:endpoint},windowsHide:true,stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',data=>{serverOutput+=data;});server.stderr.on('data',data=>{serverOutput+=data;});
 await waitForServer();console.log('Owned fixture server5174 is ready.');
 browser=await chromium.launch({channel:'chrome',headless:true,args:['--disable-blink-features=AutomationControlled']});

 const phoneContext=await browser.newContext({viewport:{width:390,height:1000},hasTouch:true,isMobile:true,reducedMotion:'no-preference'});
 const phone=await phoneContext.newPage();recordPageErrors(phone);
 await phone.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
 await phone.locator('.carousel-section').scrollIntoViewIfNeeded();
 const band=await phone.locator('.carousel-viewport').boundingBox();
 await phone.evaluate(()=>{
  window.__regressionTouchEvents=[];
  const viewport=document.querySelector('.carousel-viewport');
  for(const type of ['pointerdown','pointermove','lostpointercapture','pointerup','pointercancel'])viewport.addEventListener(type,event=>window.__regressionTouchEvents.push({type,target:event.target.className,x:event.clientX,y:event.clientY}),true);
 });
 const session=await phoneContext.newCDPSession(phone);
 const start={x:290,y:band.y+band.height/2};
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[start]});
 const baseline=Number(await phone.locator('.carousel-track').getAttribute('data-phase'));
 const scale=band.width/640;
 const touchMoves=[];
 try{
  for(let step=1;step<=8;step++){
   await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:start.x-step*15,y:start.y}]});
   await twoFrames(phone);
   const phase=Number(await phone.locator('.carousel-track').getAttribute('data-phase'));
   const native=((phase-baseline+840)%1680+1680)%1680-840;
   const actual=native*scale,expected=-step*15;
   touchMoves.push({step,expectedPhysicalPx:expected,actualPhysicalPx:actual,phase});
  }
  report.touch={baseline,scale,movesBeforeRelease:touchMoves,events:await phone.evaluate(()=>window.__regressionTouchEvents)};
  assert.equal(touchMoves.length,8);
  for(const move of touchMoves)assert.ok(Math.abs(move.actualPhysicalPx-move.expectedPhysicalPx)<=2,`Touch move${move.step} expected${move.expectedPhysicalPx}px; got${move.actualPhysicalPx}px`);
  assert.ok(report.touch.events.filter(event=>event.type==='pointermove').length>=8,'All real touch moves must reach the viewport');
  assert.equal(report.touch.events.some(event=>event.type==='pointercancel'),false,'The browser must not cancel a horizontal drag');
  pass('All8 real touch moves retain capture and match15px steps through120px before release',touchMoves);
 }finally{await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
 assert.equal(new URL(phone.url()).pathname,'/');
 await phoneContext.close();

 const desktop=await browser.newContext({viewport:{width:1314,height:1000},reducedMotion:'reduce'});
 const resultPage=await desktop.newPage();recordPageErrors(resultPage);
 const payload={plant:'Controlled browser fixture plant',condition:'Informational fixture response',confidence:.72,symptoms:['Fixture symptom one: visible markings are described here to verify that returned information fits in the result panel.','Fixture symptom two: this line is deliberately long enough to wrap across more than one line on smaller screens.','Fixture symptom three: no scientific interpretation is implied by this browser test fixture.'],care:['Fixture care one: this paragraph exercises ordinary returned guidance text and confirms the panel expands for the content.','Fixture care two: longer returned text should remain readable without covering any control, image or feature card.','Fixture care three: the entire recommendation must remain available when scrolling this page.'],prevention:['Fixture prevention one: this is a controlled UI check only and is not plant-health advice.','Fixture prevention two: this list verifies that server-provided content is displayed in document flow.','Fixture prevention three: read the informational note below without overlapping the following features.'],uncertainty:'Explicit test fixture only. No genuine analysis service exists. This controlled response checks the complete results layout.',inconclusive:true};
 await resultPage.route(endpoint,route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(payload)}));
 await resultPage.goto(`${origin}/detect`,{waitUntil:'networkidle'});
 await resultPage.locator('input[type=file]').setInputFiles(sample);
 await resultPage.locator('.image-preview img').waitFor({state:'visible'});
 await resultPage.getByRole('button',{name:'Analyze leaf',exact:true}).click();
 await resultPage.locator('.analysis-result').waitFor({state:'visible'});
 await settledUploader(resultPage);
 report.longResult=await boxes(resultPage);
 await resultPage.screenshot({path:path.join(root,'qa/scan-results-1314.png'),fullPage:true});
 assertPageContains(report.longResult,'Long1314px result');
 assert.ok(report.longResult.result.bottom<report.longResult.features.y,'Long result must end before the feature strip');
 pass('Desktop1314 long result expands page and keeps30px after full uploader',report.longResult);

 const invalid=await desktop.newPage();recordPageErrors(invalid);
 await invalid.goto('http://127.0.0.1:5173/detect',{waitUntil:'networkidle'});
 const badFile={name:'invalid-leaf.svg',mimeType:'image/svg+xml',buffer:Buffer.from('<svg></svg>')};
 report.invalidStates=[];
 for(const mode of ['empty','selected']){
  if(mode==='selected'){
   await invalid.locator('input[type=file]').setInputFiles(sample);
   await invalid.locator('.image-preview img').waitFor({state:'visible'});
  }
  await invalid.locator('input[type=file]').setInputFiles(badFile);
  await invalid.getByRole('alert').filter({hasText:'Choose a JPG, PNG or WebP image'}).waitFor();
  await settledUploader(invalid);
  const data=await boxes(invalid);report.invalidStates.push({mode,...data});
  assert.ok(data.privacy.y>=data.error.bottom-.5,`${mode}: privacy overlaps the error`);
  assert.ok(data.demo.y>=data.privacy.bottom-.5,`${mode}: demo note overlaps privacy`);
  assert.ok(data.demo.bottom<=data.uploader.bottom+.5,`${mode}: demo note exceeds measured uploader`);
  assertPageContains(data,`${mode} invalid file`);
  pass(`Invalid-file${mode} state keeps error/privacy/demo separate and features30px below uploader`,data);
 }
 assert.deepEqual(report.pageErrors,[]);
 pass('No browser page errors');
 report.passed=true;
}catch(error){report.passed=false;report.failures.push(error.stack||error.message);console.error(error);process.exitCode=1;}
finally{
 if(browser)await browser.close();
 if(server&&server.exitCode===null){server.kill();await Promise.race([new Promise(done=>server.once('exit',done)),new Promise(done=>setTimeout(done,5000))]);}
 report.testServerStopped=!server||server.exitCode!==null||server.signalCode!==null;
 await writeFile(path.join(root,'qa/scan-regression-results.json'),`${JSON.stringify(report,null,2)}\n`);
 console.log(`Regression report saved; owned5174 stopped:${report.testServerStopped}.`);
}
