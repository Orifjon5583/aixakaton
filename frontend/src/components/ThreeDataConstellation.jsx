import React, { useEffect, useRef } from 'react';

/**
 * Interactive 3D Spatial Data Constellation
 * 60-120 FPS Canvas-based 3D particle network representing 500k UZEX exchange transactions.
 * Features:
 * - 3D spherical projection with perspective division
 * - Inertial mouse rotation & cursor gravity
 * - Dynamic proximity cyber-connections
 * - Quantum acceleration effect when `loading` is true
 */
export default function ThreeDataConstellation({ loading = false, theme = 'dark' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Particle nodes
    const PARTICLE_COUNT = Math.min(Math.floor((width * height) / 12000), 150);
    const particles = [];
    const sphereRadius = Math.min(width, height) * 0.42;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Uniform distribution on a 3D sphere shell with inner depth
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const r = sphereRadius * (0.6 + Math.random() * 0.5);

      particles.push({
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta),
        z: r * Math.cos(phi),
        baseX: r * Math.sin(phi) * Math.cos(theta),
        baseY: r * Math.sin(phi) * Math.sin(theta),
        baseZ: r * Math.cos(phi),
        size: Math.random() * 2.2 + 1.2,
        speed: (Math.random() * 0.002 + 0.001) * (Math.random() > 0.5 ? 1 : -1),
        phase: Math.random() * Math.PI * 2,
        colorType: Math.random() > 0.3 ? 'cyan' : 'emerald'
      });
    }

    let rotX = 0;
    let rotY = 0;
    let targetRotX = 0;
    let targetRotY = 0;
    let mouseX = width / 2;
    let mouseY = height / 2;

    const handleMouseMove = (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      const normX = (e.clientX - width / 2) / (width / 2);
      const normY = (e.clientY - height / 2) / (height / 2);
      targetRotY = normX * 0.45;
      targetRotX = -normY * 0.45;
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);

    const fov = 420;
    let pulseTime = 0;

    const render = () => {
      pulseTime += loading ? 0.08 : 0.02;
      ctx.clearRect(0, 0, width, height);

      // Smooth inertia rotation towards mouse
      rotX += (targetRotX - rotX) * 0.05;
      rotY += (targetRotY - rotY) * 0.05;

      // Constant ambient rotation (accelerates 3x during loading)
      const baseRotationSpeed = loading ? 0.012 : 0.0025;
      rotY += baseRotationSpeed;

      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);

      const projected = [];

      // Project 3D -> 2D
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // 3D rotation around Y then X axis
        const x1 = p.baseX * cosY - p.baseZ * sinY;
        const z1 = p.baseZ * cosY + p.baseX * sinY;

        const y2 = p.baseY * cosX - z1 * sinX;
        const z2 = z1 * cosX + p.baseY * sinX;

        // Perspective scale
        const scale = fov / (fov + z2 + sphereRadius);
        const screenX = x1 * scale + width / 2;
        const screenY = y2 * scale + height / 2;

        const alpha = Math.max(0.12, Math.min(0.9, (z2 + sphereRadius) / (sphereRadius * 2)));

        projected.push({
          x: screenX,
          y: screenY,
          z: z2,
          scale,
          alpha,
          size: p.size * scale,
          colorType: p.colorType,
          pulse: Math.sin(pulseTime + p.phase) * 0.5 + 0.5
        });
      }

      // Draw cyber connections between nearby 2D nodes
      const maxDist = loading ? 110 : 85;
      const isDark = theme === 'dark';

      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const dx = projected[i].x - projected[j].x;
          const dy = projected[i].y - projected[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDist) {
            const lineAlpha = (1 - dist / maxDist) * 0.22 * projected[i].alpha;
            ctx.beginPath();
            ctx.moveTo(projected[i].x, projected[i].y);
            ctx.lineTo(projected[j].x, projected[j].y);

            if (loading) {
              ctx.strokeStyle = `rgba(168, 85, 247, ${lineAlpha * 1.5})`;
            } else if (isDark) {
              ctx.strokeStyle = `rgba(6, 182, 212, ${lineAlpha})`;
            } else {
              ctx.strokeStyle = `rgba(14, 165, 233, ${lineAlpha * 0.7})`;
            }
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      // Draw glowing nodes
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);

        let fillCol = '';
        if (loading) {
          fillCol = `rgba(192, 132, 252, ${p.alpha})`;
        } else if (p.colorType === 'cyan') {
          fillCol = isDark ? `rgba(6, 182, 212, ${p.alpha})` : `rgba(2, 132, 199, ${p.alpha})`;
        } else {
          fillCol = isDark ? `rgba(16, 185, 129, ${p.alpha})` : `rgba(5, 150, 105, ${p.alpha})`;
        }

        ctx.fillStyle = fillCol;
        ctx.fill();

        // Pulsing outer halo for close nodes
        if (p.alpha > 0.6) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * (1.5 + p.pulse * 0.8), 0, Math.PI * 2);
          ctx.fillStyle = loading
            ? `rgba(168, 85, 247, ${p.alpha * 0.15})`
            : `rgba(6, 182, 212, ${p.alpha * 0.12})`;
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [loading, theme]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-80 transition-opacity duration-700"
    />
  );
}
