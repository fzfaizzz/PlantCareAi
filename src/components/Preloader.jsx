import { useEffect, useId, useState } from 'react';
import './preloader.css';

function SculptedLeaf({ className }) {
 const id = useId().replace(/:/g, '');
 return <svg className={`preloader-leaf ${className}`} viewBox="0 0 100 144" fill="none" aria-hidden="true"><defs><linearGradient id={id} x1="4" y1="116" x2="88" y2="20" gradientUnits="userSpaceOnUse"><stop stopColor="#043e2c"/><stop offset=".32" stopColor="#116747"/><stop offset=".49" stopColor="#4c9a64"/><stop offset=".52" stopColor="#b3ce86"/><stop offset=".72" stopColor="#7eaf68"/><stop offset="1" stopColor="#d7e6ab"/></linearGradient><linearGradient id={`${id}v`} x1="21" y1="133" x2="79" y2="20" gradientUnits="userSpaceOnUse"><stop stopColor="#7ca96a"/><stop offset=".55" stopColor="#e7efb4"/><stop offset="1" stopColor="#f7f9d9"/></linearGradient><linearGradient id={`${id}s`} x1="21" y1="17" x2="65" y2="98" gradientUnits="userSpaceOnUse"><stop stopColor="#ffffff" stopOpacity=".6"/><stop offset="1" stopColor="#ffffff" stopOpacity="0"/></linearGradient><radialGradient id={`${id}d`} cx=".3" cy=".23" r=".8"><stop stopColor="#ffffff" stopOpacity=".95"/><stop offset=".4" stopColor="#e4f5d7" stopOpacity=".3"/><stop offset="1" stopColor="#074f35" stopOpacity=".8"/></radialGradient></defs><path d="M24 136C-8 90 14 30 90 10C106 79 93 127 24 136Z" fill="#12482e"/><path d="M22 133C-10 87 12 27 88 7C104 76 91 124 22 133Z" fill={`url(#${id})`} stroke="#8fba7540" strokeWidth=".8"/><path d="M19 137C35 100 57 59 82 17M38 99Q24 93 17 80M46 83Q60 88 76 75M55 66Q41 60 36 45M63 50Q77 53 87 40M30 115Q49 120 68 106" stroke={`url(#${id}v)`} strokeWidth="1.1" strokeLinecap="round" opacity=".7"/><path d="M23 119C7 79 25 38 79 15C50 44 30 83 23 119Z" fill={`url(#${id}s)`} opacity=".48"/><ellipse cx="66" cy="52" rx="5" ry="7.5" transform="rotate(27 66 52)" fill={`url(#${id}d)`} stroke="#f2ffe3" strokeOpacity=".5" strokeWidth=".5"/><ellipse cx="64.5" cy="49.5" rx="1.3" ry="1.8" fill="#fff" opacity=".8"/></svg>;
}

export default function Preloader() {
 const [phase, setPhase] = useState('loading');
 const [progress, setProgress] = useState(0);
 useEffect(() => {
  let alive = true;
  let minimumTimer, maximumTimer, exitTimer;
  document.body.classList.add('is-preloading');
  const images = [...new Map([...document.querySelectorAll('main img')].slice(0, 8).map(image => [image.currentSrc || image.src, image])).values()];
  const jobs = [document.fonts.ready, ...images.map(image => image.decode().catch(() => {}))];
  let finished = 0;
  const assets = Promise.allSettled(jobs.map(job => Promise.resolve(job).finally(() => { if (alive) setProgress(++finished / jobs.length); })));
  const minimum = new Promise(resolve => { minimumTimer = setTimeout(resolve, 1350); });
  const maximum = new Promise(resolve => { maximumTimer = setTimeout(resolve, 3500); });
  Promise.race([Promise.all([assets, minimum]), maximum]).then(() => {
   if (!alive) return;
   setProgress(1);
   setPhase('leaving');
   document.body.classList.remove('is-preloading');
   exitTimer = setTimeout(() => { if (alive) setPhase('done'); }, 600);
  });
  return () => { alive = false; clearTimeout(minimumTimer); clearTimeout(maximumTimer); clearTimeout(exitTimer); document.body.classList.remove('is-preloading'); };
 }, []);
 if (phase === 'done') return null;
 return <div className={`plant-preloader ${phase === 'leaving' ? 'is-leaving' : ''}`} role="status" aria-live="polite" aria-label="Loading PlantCare AI"><div className="preloader-inner"><div className="preloader-scene" aria-hidden="true"><div className="preloader-halo"/><div className="preloader-glass"/><div className="preloader-platform"/><div className="preloader-orbit orbit-one"/><div className="preloader-sprout"><span className="preloader-stem"/><SculptedLeaf className="leaf-left"/><SculptedLeaf className="leaf-right"/><SculptedLeaf className="leaf-center"/></div><div className="preloader-ground"/><span className="preloader-spark spark-one"/><span className="preloader-spark spark-two"/></div><p className="preloader-brand"><span className="preloader-wordmark-leaf" aria-hidden="true"/>PlantCare AI</p><p className="preloader-caption">A little care. A greener tomorrow.</p><div className="preloader-track" aria-hidden="true"><span style={{ transform: `scaleX(${Math.max(.08, progress)})` }}/></div><div className="preloader-footer"><span className="preloader-status">{phase === 'leaving' ? 'Ready to grow' : 'Preparing your experience'}</span><span className="preloader-dots" aria-hidden="true"><i/><i/><i/></span></div></div></div>;
}
