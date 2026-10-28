import { useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Play } from 'lucide-react';
import { featuredPlants } from '../data/plants';

const AUTO_SPEED = -50;
const DECAY = 3;

function roundedQuad(points, radius) {
  const corners = points.map((point, index) => {
    const previous = points[(index + points.length - 1) % points.length];
    const next = points[(index + 1) % points.length];
    const toward = target => {
      const length = Math.hypot(target.x - point.x, target.y - point.y);
      const distance = Math.min(radius, length / 3);
      return { x: point.x + (target.x - point.x) * distance / length, y: point.y + (target.y - point.y) * distance / length };
    };
    return { point, entry: toward(previous), exit: toward(next) };
  });
  const xy = point => `${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
  return `path("M ${xy(corners[0].entry)} ${corners.map((corner, index) => `${index ? `L ${xy(corner.entry)} ` : ''}Q ${xy(corner.point)} ${xy(corner.exit)}`).join(' ')} Z")`;
}

export default function PlantCarousel() {
  const section = useRef(null);
  const viewport = useRef(null);
  const track = useRef(null);
  const actions = useRef({ nudge() {} });

  useLayoutEffect(() => {
    const root = section.current;
    const windowFrame = viewport.current;
    const strip = track.current;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const cards = [...strip.querySelectorAll('.featured-card')];
    const state = {
      phase: 0, velocity: 0, inertia: false, hover: false, focus: false,
      visible: true, pointerId: null, dragging: false, startX: 0, startY: 0, lastX: 0,
      lastMove: 0, suppressClickUntil: 0, autoAfter: performance.now() + 1000,
      width: 1586, scale: 1, bandHeight: 250, mobile: false,
    };
    let alive = true;
    let frame = null;
    let wakeTimer = null;
    let lastFrame = performance.now();

    const dimensions = () => state.mobile
      ? { width: 640, center: 320, pitch: 240, first: 80, cy: state.bandHeight / state.scale / 2, cardWidth: 215, widthGrowth: 15, height: Math.min(330, Math.max(190, state.bandHeight * .8 / state.scale)), heightGrowth: 55, radius: 12 }
      : { width: state.width / state.scale, center: state.width / state.scale / 2, pitch: 229, first: state.width / state.scale / 2 - 688, cy: state.bandHeight / state.scale / 2, cardWidth: 210, widthGrowth: 8, height: 306, heightGrowth: 72, radius: 15 };
    const wrapPhase = () => {
      if (state.focus && state.pointerId === null && windowFrame.contains(document.activeElement)) return;
      const cycle = dimensions().pitch * featuredPlants.length;
      state.phase = ((state.phase + cycle / 2) % cycle + cycle) % cycle - cycle / 2;
    };
    const geometry = (index, group) => {
      const config = dimensions();
      const x = config.first + (index + (group - 1) * featuredPlants.length) * config.pitch + state.phase;
      const distance = Math.min(1.3, Math.abs(x - config.center) / config.center);
      const width = config.cardWidth + config.widthGrowth * distance ** 2;
      const cy = config.cy - (state.mobile ? 6 : 10) * distance ** 2;
      const left = x - width / 2;
      const right = x + width / 2;
      const heightAt = edge => Math.min(2 * Math.min(cy, state.bandHeight / state.scale - cy) - 24, config.height + config.heightGrowth * Math.min(1.3, Math.abs(edge - config.center) / config.center) ** (state.mobile ? 2 : 2.6));
      const leftHeight = heightAt(left);
      const rightHeight = heightAt(right);
      const topLeft = cy - leftHeight / 2;
      const topRight = cy - rightHeight / 2;
      const top = Math.min(topLeft, topRight);
      const bottomLeft = cy + leftHeight / 2;
      const bottomRight = cy + rightHeight / 2;
      return { x, width, cy, left, right, top, height: Math.max(bottomLeft, bottomRight) - top, topLeft: topLeft - top, topRight: topRight - top, bottomLeft: bottomLeft - top, bottomRight: bottomRight - top, distance };
    };
    const paint = () => {
      const scale = state.scale;
      const config = dimensions();
      for (const card of cards) {
        const shape = geometry(Number(card.dataset.index), Number(card.dataset.group));
        const visible = shape.right * scale >= -30 && shape.left * scale <= state.width + 30;
        if (!visible && !card.contains(document.activeElement)) {
          if (card.style.display !== 'none') card.style.display = 'none';
          continue;
        }
        if (card.style.display === 'none') card.style.display = '';
        card.style.transform = `translate3d(${(shape.left * scale).toFixed(2)}px, ${(shape.top * scale).toFixed(2)}px, 0)`;
        card.style.width = `${shape.width * scale}px`;
        card.style.height = `${shape.height * scale}px`;
        card.style.clipPath = roundedQuad([
          { x: 0, y: shape.topLeft * scale },
          { x: shape.width * scale, y: shape.topRight * scale },
          { x: shape.width * scale, y: shape.bottomRight * scale },
          { x: 0, y: shape.bottomLeft * scale },
        ], config.radius * scale);
        card.style.setProperty('--card-edge', shape.distance.toFixed(4));
        card.style.setProperty('--label-y', String(Math.min(shape.bottomLeft, shape.bottomRight) - 64));
        card.style.setProperty('--card-progress', (shape.x / config.width).toFixed(4));
      }
      strip.dataset.phase = state.phase.toFixed(3);
      strip.style.setProperty('--carousel-position', String(state.phase));
      strip.style.setProperty('--carousel-unit', `${scale}px`);
    };
    const autoAllowed = now => !motion.matches && !state.focus && state.pointerId === null && now >= state.autoAfter;
    const schedule = () => {
      if (!alive || document.hidden || !state.visible || frame !== null) return;
      lastFrame = performance.now();
      frame = requestAnimationFrame(tick);
    };
    const wakeForAuto = now => {
      clearTimeout(wakeTimer);
      if (!motion.matches && !state.focus && state.pointerId === null && state.autoAfter > now) {
        wakeTimer = setTimeout(schedule, state.autoAfter - now + 1);
      }
    };
    const tick = now => {
      frame = null;
      if (!alive || document.hidden || !state.visible) return;
      const elapsed = Math.min(Math.max((now - lastFrame) / 1000, 0), 0.05);
      lastFrame = now;
      const automatic = autoAllowed(now);
      if (state.pointerId === null) {
        if (motion.matches) { state.velocity = 0; state.inertia = false; }
        else if (state.inertia) {
          const target = automatic ? AUTO_SPEED : 0;
          const decay = Math.exp(-DECAY * elapsed);
          state.phase += target * elapsed + (state.velocity - target) * (1 - decay) / DECAY;
          state.velocity = target + (state.velocity - target) * decay;
          if (Math.abs(state.velocity - target) < 0.12) { state.velocity = target; state.inertia = false; }
        } else if (automatic) {
          state.velocity = AUTO_SPEED;
          state.phase += AUTO_SPEED * elapsed;
        } else state.velocity = 0;
      }
      wrapPhase();
      paint();
      if (state.pointerId === null && (state.inertia || automatic) && !motion.matches) frame = requestAnimationFrame(tick);
      else wakeForAuto(now);
    };
    const measure = () => {
      const oldConfig = dimensions();
      const nextMobile = window.innerWidth <= 820;
      state.mobile = nextMobile;
      const config = dimensions();
      if (oldConfig.width !== config.width) state.phase *= config.pitch / oldConfig.pitch;
      state.width = windowFrame.getBoundingClientRect().width || window.innerWidth; state.bandHeight = windowFrame.getBoundingClientRect().height || 250;
      state.scale = state.mobile ? state.width / 640 : (parseFloat(getComputedStyle(root).getPropertyValue('--u')) || state.width / 1586);
      paint();
      schedule();
    };
    const finishPointer = event => {
      if (event.type === 'lostpointercapture' && event.target !== windowFrame) return;
      if (state.pointerId === null || (event.pointerId !== undefined && event.pointerId !== state.pointerId)) return;
      const capturedPointer = state.pointerId;
      const dragged = state.dragging;
      state.pointerId = null;
      state.dragging = false;
      root.classList.remove('is-dragging');
      windowFrame.classList.remove('is-dragging');
      if (dragged) {
        state.suppressClickUntil = performance.now() + 450;
        if (performance.now() - state.lastMove > 140 || event.type === 'pointercancel' || motion.matches) state.velocity = 0;
        state.inertia = Math.abs(state.velocity) > 0.12;
      } else { state.velocity = 0; state.inertia = false; }
      state.autoAfter = performance.now() + 800;
      if (windowFrame.hasPointerCapture(capturedPointer)) windowFrame.releasePointerCapture(capturedPointer);
      wrapPhase();
      paint();
      schedule();
    };
    const pointerDown = event => {
      if ((event.pointerType === 'mouse' && event.button !== 0) || !event.isPrimary || state.pointerId !== null) return;
      state.pointerId = event.pointerId;
      state.startX = state.lastX = event.clientX;
      state.startY = event.clientY;
      state.lastMove = performance.now();
      state.velocity = 0;
      state.inertia = false;
      state.dragging = false;
      state.suppressClickUntil = 0;
      clearTimeout(wakeTimer);
    };
    const pointerMove = event => {
      if (state.pointerId !== event.pointerId) return;
      const totalX = event.clientX - state.startX;
      if (!state.dragging) {
        if (Math.abs(totalX) <= 6 || Math.abs(totalX) < Math.abs(event.clientY - state.startY) * 1.15) return;
        state.dragging = true;
        windowFrame.setPointerCapture(event.pointerId);
        root.classList.add('is-dragging');
        windowFrame.classList.add('is-dragging');
      }
      event.preventDefault();
      const now = performance.now();
      const dx = (event.clientX - state.lastX) / state.scale;
      const instant = Math.max(-2600, Math.min(2600, dx / Math.max((now - state.lastMove) / 1000, 0.008)));
      state.phase += dx;
      state.velocity = state.velocity * 0.25 + instant * 0.75;
      state.lastX = event.clientX;
      state.lastMove = now;
      wrapPhase();
      paint();
    };
    const pointerEnter = event => {
      if (event.pointerType !== 'mouse') return;
      state.hover = true;
      if (!state.inertia && state.pointerId === null) state.velocity = 0;
      clearTimeout(wakeTimer);
    };
    const pointerLeave = event => {
      if (event.pointerType !== 'mouse') return;
      state.hover = false;
      schedule();
    };
    const clickCapture = event => {
      if (event.detail !== 0 && performance.now() < state.suppressClickUntil) {
        event.preventDefault();
        event.stopPropagation();
        state.suppressClickUntil = 0;
      }
    };
    const focusIn = event => {
      if (state.pointerId !== null) return;
      state.focus = true;
      state.velocity = 0;
      state.inertia = false;
      clearTimeout(wakeTimer);
      const card = event.target.closest('.featured-card');
      if (card) {
        const shape = geometry(Number(card.dataset.index), Number(card.dataset.group));
        const inset = 12;
        if (shape.left < inset) state.phase += inset - shape.left;
        else if (shape.right > dimensions().width - inset) state.phase -= shape.right - dimensions().width + inset;
        paint();
        windowFrame.scrollLeft = 0;
        requestAnimationFrame(() => { if (alive) windowFrame.scrollLeft = 0; });
      }
    };
    const focusOut = event => {
      if (root.contains(event.relatedTarget)) return;
      state.focus = false;
      state.autoAfter = performance.now() + 450;
      wrapPhase();
      paint();
      schedule();
    };
    const visibilityChanged = () => {
      if (document.hidden) {
        if (frame !== null) cancelAnimationFrame(frame);
        frame = null;
        clearTimeout(wakeTimer);
        if (state.pointerId !== null) finishPointer({ type: 'pointercancel', pointerId: state.pointerId });
      } else schedule();
    };
    const preferenceChanged = () => {
      state.velocity = 0;
      state.inertia = false;
      state.autoAfter = performance.now() + 1000;
      paint();
      schedule();
    };
    actions.current.nudge = direction => {
      const pitch = dimensions().pitch;
      if (motion.matches) {
        state.phase += direction * pitch;
        wrapPhase();
        paint();
      } else {
        state.velocity = direction * pitch * DECAY;
        state.inertia = true;
        state.autoAfter = performance.now() + 1000;
        schedule();
      }
    };

    const visibility = new IntersectionObserver(([entry]) => {
      state.visible = entry.isIntersecting;
      if (state.visible) schedule();
      else if (frame !== null) { cancelAnimationFrame(frame); frame = null; }
    });
    visibility.observe(root);
    const resize = new ResizeObserver(measure);
    resize.observe(windowFrame);
    window.addEventListener('resize', measure);
    windowFrame.addEventListener('pointerdown', pointerDown);
    windowFrame.addEventListener('pointermove', pointerMove, { passive: false });
    window.addEventListener('pointerup', finishPointer);
    window.addEventListener('pointercancel', finishPointer);
    windowFrame.addEventListener('lostpointercapture', finishPointer);
    root.addEventListener('pointerenter', pointerEnter);
    root.addEventListener('pointerleave', pointerLeave);
    windowFrame.addEventListener('click', clickCapture, true);
    root.addEventListener('focusin', focusIn);
    root.addEventListener('focusout', focusOut);
    document.addEventListener('visibilitychange', visibilityChanged);
    motion.addEventListener('change', preferenceChanged);
    measure();
    return () => {
      alive = false;
      if (frame !== null) cancelAnimationFrame(frame);
      clearTimeout(wakeTimer);
      resize.disconnect();
      visibility.disconnect();
      window.removeEventListener('resize', measure);
      windowFrame.removeEventListener('pointerdown', pointerDown);
      windowFrame.removeEventListener('pointermove', pointerMove);
      window.removeEventListener('pointerup', finishPointer);
      window.removeEventListener('pointercancel', finishPointer);
      windowFrame.removeEventListener('lostpointercapture', finishPointer);
      root.removeEventListener('pointerenter', pointerEnter);
      root.removeEventListener('pointerleave', pointerLeave);
      windowFrame.removeEventListener('click', clickCapture, true);
      root.removeEventListener('focusin', focusIn);
      root.removeEventListener('focusout', focusOut);
      document.removeEventListener('visibilitychange', visibilityChanged);
      motion.removeEventListener('change', preferenceChanged);
      if (state.pointerId !== null && windowFrame.hasPointerCapture(state.pointerId)) windowFrame.releasePointerCapture(state.pointerId);
      actions.current.nudge = () => {};
    };
  }, []);

  return (
    <section className="carousel-section" ref={section} aria-label="Explore plant conditions">
      <div className="carousel-viewport" ref={viewport} style={{ position: 'relative', width: '100%', height: '100%', padding: 0, overflow: 'hidden', touchAction: 'pan-y' }}>
        <div className="carousel-track" ref={track} style={{ position: 'relative', width: '100%', height: '100%', transform: 'none' }}>
          {[0, 1, 2].map(group => (
            <div className="carousel-group" key={group} aria-hidden={group !== 1 || undefined} style={{ display: 'contents' }}>
              {featuredPlants.map((plant, index) => (
                <Link
                  key={plant.id}
                  className="featured-card"
                  data-index={index}
                  data-group={group}
                  to={plant.plant === 'Explore' ? '/library' : `/library?entry=${plant.id}`}
                  tabIndex={group === 1 ? 0 : -1}
                  draggable="false"
                  style={{ position: 'absolute', transform: 'none', borderRadius: 0, '--card-i': index }}
                >
                  <img src={plant.image} alt={`${plant.plant} — ${plant.condition}; AI-generated illustration`} width="360" height="540" draggable="false" loading={group === 1 ? 'eager' : 'lazy'} />
                  <span className="featured-shade" />
                  <span className="featured-label"><span className="play-icon"><Play size={16} fill="currentColor" aria-hidden="true" /></span><span><strong>{plant.plant}</strong><small>{plant.condition}</small></span></span>
                </Link>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="carousel-controls"><button className="icon-button" aria-label="Previous plants" onClick={() => actions.current.nudge(1)}><ChevronLeft size={18} /></button><span>Drag to explore</span><button className="icon-button" aria-label="Next plants" onClick={() => actions.current.nudge(-1)}><ChevronRight size={18} /></button></div>
    </section>
  );
}






