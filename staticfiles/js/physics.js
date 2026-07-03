/* =====================================================
   DOCVAULT — PHYSICS ENGINE
   Spring animations, Magnetic cursor, Ripples, Tilt
   ===================================================== */

(function(window) {

/* ─── Spring Physics ──────────────────────────────── */
class SpringValue {
    constructor(initial, { stiffness=180, damping=22, mass=1 } = {}) {
        this.value    = initial;
        this.target   = initial;
        this.velocity = 0;
        this.stiffness = stiffness;
        this.damping   = damping;
        this.mass      = mass;
        this._raf      = null;
        this._cb       = null;
    }
    to(target, callback) {
        this.target = target;
        this._cb = callback;
        if (!this._raf) this._loop();
    }
    _loop() {
        const dt = 1/60;
        const force   = -this.stiffness * (this.value - this.target);
        const damping = -this.damping * this.velocity;
        const accel   = (force + damping) / this.mass;
        this.velocity += accel * dt;
        this.value    += this.velocity * dt;
        if (this._cb) this._cb(this.value);
        const settled = Math.abs(this.value - this.target) < .001 && Math.abs(this.velocity) < .001;
        if (settled) {
            this.value = this.target;
            if (this._cb) this._cb(this.value);
            this._raf = null;
        } else {
            this._raf = requestAnimationFrame(() => this._loop());
        }
    }
    stop() { if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; } }
}

/* ─── Ripple Effect ───────────────────────────────── */
function addRipple(el) {
    el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.addEventListener('click', e => {
        const rect = el.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const ripple = document.createElement('span');
        const size = Math.max(rect.width, rect.height) * 2;
        ripple.style.cssText = `
            position:absolute;
            width:${size}px; height:${size}px;
            left:${x - size/2}px; top:${y - size/2}px;
            border-radius:50%;
            background:rgba(255,255,255,.2);
            transform:scale(0);
            animation:rippleAnim .7s ease-out forwards;
            pointer-events:none; z-index:9999;
        `;
        el.appendChild(ripple);
        setTimeout(() => ripple.remove(), 700);
    });
}

/* ─── 3D Card Tilt ────────────────────────────────── */
function initTilt(selector = '.premium-card, .stat-card') {
    document.querySelectorAll(selector).forEach(card => {
        let mx = 0, my = 0, rx = new SpringValue(0, {stiffness:120, damping:18}), ry = new SpringValue(0, {stiffness:120, damping:18});
        card.style.transformStyle = 'preserve-3d';
        card.style.transition = 'box-shadow .3s';
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            mx = (e.clientX - rect.left) / rect.width  - .5;
            my = (e.clientY - rect.top)  / rect.height - .5;
            rx.to(my * -12, v => card.style.transform = `perspective(1000px) rotateX(${v}deg) rotateY(${ry.value}deg) translateZ(6px)`);
            ry.to(mx *  12, v => card.style.transform = `perspective(1000px) rotateX(${rx.value}deg) rotateY(${v}deg) translateZ(6px)`);
        });
        card.addEventListener('mouseleave', () => {
            rx.to(0, v => card.style.transform = `perspective(1000px) rotateX(${v}deg) rotateY(${ry.value}deg) translateZ(0px)`);
            ry.to(0, v => card.style.transform = `perspective(1000px) rotateX(${rx.value}deg) rotateY(${v}deg) translateZ(0px)`);
        });
    });
}

/* ─── Magnetic Buttons ────────────────────────────── */
function initMagnetic(selector = '.btn-neon, .btn-glass') {
    document.querySelectorAll(selector).forEach(btn => {
        let bx = new SpringValue(0, {stiffness:200, damping:20}),
            by = new SpringValue(0, {stiffness:200, damping:20});
        btn.addEventListener('mousemove', e => {
            const rect = btn.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top  + rect.height / 2;
            const dx = (e.clientX - cx) * .25;
            const dy = (e.clientY - cy) * .25;
            bx.to(dx, v => btn.style.transform = `translate(${v}px, ${by.value}px)`);
            by.to(dy, v => btn.style.transform = `translate(${bx.value}px, ${v}px)`);
        });
        btn.addEventListener('mouseleave', () => {
            bx.to(0, v => btn.style.transform = `translate(${v}px, ${by.value}px)`);
            by.to(0, v => btn.style.transform = `translate(${bx.value}px, ${v}px)`);
        });
    });
}

/* ─── Animated Counter ────────────────────────────── */
function animateCounter(el, target, duration=1800) {
    let start = null;
    const ease = t => t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t+2,3)/2;
    function step(ts) {
        if (!start) start = ts;
        const progress = Math.min((ts - start) / duration, 1);
        el.textContent = Math.round(ease(progress) * target);
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = target;
    }
    requestAnimationFrame(step);
}

function initCounters() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target || el.textContent);
                if (!isNaN(target)) { el.textContent = '0'; animateCounter(el, target); }
                observer.unobserve(el);
            }
        });
    }, { threshold: .3 });
    document.querySelectorAll('.counter').forEach(el => {
        el.dataset.target = el.textContent;
        observer.observe(el);
    });
}

/* ─── Floating Orbs Canvas ────────────────────────── */
function initOrbCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width  = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;

    const orbs = Array.from({length: 4}, (_, i) => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - .5) * .4,
        vy: (Math.random() - .5) * .4,
        r: 80 + Math.random() * 120,
        color: ['rgba(108,99,255,', 'rgba(0,212,255,', 'rgba(0,245,160,', 'rgba(255,107,157,'][i],
    }));

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        orbs.forEach(o => {
            o.x += o.vx; o.y += o.vy;
            if (o.x < -o.r || o.x > canvas.width + o.r) o.vx *= -1;
            if (o.y < -o.r || o.y > canvas.height + o.r) o.vy *= -1;
            const g = ctx.createRadialGradient(o.x, o.y, 0, o.x, o.y, o.r);
            g.addColorStop(0, o.color + '.18)');
            g.addColorStop(1, o.color + '0)');
            ctx.beginPath();
            ctx.arc(o.x, o.y, o.r, 0, Math.PI * 2);
            ctx.fillStyle = g;
            ctx.fill();
        });
        requestAnimationFrame(draw);
    }
    draw();
    window.addEventListener('resize', () => {
        canvas.width  = canvas.parentElement.offsetWidth;
        canvas.height = canvas.parentElement.offsetHeight;
    });
}

/* ─── Scroll Reveal ───────────────────────────────── */
function initScrollReveal() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                const el = entry.target;
                el.style.animationDelay = (el.dataset.delay || i * 80) + 'ms';
                el.classList.add('animate-fade-up');
                observer.unobserve(el);
            }
        });
    }, { threshold: .1, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal').forEach(el => { el.style.opacity = '0'; observer.observe(el); });
}

/* ─── Live Clock ──────────────────────────────────── */
function initLiveClock(id) {
    const el = document.getElementById(id);
    if (!el) return;
    function tick() {
        const now = new Date();
        el.textContent = now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
    }
    tick();
    setInterval(tick, 1000);
}

/* ─── Sidebar Mobile Toggle ───────────────────────── */
function initSidebarToggle() {
    const btn = document.getElementById('sidebarToggleBtn');
    const sidebar = document.querySelector('.sidebar-framework');
    if (btn && sidebar) {
        btn.addEventListener('click', () => sidebar.classList.toggle('open'));
        document.addEventListener('click', e => {
            if (!sidebar.contains(e.target) && !btn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

/* ─── Search Bar Live ─────────────────────────────── */
function initSearch() {
    const input = document.getElementById('globalSearch');
    if (!input) return;
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            const q = input.value.trim();
            if (q) window.location.href = '/documents/?search=' + encodeURIComponent(q);
        }
    });
}

/* ─── CSS Injection for Ripple ────────────────────── */
function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes rippleAnim {
            to { transform:scale(1); opacity:0; }
        }
    `;
    document.head.appendChild(style);
}

/* ─── Auto-init on DOM ready ──────────────────────── */
function init() {
    injectStyles();
    document.querySelectorAll('.btn-neon, .btn-glass, .btn-danger-glass, button, .btn').forEach(addRipple);
    initTilt();
    initMagnetic();
    initCounters();
    initScrollReveal();
    initOrbCanvas('orbCanvas');
    initLiveClock('liveClock');
    initSidebarToggle();
    initSearch();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

/* ─── Expose API ──────────────────────────────────── */
window.DocVaultPhysics = { SpringValue, addRipple, initTilt, initMagnetic, animateCounter, initOrbCanvas };

})(window);
