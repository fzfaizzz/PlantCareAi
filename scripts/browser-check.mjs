import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const output = new URL('../qa/',import.meta.url);
await mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
const report={responsive:[],interactions:[],errors};
const origin='http://127.0.0.1:5173';
try {
 for(const width of (process.argv.includes('--interactions-only') ? [] : [1440,1024,768,390,320])) {
  await page.setViewportSize({width,height:width<700?844:1000});
  for(const route of ['/','/library','/detect','/about','/how-it-works']) {
   const response=await page.goto(origin+route); assert.equal(response.status(),200);
   await page.locator('h1').waitFor();await page.evaluate(()=>document.fonts.ready);
   await page.waitForTimeout(700);
   const metrics=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth,missing:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src)}));
   assert.ok(metrics.scroll<=width+1,`${route} overflows at ${width}: ${metrics.scroll}`);assert.deepEqual(metrics.missing,[]);
   report.responsive.push({width,route,overflow:false,brokenImages:0});
   await page.screenshot({path:new URL(`${route==='/'?'home':route.slice(1)}-${width}.png`,output).pathname.replace(/^\/([A-Z]:)/,'$1'),fullPage:true,animations:'disabled'});
  }
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(origin+'/library');
 const cards=page.locator('.library-card');await cards.first().waitFor();assert.equal(await cards.count(),10);
 await page.getByRole('searchbox').fill('blight');assert.equal(await cards.count(),3);
 await page.getByRole('button',{name:'Clear search'}).click();assert.equal(await cards.count(),10);assert.equal(await page.locator('#plant-search').evaluate(e=>e===document.activeElement),true);
 await page.getByRole('button',{name:'Tomato',exact:true}).click();assert.equal(await cards.count(),3);
 await page.getByRole('button',{name:'All',exact:true}).click();await page.locator('#plant-select').selectOption('Apple');assert.equal(await cards.count(),2);
 await page.locator('#plant-select').selectOption('All Plants');await page.getByRole('searchbox').fill('no-such-plant');await page.getByText('No leaves on this branch yet.').waitFor();
 await page.getByRole('button',{name:'Explore all plants'}).click();assert.equal(await cards.count(),10);
 await cards.first().click();await page.getByRole('dialog').waitFor();await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'detached'});
 report.interactions.push('live search, clear-search focus, category + dropdown filters, empty-state reset, detail modal + Escape');
 await page.goto(origin+'/');await page.waitForTimeout(700);
 const cardPoint=await page.locator('.featured-card').evaluateAll(nodes=>{const e=nodes.find(n=>{const r=n.getBoundingClientRect();return r.left>50&&r.right<innerWidth-50});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};});
 await page.mouse.click(cardPoint.x,cardPoint.y);await page.waitForURL(/library\?entry=/);await page.getByRole('dialog').waitFor();
 report.interactions.push('carousel visible card click opens correct library detail');
 await page.goto(origin+'/');await page.waitForTimeout(300);const area=await page.locator('.carousel-viewport').boundingBox();
 const before=await page.locator('.carousel-track').evaluate(e=>e.dataset.phase);
 await page.mouse.move(700,area.y+100);await page.mouse.down();await page.mouse.move(450,area.y+100,{steps:12});await page.mouse.up();const release=await page.locator('.carousel-track').evaluate(e=>e.dataset.phase);await page.waitForTimeout(200);const after=await page.locator('.carousel-track').evaluate(e=>e.dataset.phase);assert.notEqual(before,release);assert.notEqual(release,after);assert.equal(page.url(),origin+'/');
 report.interactions.push('carousel dragging, click suppression and momentum after release');
 await page.goto(origin+'/detect');
 await page.locator('input[type=file]').setInputFiles({name:'wrong.txt',mimeType:'text/plain',buffer:Buffer.from('test')});await page.getByRole('alert').waitFor();assert.match(await page.getByRole('alert').innerText(),/JPG/);
 await page.locator('input[type=file]').setInputFiles({name:'broken.png',mimeType:'image/png',buffer:Buffer.from('not a png')});await page.getByRole('alert').waitFor();await page.getByText(/damaged or unreadable/).waitFor();
 await page.locator('input[type=file]').setInputFiles({name:'too-big.png',mimeType:'image/png',buffer:Buffer.alloc(11*1024*1024)});await page.getByText(/too large/).waitFor();
 await page.locator('input[type=file]').setInputFiles(new URL('../public/assets/plants/tomato-healthy.webp',import.meta.url).pathname.replace(/^\/([A-Z]:)/,'$1'));
 await page.getByAltText('Your selected leaf preview').waitFor();assert.equal(await page.getByRole('button',{name:'Analyze leaf'}).isDisabled(),true);assert.equal(await page.locator('.scan-overlay').count(),0);
 await page.getByRole('button',{name:'Remove selected image'}).click();await page.getByRole('button',{name:'Choose Image',exact:true}).waitFor();
 await page.getByRole('button',{name:'Preview illustrative sample: Healthy leaf',exact:true}).click();await page.getByAltText('Your selected leaf preview').waitFor();await page.getByText(/AI-generated sample/).waitFor();
 report.interactions.push('file type, corrupt image, size validation; real file preview, remove, sample preview; demo analysis disabled without fake scan');
 await page.setViewportSize({width:390,height:844});await page.goto(origin+'/');
 await page.getByRole('button',{name:'Open navigation'}).click();await page.getByRole('navigation').getByRole('link',{name:'Plant Library'}).focus();await page.keyboard.press('Escape');assert.equal(await page.getByRole('button',{name:'Open navigation'}).evaluate(e=>e===document.activeElement),true);
 await page.getByRole('button',{name:'Open navigation'}).click();await page.getByRole('navigation').getByRole('link',{name:'Plant Library'}).click();await page.waitForURL(origin+'/library');
 report.interactions.push('mobile menu, keyboard Escape focus restoration, client-side navigation');
 await page.setViewportSize({width:1440,height:1000});await page.goto(origin+'/');await page.getByRole('button',{name:'Sign up',exact:true}).first().click();await page.getByLabel('Create a simple profile on this device').fill('Asha');await page.getByRole('button',{name:'Save local profile'}).click();await page.getByText('Your profile is saved on this device.').waitFor();await page.getByRole('button',{name:'Keep exploring'}).click();await page.reload();await page.getByRole('button',{name:'Hi, Asha'}).waitFor();
 report.interactions.push('honest local-profile flow and browser persistence');
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto(origin+'/');await page.waitForTimeout(400);const reducedBefore=await page.locator('.carousel-track').evaluate(e=>e.dataset.phase);await page.waitForTimeout(400);const reducedAfter=await page.locator('.carousel-track').evaluate(e=>e.dataset.phase);assert.equal(reducedBefore,reducedAfter);report.interactions.push('reduced motion disables automatic carousel movement');
 const touchPage=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 await touchPage.goto(origin+'/');await touchPage.locator('.featured-card').first().waitFor();await touchPage.waitForTimeout(350);
 const touchBefore=await touchPage.locator('.carousel-track').evaluate(e=>e.dataset.phase);
 const touchArea=await touchPage.locator('.carousel-viewport').boundingBox();const touchY=Math.round(touchArea.y+100);
 const touchSession=await touchPage.context().newCDPSession(touchPage);
 await touchSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:315,y:touchY}]});
 for(let x=295;x>=115;x-=20) await touchSession.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:touchY}]});
 await touchSession.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await touchPage.waitForTimeout(100);
 const touchAfter=await touchPage.locator('.carousel-track').evaluate(e=>e.dataset.phase);assert.notEqual(touchBefore,touchAfter);assert.equal(touchPage.url(),origin+'/');await touchPage.close();report.interactions.push('real mobile touch swipe drags carousel without unwanted navigation');
 assert.deepEqual(errors,[]);
 await writeFile(new URL('browser-report.json',output),JSON.stringify(report,null,2));
 console.log(`PASS: ${report.responsive.length} route/viewport checks and ${report.interactions.length} interaction groups; zero page errors.`);
} finally {await browser.close();}



