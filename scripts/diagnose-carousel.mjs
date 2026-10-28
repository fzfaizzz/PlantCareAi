import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:900}});let errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8502');await page.locator('input[type=file]').waitFor({state:'attached',timeout:60000});await page.waitForTimeout(500);
console.log(JSON.stringify(await page.evaluate(()=>({stages:[...document.querySelectorAll('.home-stage')].map(el=>({html:el.outerHTML.slice(-150),rect:el.getBoundingClientRect().toJSON()})),strips:[...document.querySelectorAll('.home-strip')].map(el=>({class:el.className,first:el.firstElementChild?.getAttribute('style')})),scripts:[...document.querySelectorAll('.stHtml script')].map(el=>({length:el.textContent.length,start:el.textContent.slice(0,500),end:el.textContent.slice(-700)}))})),null,2));console.log('ERRORS',errors);
const source=await fs.readFile('plantcare_streamlit/home.py','utf8');const script=source.split('CAROUSEL_SCRIPT = r\"\"\"')[1].split('\"\"\"')[0];
console.log('SANITIZER',await page.evaluate(async script=>{const url=performance.getEntriesByType('resource').map(e=>e.name).find(n=>n.includes('purify.es.'));const mod=await import(url);const config={USE_PROFILES:{html:true},FORCE_BODY:true,ADD_TAGS:['script','style'],ADD_ATTR:['src','type','async','defer','nonce','crossorigin','referrerpolicy','integrity']};return {original:mod.t.sanitize(script,config).length,spaced:mod.t.sanitize(script.replace('height<100','height < 100'),config).length,source:script.length};},script));

await browser.close();
