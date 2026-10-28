import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
const b=await chromium.launch({channel:'chrome',headless:true});const p=await b.newPage({viewport:{width:1440,height:900}});
await p.goto('http://127.0.0.1:8502/?page=Detect');await p.locator('.choose-leaf-control').waitFor({timeout:60000});await p.locator('input[type=file]').waitFor({state:'attached',timeout:60000});await p.waitForTimeout(400);
const data=await p.evaluate(()=>{
 const info=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {tag:el.tagName,test:el.dataset.testid,class:el.className,x:r.x,y:r.y,w:r.width,h:r.height,z:s.zIndex,position:s.position,opacity:s.opacity,pointer:s.pointerEvents};};
 const picker=document.querySelector('.choose-leaf-control'),r=picker.getBoundingClientRect();
 return {stack:document.elementsFromPoint(r.x+r.width/2,r.y+r.height/2).map(info),widgets:[...document.querySelectorAll('.st-key-leaf-upload [data-testid]')].map(info),html:document.querySelector('.st-key-leaf-upload').outerHTML.slice(-18000)};
});await fs.writeFile('qa/controls-review/picker-dom.json',JSON.stringify(data,null,2));console.log(JSON.stringify({stack:data.stack,widgets:data.widgets},null,2));
const r=await p.locator('.choose-leaf-control').boundingBox();const event=p.waitForEvent('filechooser',{timeout:10000});await p.mouse.click(r.x+r.width/2,r.y+r.height/2);try{const chooser=await event;console.log('REAL_CLICK_FILE_CHOOSER: PASS');}catch(error){console.log('REAL_CLICK_FILE_CHOOSER: FAIL '+error.message);}await p.screenshot({path:'qa/controls-review/picker-diagnostic.png'});await b.close();
