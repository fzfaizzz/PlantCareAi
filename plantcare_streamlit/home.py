from pathlib import Path

import streamlit as st

from .ui import asset, esc, render_html

FEATURED = [
    ("tomato-healthy", "Tomato", "Healthy"),
    ("tomato-early-blight", "Tomato", "Early Blight"),
    ("potato-late-blight", "Potato", "Late Blight"),
    ("apple-scab", "Apple", "Apple Scab"),
    ("corn-common-rust", "Corn", "Common Rust"),
    ("grape-powdery-mildew", "Grape", "Powdery Mildew"),
    ("healthy-dew-leaf", "Explore", "More Plants"),
]


def render_home():
    render_html("<style>" + Path(__file__).with_name("home.css").read_text(encoding="utf-8") + "</style>")
    cards = "".join(
        f'''<a href="#detect" class="home-leaf-card" aria-label="Explore {esc(plant)} {esc(condition)}" draggable="false"><img src="{asset(name)}" alt="Illustrative {esc(plant)} leaf: {esc(condition)}" draggable="false"><span class="leaf-card-label"><span class="play-circle" aria-hidden="true"><svg viewBox="0 0 16 18"><path d="M3 2.5 13 9 3 15.5Z"/></svg></span><span><strong>{esc(plant)}</strong><small>{esc(condition)}</small></span></span></a>'''
        for name, plant, condition in FEATURED * 3
    )
    st.html(f'''<section class="home-stage" aria-labelledby="plantcare-home-heading">
      <div class="home-copy"><h1 id="plantcare-home-heading">Detect Plant Diseases<br>with a Single Leaf Photo</h1><p>Upload a leaf image to identify supported plant diseases,<br class="desktop-break"> explore symptoms, and discover helpful plant-care guidance.</p></div>
      <span class="hand-note home-scan" aria-hidden="true">Scan<br>a leaf<svg viewBox="0 0 150 115"><path d="M12 8C120 0 142 50 105 100M105 100l3-25M105 100l23-10M3 14l-18 6M3 34l-18-8"/></svg></span>
      <svg class="home-scribble" viewBox="0 0 48 62" aria-hidden="true"><path d="M38 48C30 21 19 4 16 4c-3 1 8 26 22 44ZM25 58C12 39 3 33 3 35c1 7 10 17 22 23Z"/></svg>
      <div class="home-carousel" aria-label="Illustrative plant condition gallery"><div class="home-strip">{cards}</div></div>
      <div class="home-cta-row"><span class="hand-note free-note" aria-hidden="true">Free to try<svg viewBox="0 0 85 60"><path d="M4 4C14 35 39 45 73 39M73 39l-16-10M73 39l-13 12"/></svg></span><a class="detect-cta" href="#detect"><svg class="cta-scan-icon" viewBox="0 0 30 30" fill="none" aria-hidden="true"><path d="M10 3H6a3 3 0 0 0-3 3v4m17-7h4a3 3 0 0 1 3 3v4M3 20v4a3 3 0 0 0 3 3h4m17-7v4a3 3 0 0 1-3 3h-4M11 14v-3a4 4 0 0 1 8 0v3m-9 2h10v7H10z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Detect a Leaf</span><svg class="cta-arrow" viewBox="0 0 22 22" fill="none" aria-hidden="true"><path d="M4 11h14m-6-6 6 6-6 6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg></a></div>
    </section>''' + CAROUSEL_SCRIPT, unsafe_allow_javascript=True)


CAROUSEL_SCRIPT = r"""<script>
(() => {
  window.__plantcareCarouselCleanup?.();
  const stage = document.querySelector('.home-stage');
  const row = stage?.querySelector('.home-carousel');
  const strip = row?.querySelector('.home-strip');
  if (!row || !strip) return;
  const cards = [...strip.children];
  const media = matchMedia('(prefers-reduced-motion: reduce)');
  const controller = new AbortController(), options = {signal:controller.signal};
  const scrollRoot = stage.closest('[data-testid="stMain"]');
  let width=0, height=0, pitch=0, cycle=0, offset=0, velocity=0, positioned=false;
  let dragging=false, pointerId=null, lastX=0, lastMove=0, moved=0, raf=0, visible=true, previous=performance.now();
  row.tabIndex=0;
  row.setAttribute('role','region');
  row.setAttribute('aria-label','Drag or use arrow keys to explore illustrative leaf cards');
  strip.classList.add('is-driven');
  function fit() {
    const top=stage.getBoundingClientRect().top+(scrollRoot?.scrollTop || window.scrollY || 0);
    stage.style.height=`${Math.max(1,window.innerHeight-top-4)}px`;
    width=row.clientWidth; height=row.clientHeight;
    pitch=width>820 ? width/7.02 : Math.min(190,Math.max(145,width/2.55));
    cycle=cards.length*pitch;
    if(!positioned){offset=3*pitch;positioned=true;}
    paint();
  }
  function roundedQuad(points,radius) {
    const cuts=points.map((p,i)=>{
      const before=points[(i+points.length-1)%points.length], after=points[(i+1)%points.length];
      const lenA=Math.hypot(before[0]-p[0],before[1]-p[1]),lenB=Math.hypot(after[0]-p[0],after[1]-p[1]);
      const a=Math.min(radius,lenA/4),b=Math.min(radius,lenB/4);
      return [[p[0]+(before[0]-p[0])*a/lenA,p[1]+(before[1]-p[1])*a/lenA],[p[0]+(after[0]-p[0])*b/lenB,p[1]+(after[1]-p[1])*b/lenB]];
    });
    const n=value=>Math.round(value*10)/10;
    let path=`M${cuts[0][1].map(n).join(' ')}`;
    for(let step=1;step<=points.length;step++) {const i=step%points.length;path+=` L${cuts[i][0].map(n).join(' ')} Q${points[i].map(n).join(' ')} ${cuts[i][1].map(n).join(' ')}`;}
    return path+' Z';
  }
  function paint() {
    if(!width || !height || !cycle)return;
    const gap=width>820 ? Math.max(12,width*.011) : 12;
    cards.forEach((card,i)=>{
      const t=((i*pitch-offset+cycle/2)%cycle+cycle)%cycle-cycle/2;
      const d=Math.abs(t)/(width/2),x=width/2+t;
      if(x < -pitch*1.3 || x > width+pitch*1.3) {card.style.visibility='hidden';card.tabIndex=-1;return;}
      card.style.visibility='visible';card.tabIndex=0;
      const w=pitch-gap+(width>820?Math.min(d*d,1.3)*pitch*.035:0);
      const edge=q=>height*(.78+.19*Math.pow(Math.min(Math.abs(q),1),2.6));
      const lh=edge((t-w/2)/(width/2)),rh=edge((t+w/2)/(width/2)),h=Math.max(lh,rh);
      const y=height*.505-height*.012*Math.min(d*d,1.4);
      const points=[[0,(h-lh)/2],[w,(h-rh)/2],[w,(h+rh)/2],[0,(h+lh)/2]];
      card.style.width=`${w}px`;card.style.height=`${h}px`;
      card.style.transform=`translate3d(${(x-w/2).toFixed(2)}px,${(y-h/2).toFixed(2)}px,0)`;
      card.style.clipPath=`path('${roundedQuad(points,Math.max(10,Math.min(16,width*.01)))}')`;
      card.style.setProperty('--label-bottom',`${Math.max(Math.min(14,height*.06),(h-Math.min(lh,rh))/2+height*.045)}px`);
    });
  }
  function tick(now) {
    const dt=Math.min(Math.max((now-previous)/1000,0),.04);previous=now;
    if(visible&&!dragging&&!media.matches) {
      offset+=(Math.min(50,width*.035)+velocity)*dt;
      velocity*=Math.exp(-3.2*dt);
    }
    if(cycle)offset=((offset%cycle)+cycle)%cycle;
    if(visible)paint();
    if(!media.matches || dragging || Math.abs(velocity)>1)raf=requestAnimationFrame(tick);else raf=0;
  }
  function animate(){if(!raf){previous=performance.now();raf=requestAnimationFrame(tick);}}
  row.addEventListener('pointerdown',e=>{if(e.button!==0)return;dragging=true;pointerId=e.pointerId;moved=0;lastX=e.clientX;lastMove=performance.now();velocity=0;row.classList.add('is-dragging');row.setPointerCapture(e.pointerId);animate();},options);
  row.addEventListener('pointermove',e=>{if(!dragging||e.pointerId!==pointerId)return;const now=performance.now(),delta=e.clientX-lastX;offset-=delta;moved+=Math.abs(delta);velocity=Math.max(-1800,Math.min(1800,-delta/Math.max((now-lastMove)/1000,.008)));lastX=e.clientX;lastMove=now;paint();},options);
  function release(e){if(!dragging||e.pointerId!==pointerId)return;dragging=false;row.classList.remove('is-dragging');if(row.hasPointerCapture(e.pointerId))row.releasePointerCapture(e.pointerId);pointerId=null;animate();}
  row.addEventListener('pointerup',release,options);
  row.addEventListener('pointercancel',e=>{velocity=0;release(e);},options);
  row.addEventListener('lostpointercapture',()=>{dragging=false;row.classList.remove('is-dragging');},options);
  row.addEventListener('click',e=>{if(moved>5){e.preventDefault();e.stopPropagation();}}, {...options,capture:true});
  row.addEventListener('dragstart',e=>e.preventDefault(),options);
  row.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){offset+=e.key==='ArrowRight'?pitch:-pitch;velocity=0;paint();e.preventDefault();}},options);
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible)animate();});observer.observe(row);
  const resize=new ResizeObserver(()=>{width=row.clientWidth;height=row.clientHeight;pitch=width>820?width/7.02:Math.min(190,Math.max(145,width/2.55));cycle=cards.length*pitch;paint();});resize.observe(row);
  window.addEventListener('resize',fit,options);
  media.addEventListener('change',()=>{velocity=0;paint();animate();},options);
  let detectMountObserver=null,detectMountTimeout=0;
  function stopDetectWait(){detectMountObserver?.disconnect();detectMountObserver=null;clearTimeout(detectMountTimeout);}
  document.addEventListener('click',event=>{
    if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    const link=event.target.closest?.('a[href="#detect"]');
    if(!link||!stage.contains(link))return;
    event.preventDefault();stopDetectWait();
    const reveal=()=>{
      const target=document.querySelector('.st-key-detect-page');
      if(!target||!target.querySelector('.detect-heading')||target.getBoundingClientRect().height < 100)return false;
      target.id='detect';stopDetectWait();
      requestAnimationFrame(()=>{if(!controller.signal.aborted)target.scrollIntoView({block:'start',behavior:media.matches?'auto':'smooth'});});
      return true;
    };
    if(!reveal()){
      detectMountObserver=new MutationObserver(reveal);
      detectMountObserver.observe(document.body,{childList:true,subtree:true});
      detectMountTimeout=setTimeout(stopDetectWait,15000);
    }
  },options);
  fit();animate();
  window.__plantcareCarouselCleanup=()=>{cancelAnimationFrame(raf);controller.abort();stopDetectWait();observer.disconnect();resize.disconnect();};
})();
</script>"""


