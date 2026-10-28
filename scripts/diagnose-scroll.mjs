import {chromium} from '@playwright/test';
const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:900}});page.on('pageerror',e=>console.log('JS_ERROR',e.message));
await page.goto('http://127.0.0.1:8502');await page.locator('.home-stage').waitFor({timeout:60000});await page.locator('input[type=file]').waitFor({state:'attached',timeout:60000});await page.waitForTimeout(500);
await page.evaluate(()=>{window.__observedClicks=[];for(const capture of [true,false])document.addEventListener('click',e=>window.__observedClicks.push({capture,defaultPrevented:e.defaultPrevented,target:e.target.outerHTML.slice(0,300)}),capture);});
console.log('BEFORE',await page.evaluate(()=>({scripts:[...document.querySelectorAll('.stHtml script')].map(el=>({observer:el.textContent.includes('detectMountObserver'),detect:el.textContent.includes('__plantcareDetectCleanup')})),page:document.querySelector('.st-key-detect-page')?.getBoundingClientRect().toJSON(),id:document.getElementById('detect')?.className,body:document.body?.outerHTML.slice(0,120)})));
await page.getByRole('link',{name:'Detect a Leaf',exact:true}).click();await page.waitForTimeout(2500);
console.log('AFTER',await page.evaluate(()=>({clicks:window.__observedClicks,page:document.querySelector('.st-key-detect-page')?.getBoundingClientRect().toJSON(),mainScroll:document.querySelector('[data-testid=stMain]')?.scrollTop,hash:location.hash})));
await page.screenshot({path:'qa/controls-review/scroll-diagnostic.png'});await browser.close();
