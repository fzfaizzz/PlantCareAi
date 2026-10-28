import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { ArrowRight, Check, Leaf, Menu, Sprout, X } from 'lucide-react';
import Modal from './components/Modal';
import SmoothScrolling from './components/SmoothScrolling';
import Preloader from './components/Preloader';
import HomePage from './pages/HomePage';
import LibraryPage from './pages/LibraryPage';
import DetectPage from './pages/DetectPage';
import AboutPage from './pages/AboutPage';
import HowItWorksPage from './pages/HowItWorksPage';
import assets from './data/plantAssets';
const navigation = [['/','Home'],['/library','Plant Library'],['/about','About']];
function ProfileDialog({ mode, onClose, onSave }) {
  const [name,setName]=useState(''), [saved,setSaved]=useState(false), [error,setError]=useState('');
  const save = event => { event.preventDefault(); try { const profile={name:name.trim()}; localStorage.setItem('plantcare-profile',JSON.stringify(profile)); onSave(profile); setSaved(true); } catch { setError('Your browser could not save a profile. You can still explore without one.'); } };
  return <Modal title={mode==='signup'?'Create a garden profile':'Your garden profile'} onClose={onClose} className="profile-modal"><span className="round-symbol"><Sprout/></span><span className="eyebrow">A little room to grow</span><h2>{saved?'Welcome to your greener days.':mode==='signup'?'Make yourself at home.':'Welcome back, plant lover.'}</h2><p>Online accounts are not connected yet. Every current feature is free to explore without signing in.</p>{saved?<><p className="profile-success"><Check size={18}/> Your profile is saved on this device.</p><button className="button button-primary" onClick={onClose}>Keep exploring <ArrowRight size={17}/></button></>:<form onSubmit={save}><label htmlFor="profile-name">Create a simple profile on this device</label><input id="profile-name" value={name} onChange={e=>setName(e.target.value)} placeholder="Your first name" maxLength={40} required autoComplete="given-name"/><small>Your name stays in this browser. This is not an online account.</small>{error&&<p role="alert">{error}</p>}<button className="button button-primary" type="submit">Save local profile <ArrowRight size={17}/></button><button className="text-button" type="button" onClick={onClose}>Continue without a profile</button></form>}</Modal>;
}
function Navbar() {
  const [open,setOpen]=useState(false),[dialog,setDialog]=useState(null),[profile,setProfile]=useState(()=>{try{return JSON.parse(localStorage.getItem('plantcare-profile'));}catch{return null;}});
  const location=useLocation(), menuButton=useRef(null);
  useEffect(()=>{setOpen(false);},[location.pathname]);
  useEffect(()=>{if(!open)return;const escape=e=>{if(e.key==='Escape'){setOpen(false);menuButton.current?.focus();}};window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);},[open]);
  return <><header className="site-header"><div className="navbar"><Link to="/" className="brand" aria-label="PlantCare AI home"><span className="brand-mark"><svg viewBox="0 0 44 46" aria-hidden="true"><path d="M7 38C0 15 20 10 42 2C40 24 34 42 12 41Z" fill="currentColor"/><path d="M2 45C11 31 25 20 37 9" fill="none" stroke="#f7fbef" strokeWidth="1.8"/><path d="M2 45 9 36" fill="none" stroke="#175337" strokeWidth="1.8"/></svg></span><span>PlantCare AI</span></Link><nav className={`main-nav ${open?'is-open':''}`} aria-label="Main navigation" id="main-navigation">{navigation.map(([path,label])=><NavLink to={path} key={path} end={path==='/'}>{label}</NavLink>)}<div className="mobile-account"><button className="button button-secondary" onClick={()=>{setDialog('login');setOpen(false);}}>Log in</button><button className="button button-primary" onClick={()=>{setDialog('signup');setOpen(false);}}>Sign up</button></div></nav><div className="account-actions"><button className="button button-secondary" onClick={()=>setDialog('login')}>{profile?.name?`Hi, ${profile.name}`:'Log in'}</button><button className="button button-primary" onClick={()=>setDialog('signup')}>Sign up</button></div><button ref={menuButton} className="menu-toggle icon-button" aria-expanded={open} aria-controls="main-navigation" aria-label={open?'Close navigation':'Open navigation'} onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button></div></header>{dialog&&<ProfileDialog mode={dialog} onClose={()=>setDialog(null)} onSave={setProfile}/>}</>;
}
export function BotanicalDecorations({variant=''}) {
  return <div className={`botanical-decorations ${variant}`} aria-hidden="true"><img className="decor decor-left" src={assets['reference-leaf-upper-left']} alt="" width="450" height="450"/><img className="decor decor-right" src={assets['reference-leaf-upper-right']} alt="" width="450" height="450"/><img className="decor decor-bottom-left" src={assets['home-foliage-bottom-left']} alt="" width="550" height="450" loading="lazy"/><img className="decor decor-bottom-right" src={assets['home-foliage-bottom-right']} alt="" width="550" height="450" loading="lazy"/><svg className="botanical-lines" viewBox="0 0 1440 900" preserveAspectRatio="none"><path d="M-10 95 C160 96 214 164 378 152 M1000 900 C1100 780 1248 877 1455 724"/></svg></div>;
}
export function Badge({children}) {return <span className="badge"><Sprout size={19} fill="currentColor" strokeWidth={1.2}/>{children}</span>;}
export function Scribble({className=''}) {return <svg className={`scribble ${className}`} width="48" height="62" viewBox="0 0 48 62" fill="none" aria-hidden="true"><path d="M38 48C30 21 19 4 16 4c-3 1 8 26 22 44ZM25 58C12 39 3 33 3 35c1 7 10 17 22 23Z"/></svg>;}
export function HandArrow({className='',flip=false}) {
 const path=className.includes('arrow-rise')?'M20 90C71 75 96 53 116 13M116 13l-18 6M116 13l-2 22':className.includes('arrow-free')?'M8 8C16 43 41 64 69 58M69 58l-14-10M69 58l-14 9':'M8 10C97 2 128 45 97 84M97 84l1-23M97 84l22-10';
 return <svg className={`hand-arrow ${className}`} style={flip?{transform:'scaleX(-1)'}:undefined} viewBox={className.includes('arrow-free')?'0 0 80 80':'0 0 140 100'} fill="none" aria-hidden="true"><path d={path}/></svg>;
}function Footer() {return <footer className="site-footer"><Link to="/" className="footer-brand"><Leaf size={17}/> PlantCare AI</Link><span>A little care. A greener tomorrow.</span><span>Botanical imagery is AI-generated and illustrative.</span></footer>;}
function RouteEffects() {
  const {pathname}=useLocation(),first=useRef(true);
  useEffect(()=>{const title={'/':'Plant health starts with a single leaf','/library':'Plant Disease Library','/detect':'Detect Disease','/about':'About PlantCare AI','/how-it-works':'How It Works'}[pathname]||'Page not found';document.title=`${title} — PlantCare AI`;window.scrollTo({top:0,behavior:'instant'});if(!first.current)document.querySelector('main h1')?.focus({preventScroll:true});first.current=false;},[pathname]);
  useEffect(()=>{const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target);}});},{threshold:.08});document.querySelectorAll('[data-reveal]').forEach(node=>observer.observe(node));return()=>observer.disconnect();},[pathname]);
  return null;
}
export default function App() {
 const {pathname}=useLocation();
 const [viewport,setViewport]=useState(()=>({width:window.innerWidth,height:window.innerHeight}));
 const {width,height}=viewport;
 useEffect(()=>{const update=()=>setViewport({width:window.innerWidth,height:window.innerHeight});window.addEventListener('resize',update);return()=>window.removeEventListener('resize',update);},[]);
 const frame={'/':['home',1586,992],'/library':['library',1536,1024],'/detect':['detect',1314,870],'/about':['about',1536,1024]}[pathname];
 const scale=frame?(['home','detect'].includes(frame[0])&&width>820?Math.min(width/frame[1],height/frame[2]):width/frame[1]):1;
 const className=frame?`app-shell reference-shell route-${frame[0]}`:'app-shell route-other';
 return <div className={className} style={frame?{'--u':`${scale}px`,'--frame-height':`${scale*frame[2]}px`,'--detect-u':`${Math.min(width/1314,height/870)}px`,'--detect-frame-height':`${Math.min(width/1314,height/870)*870}px`}:undefined}><a className="skip-link" href="#main-content">Skip to content</a><Preloader/><SmoothScrolling/><Navbar/><RouteEffects/><main id="main-content"><Routes><Route path="/" element={<HomePage/>}/><Route path="/library" element={<LibraryPage/>}/><Route path="/detect" element={<DetectPage/>}/><Route path="/about" element={<AboutPage/>}/><Route path="/how-it-works" element={<HowItWorksPage/>}/><Route path="*" element={<section className="not-found"><Badge>Let's find your way</Badge><h1 tabIndex="-1">A little off the garden path.</h1><p>This page isn't here, but there's plenty more to explore.</p><Link to="/" className="button button-primary">Back to home <ArrowRight size={18}/></Link></section>}/></Routes></main><Footer/></div>;
}

