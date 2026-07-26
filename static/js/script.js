/* =====================================================
   MentorConnect v3.0 — Advanced Motion & UX Script
===================================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* ─────────────────────────────────────────────
       1. CURSOR GLOW
    ───────────────────────────────────────────── */

    const cursorGlow = document.getElementById("cursor-glow");
    if (cursorGlow) {
        let mouseX = 0, mouseY = 0;
        let currentX = 0, currentY = 0;

        document.addEventListener("mousemove", (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        function animateCursor() {
            currentX += (mouseX - currentX) * 0.1;
            currentY += (mouseY - currentY) * 0.1;
            cursorGlow.style.left = currentX + "px";
            cursorGlow.style.top  = currentY + "px";
            requestAnimationFrame(animateCursor);
        }
        animateCursor();
    }

    /* ─────────────────────────────────────────────
       2. PAGE FADE-IN
    ───────────────────────────────────────────── */

    document.body.classList.add("page-fade-in");

    /* ─────────────────────────────────────────────
       3. AUTO-HIDE FLASH MESSAGES
    ───────────────────────────────────────────── */

    const flashMessages = document.querySelectorAll(".flash-message");
    flashMessages.forEach(function (flash) {
        setTimeout(() => {
            flash.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            flash.style.opacity = "0";
            flash.style.transform = "translateY(-10px)";
            setTimeout(() => flash.remove(), 500);
        }, 3500);
    });

    /* ─────────────────────────────────────────────
       4. RIPPLE EFFECT ON BUTTONS
    ───────────────────────────────────────────── */

    function createRipple(e) {
        const btn = e.currentTarget;
        const existing = btn.querySelector(".ripple");
        if (existing) existing.remove();

        const circle = document.createElement("span");
        const diameter = Math.max(btn.clientWidth, btn.clientHeight);
        const radius   = diameter / 2;

        const rect = btn.getBoundingClientRect();
        circle.style.width  = circle.style.height = diameter + "px";
        circle.style.left   = (e.clientX - rect.left - radius) + "px";
        circle.style.top    = (e.clientY - rect.top  - radius) + "px";
        circle.classList.add("ripple");

        btn.appendChild(circle);
        setTimeout(() => circle.remove(), 700);
    }

    document.querySelectorAll("button").forEach(btn => {
        btn.addEventListener("click", createRipple);
    });

    /* ─────────────────────────────────────────────
       5. STAGGERED SCROLL-REVEAL
    ───────────────────────────────────────────── */

    const revealSelectors = [
        ".dashboard-card",
        ".mentor-card",
        ".request-card",
        ".session-card",
        ".feedback-card",
        ".stat-card",
        ".feature-card",
        ".about-section",
        ".session-form-card"
    ].join(", ");

    const revealItems = document.querySelectorAll(revealSelectors);
    revealItems.forEach((el, i) => {
        el.classList.add("stagger-item");
        el.style.transitionDelay = `${(i % 8) * 0.07}s`;
    });

    const revealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("revealed");
                    revealObserver.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    revealItems.forEach(el => revealObserver.observe(el));

    /* ─────────────────────────────────────────────
       6. 3D TILT CARD EFFECT
    ───────────────────────────────────────────── */

    const tiltCards = document.querySelectorAll(
        ".dashboard-card, .mentor-card, .session-card, .stat-card, .feature-card"
    );

    tiltCards.forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const rect   = card.getBoundingClientRect();
            const x      = e.clientX - rect.left;
            const y      = e.clientY - rect.top;
            const cx     = rect.width  / 2;
            const cy     = rect.height / 2;
            const rotateX = ((y - cy) / cy) * -6;
            const rotateY = ((x - cx) / cx) *  6;

            card.style.transform    = `translateY(-10px) perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            card.style.transition   = "transform 0.1s ease";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform  = "";
            card.style.transition = "transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)";
        });
    });

    /* ─────────────────────────────────────────────
       7. MAGNETIC BUTTON EFFECT
    ───────────────────────────────────────────── */

    const magnetBtns = document.querySelectorAll(
        ".hero-buttons button, .dashboard-actions button"
    );

    magnetBtns.forEach(btn => {
        btn.addEventListener("mousemove", (e) => {
            const rect  = btn.getBoundingClientRect();
            const x     = e.clientX - rect.left - rect.width / 2;
            const y     = e.clientY - rect.top  - rect.height / 2;
            btn.style.transform    = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            btn.style.transition   = "transform 0.15s ease";
        });

        btn.addEventListener("mouseleave", () => {
            btn.style.transform  = "";
            btn.style.transition = "transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)";
        });
    });

    /* ─────────────────────────────────────────────
       8. TYPED TEXT EFFECT (hero)
    ───────────────────────────────────────────── */

    const typedEl = document.getElementById("typed-text");
    if (typedEl) {
        const words  = typedEl.dataset.words
            ? typedEl.dataset.words.split("|")
            : ["Connect.", "Learn.", "Grow."];
        let wi = 0, ci = 0, isDeleting = false;

        function typeLoop() {
            const word    = words[wi % words.length];
            const display = isDeleting
                ? word.substring(0, ci--)
                : word.substring(0, ci++);

            typedEl.textContent = display;

            let delay = isDeleting ? 60 : 110;
            if (!isDeleting && ci === word.length + 1) {
                delay = 1800;
                isDeleting = true;
            } else if (isDeleting && ci === 0) {
                isDeleting = false;
                wi++;
                delay = 350;
            }
            setTimeout(typeLoop, delay);
        }
        typeLoop();
    }

    /* ─────────────────────────────────────────────
       9. DASHBOARD COUNTER ANIMATION
    ───────────────────────────────────────────── */

    const counters = document.querySelectorAll(".counter");
    counters.forEach(counter => {
        const target = Number(counter.dataset.target);
        let count    = 0;
        const speed  = Math.max(1, Math.ceil(target / 80));

        const tick = () => {
            if (count < target) {
                count = Math.min(count + speed, target);
                counter.textContent = count;
                requestAnimationFrame(tick);
            }
        };

        // Start when visible
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(e => {
                if (e.isIntersecting) { tick(); obs.unobserve(counter); }
            });
        });
        obs.observe(counter);
    });

    /* ─────────────────────────────────────────────
       10. LIVE MENTOR SEARCH
    ───────────────────────────────────────────── */

    const mentorSearch = document.getElementById("mentorSearch") ||
                         document.getElementById("searchInput");
    if (mentorSearch) {
        mentorSearch.addEventListener("keyup", function () {
            const val   = this.value.toLowerCase();
            const cards = document.querySelectorAll(".mentor-card");
            cards.forEach(card => {
                const match = card.innerText.toLowerCase().includes(val);
                card.style.display = match ? "" : "none";
                if (match) {
                    card.style.animation = "none";
                    requestAnimationFrame(() => {
                        card.style.animation = "fadeSlideUp 0.3s ease";
                    });
                }
            });
        });
    }

    /* ─────────────────────────────────────────────
       11. CHAT AUTO SCROLL
    ───────────────────────────────────────────── */

    const chatMessages = document.querySelector(".messages");
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /* ─────────────────────────────────────────────
       12. ENTER TO SEND MESSAGE
    ───────────────────────────────────────────── */

    const messageInput = document.querySelector(".message-form input[name='message']");
    if (messageInput) {
        messageInput.addEventListener("keypress", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                this.form.submit();
            }
        });
    }

    /* ─────────────────────────────────────────────
       13. CHARACTER COUNTER
    ───────────────────────────────────────────── */

    const commentBox = document.getElementById("comments");
    if (commentBox) {
        const counter = document.createElement("small");
        counter.style.cssText = "display:block; margin-top:6px; font-size:12px; color:var(--text-muted); text-align:right;";
        commentBox.parentNode.appendChild(counter);
        commentBox.addEventListener("input", function () {
            const len   = this.value.length;
            const max   = 500;
            counter.textContent = `${len} / ${max}`;
            counter.style.color = len > 450 ? "#f87171" : "var(--text-muted)";
        });
    }

    /* ─────────────────────────────────────────────
       14. SESSION DATE VALIDATION
    ───────────────────────────────────────────── */

    const sessionDate = document.getElementById("session_date");
    if (sessionDate) {
        sessionDate.min = new Date().toISOString().split("T")[0];
    }

    /* ─────────────────────────────────────────────
       15. STAR RATING
    ───────────────────────────────────────────── */

    const stars       = document.querySelectorAll(".rating-star");
    const ratingInput = document.getElementById("rating");

    if (stars.length > 0 && ratingInput) {
        stars.forEach(star => {
            star.addEventListener("click", function () {
                const rating = this.dataset.value;
                ratingInput.value = rating;
                stars.forEach(s => {
                    s.style.color      = s.dataset.value <= rating ? "#fbbf24" : "var(--text-muted)";
                    s.style.transform  = s.dataset.value <= rating ? "scale(1.2)" : "scale(1)";
                    s.style.transition = "all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)";
                });
            });

            star.addEventListener("mouseenter", function () {
                const val = this.dataset.value;
                stars.forEach(s => {
                    s.style.color = s.dataset.value <= val ? "#fbbf24" : "var(--text-muted)";
                });
            });

            star.addEventListener("mouseleave", () => {
                const current = ratingInput.value || 0;
                stars.forEach(s => {
                    s.style.color = s.dataset.value <= current ? "#fbbf24" : "var(--text-muted)";
                });
            });
        });
    }

    /* ─────────────────────────────────────────────
       16. COPY MEETING LINK
    ───────────────────────────────────────────── */

    document.querySelectorAll(".copy-link, .copy-btn").forEach(button => {
        button.addEventListener("click", function () {
            const text = this.dataset.link || this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                const orig = this.innerHTML;
                this.innerHTML = "✓ Copied!";
                this.style.background = "rgba(16,185,129,0.2)";
                this.style.borderColor = "rgba(16,185,129,0.4)";
                this.style.color = "#34d399";
                setTimeout(() => {
                    this.innerHTML = orig;
                    this.style.background = "";
                    this.style.borderColor = "";
                    this.style.color = "";
                }, 1800);
            });
        });
    });

    /* ─────────────────────────────────────────────
       17. PROFILE IMAGE PREVIEW
    ───────────────────────────────────────────── */

    const imageInput = document.getElementById("profileImage");
    if (imageInput) {
        imageInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = e => {
                const preview = document.getElementById("previewImage");
                if (preview) {
                    preview.src = e.target.result;
                    preview.style.animation = "scaleIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)";
                }
            };
            reader.readAsDataURL(file);
        });
    }

    /* ─────────────────────────────────────────────
       18. FORM VALIDATION (enhanced)
    ───────────────────────────────────────────── */

    const forms = document.querySelectorAll("form");
    forms.forEach(form => {
        form.addEventListener("submit", function (e) {
            const required = form.querySelectorAll("[required]");
            let valid = true;

            required.forEach(input => {
                if (input.value.trim() === "") {
                    input.style.borderColor = "rgba(239,68,68,0.6)";
                    input.style.boxShadow   = "0 0 0 3px rgba(239,68,68,0.15)";
                    input.style.animation   = "shake 0.4s ease";
                    valid = false;

                    setTimeout(() => {
                        input.style.animation = "";
                    }, 400);
                } else {
                    input.style.borderColor = "";
                    input.style.boxShadow   = "";
                }
            });

            if (!valid) {
                e.preventDefault();
                showToast("⚠️ Please fill all required fields.");
            }
        });
    });

    /* ─────────────────────────────────────────────
       19. DISABLE MULTIPLE SUBMITS
    ───────────────────────────────────────────── */

    forms.forEach(form => {
        form.addEventListener("submit", () => {
            const btn = form.querySelector("button[type='submit']");
            if (btn) {
                setTimeout(() => {
                    btn.disabled     = true;
                    btn.innerHTML    = `<span class="spinner-inline"></span> Processing...`;
                    btn.style.opacity = "0.8";
                }, 100);
            }
        });
    });

    /* ─────────────────────────────────────────────
       20. CONFIRM DELETE / ACCEPT / REJECT
    ───────────────────────────────────────────── */

    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            if (!confirm("Delete this user?")) e.preventDefault();
        });
    });

    document.querySelectorAll(".accept-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            if (!confirm("Accept this mentorship request?")) e.preventDefault();
        });
    });

    document.querySelectorAll(".reject-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            if (!confirm("Reject this mentorship request?")) e.preventDefault();
        });
    });

    /* ─────────────────────────────────────────────
       21. TABLE SEARCH FILTER
    ───────────────────────────────────────────── */

    const tableSearch = document.getElementById("tableSearch");
    if (tableSearch) {
        tableSearch.addEventListener("keyup", function () {
            const val = this.value.toLowerCase();
            document.querySelectorAll("tbody tr").forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(val) ? "" : "none";
            });
        });
    }

    /* ─────────────────────────────────────────────
       22. SMOOTH SCROLL (anchor links)
    ───────────────────────────────────────────── */

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    /* ─────────────────────────────────────────────
       23. BACK TO TOP BUTTON
    ───────────────────────────────────────────── */

    const topBtn = document.getElementById("topBtn");
    if (topBtn) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 300) {
                topBtn.style.display = "flex";
                topBtn.style.animation = "scaleIn 0.3s ease";
            } else {
                topBtn.style.display = "none";
            }
        });

        topBtn.onclick = () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        };
    }

    /* ─────────────────────────────────────────────
       24. LOADER
    ───────────────────────────────────────────── */

    window.showLoader = () => {
        const loader = document.getElementById("loader");
        if (loader) loader.style.display = "flex";
    };

    window.hideLoader = () => {
        const loader = document.getElementById("loader");
        if (loader) loader.style.display = "none";
    };

    /* ─────────────────────────────────────────────
       25. TOAST NOTIFICATION
    ───────────────────────────────────────────── */

    window.showToast = function (message, type = "info") {
        let container = document.querySelector(".toast-container");
        if (!container) {
            container = document.createElement("div");
            container.className = "toast-container";
            document.body.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = message;
        container.appendChild(toast);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => toast.classList.add("show"));
        });

        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    };

    /* ─────────────────────────────────────────────
       26. CURRENT YEAR IN FOOTER
    ───────────────────────────────────────────── */

    const yearEl = document.getElementById("currentYear");
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    /* ─────────────────────────────────────────────
       27. ONLINE / OFFLINE STATUS
    ───────────────────────────────────────────── */

    function updateStatus() {
        const status = document.getElementById("networkStatus");
        if (!status) return;
        status.innerHTML = navigator.onLine ? "🟢 Online" : "🔴 Offline";
    }

    window.addEventListener("online",  updateStatus);
    window.addEventListener("offline", updateStatus);
    updateStatus();

    /* ─────────────────────────────────────────────
       28. NAVBAR SCROLL EFFECT
    ───────────────────────────────────────────── */

    const navbar = document.querySelector("body > nav");
    if (navbar) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 30) {
                navbar.style.background = "rgba(4,4,26,0.92)";
                navbar.style.boxShadow  = "0 8px 40px rgba(0,0,0,0.4)";
            } else {
                navbar.style.background = "rgba(4,4,26,0.75)";
                navbar.style.boxShadow  = "0 4px 30px rgba(0,0,0,0.3)";
            }
        });
    }

    /* ─────────────────────────────────────────────
       29. INPUT FOCUS GLOW ANIMATION
    ───────────────────────────────────────────── */

    document.querySelectorAll("input, textarea, select").forEach(input => {
        input.addEventListener("focus", function () {
            this.parentElement.style.position = "relative";
        });
    });

    /* ─────────────────────────────────────────────
       30. HERO PARTICLE CANVAS
    ───────────────────────────────────────────── */

    const canvas = document.getElementById("hero-canvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let particles = [];
        let animId;

        function resizeCanvas() {
            canvas.width  = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }

        class Particle {
            constructor() { this.reset(); }
            reset() {
                this.x    = Math.random() * canvas.width;
                this.y    = Math.random() * canvas.height;
                this.vx   = (Math.random() - 0.5) * 0.4;
                this.vy   = (Math.random() - 0.5) * 0.4;
                this.r    = Math.random() * 1.5 + 0.5;
                this.alpha = Math.random() * 0.5 + 0.1;
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < 0 || this.x > canvas.width)  this.vx *= -1;
                if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(139, 92, 246, ${this.alpha})`;
                ctx.fill();
            }
        }

        function initParticles() {
            particles = [];
            const count = Math.min(80, Math.floor(canvas.width * canvas.height / 12000));
            for (let i = 0; i < count; i++) particles.push(new Particle());
        }

        function drawLines() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx   = particles[i].x - particles[j].x;
                    const dy   = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx*dx + dy*dy);

                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(99,102,241,${0.15 * (1 - dist/120)})`;
                        ctx.lineWidth   = 0.5;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }
        }

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => { p.update(); p.draw(); });
            drawLines();
            animId = requestAnimationFrame(animate);
        }

        resizeCanvas();
        initParticles();
        animate();

        window.addEventListener("resize", () => {
            resizeCanvas();
            initParticles();
        });
    }

    /* ─────────────────────────────────────────────
       31. ACTIVE NAV LINK HIGHLIGHT
    ───────────────────────────────────────────── */

    const currentPath = window.location.pathname;
    document.querySelectorAll("nav ul li a").forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });

    /* ─────────────────────────────────────────────
       32. SHAKE KEYFRAME (CSS injection)
    ───────────────────────────────────────────── */

    if (!document.getElementById("dynamic-keyframes")) {
        const style = document.createElement("style");
        style.id    = "dynamic-keyframes";
        style.textContent = `
            @keyframes shake {
                0%,100% { transform: translateX(0); }
                20%      { transform: translateX(-6px); }
                40%      { transform: translateX(6px); }
                60%      { transform: translateX(-4px); }
                80%      { transform: translateX(4px); }
            }
            .spinner-inline {
                display: inline-block;
                width: 14px; height: 14px;
                border: 2px solid rgba(255,255,255,0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 0.7s linear infinite;
                vertical-align: middle;
                margin-right: 6px;
            }
            @keyframes scaleIn {
                from { opacity: 0; transform: scale(0.9); }
                to   { opacity: 1; transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }

    /* ─────────────────────────────────────────────
       33. PASSWORD TOGGLE
    ───────────────────────────────────────────── */

    document.querySelectorAll(".password-field").forEach(field => {
        const toggle = field.parentElement.querySelector(".toggle-password");
        if (!toggle) return;
        toggle.addEventListener("click", () => {
            field.type   = field.type === "password" ? "text" : "password";
            toggle.innerHTML = field.type === "password" ? "Show" : "Hide";
        });
    });

    /* ─────────────────────────────────────────────
       34. AUTO-CLOSE MODAL (click outside)
    ───────────────────────────────────────────── */

    const modal = document.querySelector(".modal");
    if (modal) {
        window.addEventListener("click", e => {
            if (e.target === modal) modal.style.display = "none";
        });
    }

    /* ─────────────────────────────────────────────
       35. MENTOR PROFILE PAGE — Avatar initials
    ───────────────────────────────────────────── */

    document.querySelectorAll(".mentor-avatar[data-name]").forEach(av => {
        const name = av.dataset.name || "?";
        av.textContent = name.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase();
    });

    /* ─────────────────────────────────────────────
       36. CONVERSATION CARD ACTIVE STATE FIX
    ───────────────────────────────────────────── */

    // Ensure li wrapping .active-user also gets styling
    document.querySelectorAll("li.active-user").forEach(li => {
        li.style.background = "rgba(99,102,241,0.12)";
    });

    /* ─────────────────────────────────────────────
       37. IN-APP NOTIFICATIONS
    ───────────────────────────────────────────── */
    if (window.userId) {
        const bell = document.getElementById('notificationBell');
        const dot = document.getElementById('notificationDot');
        const dropdown = document.getElementById('notificationDropdown');
        const notifList = document.getElementById('notificationList');
        
        let unreadCount = 0;
        
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success' && data.notifications.length > 0) {
                    unreadCount = data.notifications.length;
                    if (dot) dot.style.display = 'block';
                    
                    if (notifList) {
                        notifList.innerHTML = '';
                        data.notifications.forEach(n => {
                            notifList.innerHTML += `
                                <div class="notification-item">
                                    <span class="notif-msg">${n.message}</span>
                                    <span class="notif-time">${n.created_at}</span>
                                </div>
                            `;
                        });
                    }
                }
            })
            .catch(err => console.error('Error fetching notifications:', err));
            
        if (bell) {
            bell.addEventListener('click', (e) => {
                e.stopPropagation();
                if (dropdown) dropdown.classList.toggle('show');
                
                if (dropdown && dropdown.classList.contains('show') && unreadCount > 0) {
                    fetch('/api/notifications/read', { method: 'POST' })
                        .then(() => {
                            unreadCount = 0;
                            if (dot) dot.style.display = 'none';
                        })
                        .catch(err => console.error('Error marking notifications read:', err));
                }
            });
        }
        
        window.addEventListener('click', (e) => {
            if (dropdown && dropdown.classList.contains('show') && !e.target.closest('.notification-wrapper')) {
                dropdown.classList.remove('show');
            }
        });
        
        if (typeof io !== 'undefined') {
            const notifSocket = io();
            
            notifSocket.on('new_notification', (data) => {
                unreadCount++;
                if (dot) dot.style.display = 'block';
                
                if (notifList) {
                    const noNotifs = notifList.querySelector('.no-notifications');
                    if (noNotifs) noNotifs.remove();
                    
                    const item = document.createElement('div');
                    item.className = 'notification-item';
                    item.style.animation = 'scaleIn 0.3s ease';
                    item.innerHTML = `
                        <span class="notif-msg">${data.message}</span>
                        <span class="notif-time">${data.created_at}</span>
                    `;
                    notifList.prepend(item);
                }
                
                if (window.showToast) {
                    window.showToast('🔔 ' + data.message);
                }
            });
        }
    }

}); // end DOMContentLoaded