// src/components/FloatingHome.jsx
import React, { useState, useCallback } from 'react';
import { motion, useMotionValue, animate } from 'framer-motion';
import HomeIcon from '../assets/icons/home.svg';

export default function FloatingHome() {
  const [collapsedEdge, setCollapsedEdge] = useState(null);
  const [prevPos, setPrevPos] = useState({ x: 0, y: 0 });

  const size = 56;
  const tabSize = 32;
  const threshold = 100;
  const x = useMotionValue(window.innerWidth - size - 16);
  const y = useMotionValue(window.innerHeight - size - 16);

  const handleDragEnd = useCallback(
    (_, info) => {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const px = info.point.x;
      const py = info.point.y;

      if (py < threshold) {
        setPrevPos({ x: px, y: py });
        setCollapsedEdge('top');
        animate(y, -tabSize / 2, { type: 'spring', stiffness: 300, damping: 20 });
        animate(x, vw / 2 - tabSize / 2, { type: 'spring', stiffness: 300, damping: 20 });
      } else if (py > vh - threshold) {
        setPrevPos({ x: px, y: py });
        setCollapsedEdge('bottom');
        animate(y, vh - tabSize / 2, { type: 'spring', stiffness: 300, damping: 20 });
        animate(x, vw / 2 - tabSize / 2, { type: 'spring', stiffness: 300, damping: 20 });
      } else {
        setCollapsedEdge(null);
        const targetX = px > vw / 2 ? vw - size - 16 : 16;
        const targetY = Math.min(Math.max(py, 16), vh - size - 16);
        animate(x, targetX, { type: 'spring', stiffness: 200, damping: 20 });
        animate(y, targetY, { type: 'spring', stiffness: 200, damping: 20 });
      }
    },
    [x, y]
  );

  const isTop = collapsedEdge === 'top';

  if (collapsedEdge) {
    const tabClasses = [
      'bg-teal-500',
      'shadow-lg',
      'flex items-center justify-center',
      isTop ? 'rounded-b-full h-4 w-8' : 'rounded-t-full h-4 w-8'
    ].join(' ');

    return (
      <motion.div
        style={{ x, y, touchAction: 'none', cursor: 'grab' }}
        className="fixed z-50 md:hidden"
        onClick={() => {
          setCollapsedEdge(null);
          animate(x, prevPos.x, { type: 'spring', stiffness: 200, damping: 20 });
          animate(y, prevPos.y, { type: 'spring', stiffness: 200, damping: 20 });
        }}
      >
        <div className={tabClasses}>
          <HomeIcon
            className={`text-white ${isTop ? 'rotate-180' : ''} w-3 h-3`}
            aria-hidden="true"
          />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.button
      style={{ x, y, touchAction: 'none', cursor: 'grab' }}
      drag
      dragMomentum={false}
      dragConstraints={{
        top: 0,
        left: 0,
        right: window.innerWidth - size - 16,
        bottom: window.innerHeight - size - 16,
      }}
      onDragEnd={handleDragEnd}
      onClick={() => window.location.assign('/')}
      className="floating-home"
      aria-label="Go Home"
    >
      <HomeIcon className="w-6 h-6 text-white" aria-hidden="true" />
    </motion.button>
  );
}
