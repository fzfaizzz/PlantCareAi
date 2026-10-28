import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
export default function Modal({ title, children, onClose, className = '' }) {
  const ref = useRef(null), startedOutside = useRef(false);
  useEffect(() => { const dialog = ref.current; const previous = document.activeElement; dialog.showModal(); document.body.classList.add('modal-open'); return () => { dialog.close(); document.body.classList.remove('modal-open'); previous?.focus(); }; }, []);
  const outside = event => { const r=event.currentTarget.getBoundingClientRect(); return event.target===event.currentTarget && (event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom); };
  return <dialog ref={ref} className={`modal ${className}`} aria-label={title} onCancel={onClose} onPointerDown={event=>{startedOutside.current=outside(event);}} onClick={event=>{if(startedOutside.current && outside(event))onClose();startedOutside.current=false;}}><button className="icon-button modal-close" onClick={onClose} aria-label="Close dialog"><X size={21}/></button>{children}</dialog>;
}
