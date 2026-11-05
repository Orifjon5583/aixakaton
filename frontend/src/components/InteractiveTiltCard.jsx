import React, { useRef, useState } from 'react';

/**
 * 3D Perspective Tilt Card
 * Smoothly tilts in 3D space tracking cursor movement with a subtle holographic glare.
 */
export default function InteractiveTiltCard({ children, className = '', glowColor = 'cyan', maxTilt = 5 }) {
  const cardRef = useRef(null);
  const [transform, setTransform] = useState('');
  const [glarePos, setGlarePos] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -maxTilt;
    const rotateY = ((x - centerX) / centerX) * maxTilt;

    setTransform(`perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateZ(8px)`);
    setGlarePos({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.15
    });
  };

  const handleMouseLeave = () => {
    setTransform('perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)');
    setGlarePos(prev => ({ ...prev, opacity: 0 }));
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform,
        transition: 'transform 0.18s cubic-bezier(0.2, 0.8, 0.2, 1)',
        transformStyle: 'preserve-3d'
      }}
      className={`relative overflow-hidden ${className}`}
    >
      {/* Dynamic Cursor Glare */}
      <div
        className="pointer-events-none absolute inset-0 z-20 transition-opacity duration-300"
        style={{
          opacity: glarePos.opacity,
          background: `radial-gradient(circle 240px at ${glarePos.x}% ${glarePos.y}%, rgba(6, 182, 212, 0.4), transparent 80%)`
        }}
      />
      {children}
    </div>
  );
}
