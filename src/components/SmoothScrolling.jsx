import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';

export default function SmoothScrolling() {
 const instance = useRef(null);
 const { pathname } = useLocation();
 useEffect(() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const setup = () => {
   instance.current?.destroy();
   instance.current = motion.matches ? null : new Lenis({
    autoRaf: true, anchors: true, duration: 1.05, lerp: 0.085, smoothWheel: true,
    syncTouch: false, prevent: node => !!node.closest('dialog'),
   });
  };
  setup();
  if (document.body.classList.contains('is-preloading')) instance.current?.stop();
  const modalObserver = new MutationObserver(() => {
   if (document.body.classList.contains('modal-open') || document.body.classList.contains('is-preloading')) instance.current?.stop();
   else instance.current?.start();
  });
  modalObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  motion.addEventListener('change', setup);
  return () => { modalObserver.disconnect(); motion.removeEventListener('change', setup); instance.current?.destroy(); instance.current = null; };
 }, []);
 useEffect(() => { instance.current?.scrollTo(0, { immediate: true }); }, [pathname]);
 return null;
}
