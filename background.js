// background.js — анимированный фон "нейросеть"
(function() {
    function initBackground() {
        let canvas = document.getElementById('particles-canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'particles-canvas';
            document.body.insertBefore(canvas, document.body.firstChild);
        }

        const ctx = canvas.getContext('2d');

        let width, height;
        let particles = [];

        // === НАСТРОЙКИ ===
        const PARTICLE_COUNT = 80;
        const MAX_DISTANCE = 150;
        const PARTICLE_SIZE = 2;
        const SPEED = 0.4;
        const LINE_COLOR = '255, 255, 255';
        const DOT_COLOR = '255, 255, 255';
        const MAX_LINE_OPACITY = 0.25;
        const DOT_OPACITY = 0.6;

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }

        function createParticles() {
            particles = [];
            for (let i = 0; i < PARTICLE_COUNT; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    vx: (Math.random() - 0.5) * SPEED * 2,
                    vy: (Math.random() - 0.5) * SPEED * 2,
                });
            }
        }

        function updateParticles() {
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;

                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;

                p.x = Math.max(0, Math.min(width, p.x));
                p.y = Math.max(0, Math.min(height, p.y));
            });
        }

        function drawParticles() {
            ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < MAX_DISTANCE) {
                        const opacity = (1 - dist / MAX_DISTANCE) * MAX_LINE_OPACITY;
                        ctx.strokeStyle = `rgba(${LINE_COLOR}, ${opacity})`;
                        ctx.lineWidth = 0.8;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }

            particles.forEach(p => {
                ctx.fillStyle = `rgba(${DOT_COLOR}, ${DOT_OPACITY})`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, PARTICLE_SIZE, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        function animate() {
            updateParticles();
            drawParticles();
            requestAnimationFrame(animate);
        }

        window.addEventListener('resize', () => {
            resize();
            createParticles();
        });

        resize();
        createParticles();
        animate();
    }

    // Ждём загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBackground);
    } else {
        initBackground();
    }
})();