import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const out=new URL('../qa/reference-v2/',import.meta.url);await mkdir(out,{recursive:true});
const definitions=[['home','/',1586,992,{badge:'.home-hero>.badge',heading:'.home-hero h1',cards:'.carousel-section',cta:'.home-action'}],['library','/library',1536,1024,{badge:'.library-hero>.badge',heading:'.library-hero h1',search:'.search-input',dropdown:'.select-wrap',filters:'.category-filters',grid:'.plant-grid',firstCard:'.library-card'}],['detect','/detect',1314,870,{badge:'.detect-hero>.badge',heading:'.detect-hero h1',panel:'.upload-panel',button:'.choose-image',features:'.detect-features'}],['about','/about',1536,1024,{badge:'.about-copy>.badge',heading:'.about-copy h1',primary:'.about-actions .button-primary',visual:'.about-visual',mission:'.purpose-section',technology:'.technology-section',firstTechnology:'.technology-card',dataset:'.architecture-content'}]];
const report={nativeFrames:[],responsive:[],pageErrors:[]};
const page=await browser.newPage();page.on('pageerror',error=>report.pageErrors.push(error.message));await page.emulateMedia({reducedMotion:'reduce'});
try{
 for(const [name,route,width,height,selectors] of definitions){
  await page.setViewportSize({width,height});const response=await page.goto('http://127.0.0.1:5173'+route);assert.equal(response.status(),200);await page.locator('h1').waitFor();await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(300);
  const boxes={};for(const [label,selector]of Object.entries(selectors)) boxes[label]=await page.locator(selector).first().boundingBox();
  const broken=await page.evaluate(()=>[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src));assert.deepEqual(broken,[]);
  report.nativeFrames.push({name,width,height,boxes});
  await page.screenshot({path:new URL(name+'.png',out).pathname.replace(/^\/([A-Z]:)/,'$1'),animations:'disabled',fullPage:true});
 }
 const box=(name,key)=>report.nativeFrames.find(frame=>frame.name===name).boxes[key];
 const near=(actual,expected,label)=>{for(const [key,value]of Object.entries(expected))assert.ok(Math.abs(actual[key]-value)<=2,`${label}.${key}: ${actual[key]} expected${value}`);};
 near(box('home','badge'),{x:664,y:115,width:258,height:43},'home badge');near(box('home','cta'),{x:656,y:831,width:275,height:85},'home CTA');
 near(box('library','search'),{x:209,y:244,width:887,height:48},'library search');near(box('library','grid'),{x:45,y:377,width:1446},'library grid');
 near(box('detect','panel'),{x:394,y:362,width:536,height:306},'detect upload');near(box('about','badge'),{x:254,y:89,width:171,height:35},'about badge');near(box('about','primary'),{x:254,y:390,width:222,height:48},'about button');near(box('about','mission'),{y:517,height:179},'about mission');near(box('about','firstTechnology'),{x:425,y:712,width:136,height:103},'about technology');near(box('about','dataset'),{x:612,y:827,width:924},'about dataset');
 for(const width of [1440,1024,821,820,768,390,320])for(const [name,route]of definitions){await page.setViewportSize({width,height:width<821?844:1080});await page.goto('http://127.0.0.1:5173'+route);await page.locator('h1').waitFor();const extent=await page.evaluate(()=>document.documentElement.scrollWidth);assert.ok(extent<=width+1,`${name} overflow at ${width}: ${extent}`);report.responsive.push({name,width,overflow:false});if(width===390||width===1440)await page.screenshot({path:new URL(name+'-'+width+'.png',out).pathname.replace(/^\/([A-Z]:)/,'$1'),animations:'disabled',fullPage:true});}
 assert.deepEqual(report.pageErrors,[]);report.passed=true;await writeFile(new URL('measurements.json',out),JSON.stringify(report,null,2));console.log('PASS: 10 native reference coordinate groups; 28 responsive route checks; zero page errors.');
}finally{await browser.close();}
