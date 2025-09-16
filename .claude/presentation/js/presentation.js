/**
 * AI-Agent Development Presentation
 * Interactive JavaScript Features
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize all features
    initNavigation();
    initProgressBar();
    initKeyboardShortcuts();
    initScrollEffects();
    initPresentationMode();
    initAnimations();
    initInteractiveElements();
    initMobileMenu();
    
});

/**
 * Navigation Enhancement
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    // Update active state based on current page
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath.split('/').pop() || 
            (currentPath.endsWith('/') && link.getAttribute('href') === 'index.html')) {
            link.classList.add('active');
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Progress Bar Updates
 */
function initProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    
    // Update progress on scroll
    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        
        // Only update page scroll progress if not in presentation mode
        if (!document.body.classList.contains('presentation-mode')) {
            const baseProgress = parseFloat(progressBar.style.width) || 0;
            const scrollProgress = Math.min(baseProgress + (scrolled * 0.1), 100);
            // Keep the base progress, add small scroll indicator
        }
    });
}

/**
 * Keyboard Shortcuts
 */
function initKeyboardShortcuts() {
    const pages = [
        'index.html',
        'story.html',
        'paradigm-shift.html',
        'methodology.html',
        'implementation.html',
        'platform-architecture.html',
        'portfolio-impact.html',
        'call-to-action.html'
    ];
    
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const currentIndex = pages.indexOf(currentPage);
    
    document.addEventListener('keydown', (e) => {
        // Arrow key navigation
        if (e.key === 'ArrowRight' && currentIndex < pages.length - 1) {
            window.location.href = pages[currentIndex + 1];
        } else if (e.key === 'ArrowLeft' && currentIndex > 0) {
            window.location.href = pages[currentIndex - 1];
        }
        
        // F key for fullscreen
        if (e.key === 'f' || e.key === 'F') {
            toggleFullscreen();
        }
        
        // P key for presentation mode
        if (e.key === 'p' || e.key === 'P') {
            togglePresentationMode();
        }
        
        // Escape to exit presentation mode
        if (e.key === 'Escape') {
            exitPresentationMode();
        }
        
        // Number keys for quick navigation
        if (e.key >= '1' && e.key <= '8') {
            const pageIndex = parseInt(e.key) - 1;
            if (pageIndex < pages.length) {
                window.location.href = pages[pageIndex];
            }
        }
    });
}

/**
 * Scroll Effects
 */
function initScrollEffects() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all major sections
    document.querySelectorAll('section').forEach(section => {
        observer.observe(section);
    });
    
    // Parallax effect for hero sections
    const heroSections = document.querySelectorAll('.hero, .page-header');
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        heroSections.forEach(hero => {
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    });
}

/**
 * Presentation Mode
 */
function initPresentationMode() {
    // Create presentation mode UI
    const presentationControls = document.createElement('div');
    presentationControls.className = 'presentation-controls';
    presentationControls.innerHTML = `
        <button class="present-btn" onclick="togglePresentationMode()">
            <i data-lucide="maximize"></i>
            <span>Present</span>
        </button>
        <div class="presentation-nav" style="display: none;">
            <button onclick="previousSlide()"><i data-lucide="chevron-left"></i></button>
            <span class="slide-counter">1 / 8</span>
            <button onclick="nextSlide()"><i data-lucide="chevron-right"></i></button>
            <button onclick="exitPresentationMode()"><i data-lucide="x"></i></button>
        </div>
    `;
    document.body.appendChild(presentationControls);
}

function togglePresentationMode() {
    document.body.classList.toggle('presentation-mode');
    const controls = document.querySelector('.presentation-controls');
    const presentBtn = controls.querySelector('.present-btn');
    const navControls = controls.querySelector('.presentation-nav');
    
    if (document.body.classList.contains('presentation-mode')) {
        presentBtn.style.display = 'none';
        navControls.style.display = 'flex';
        enterFullscreen();
        updateSlideCounter();
    } else {
        presentBtn.style.display = 'flex';
        navControls.style.display = 'none';
        exitFullscreen();
    }
}

function exitPresentationMode() {
    document.body.classList.remove('presentation-mode');
    const controls = document.querySelector('.presentation-controls');
    controls.querySelector('.present-btn').style.display = 'flex';
    controls.querySelector('.presentation-nav').style.display = 'none';
    exitFullscreen();
}

function updateSlideCounter() {
    const pages = [
        'index.html',
        'story.html',
        'paradigm-shift.html',
        'methodology.html',
        'implementation.html',
        'platform-architecture.html',
        'portfolio-impact.html',
        'call-to-action.html'
    ];
    
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const currentIndex = pages.indexOf(currentPage) + 1;
    
    const counter = document.querySelector('.slide-counter');
    if (counter) {
        counter.textContent = `${currentIndex} / ${pages.length}`;
    }
}

function nextSlide() {
    const pages = [
        'index.html',
        'story.html',
        'paradigm-shift.html',
        'methodology.html',
        'implementation.html',
        'platform-architecture.html',
        'portfolio-impact.html',
        'call-to-action.html'
    ];
    
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const currentIndex = pages.indexOf(currentPage);
    
    if (currentIndex < pages.length - 1) {
        window.location.href = pages[currentIndex + 1];
    }
}

function previousSlide() {
    const pages = [
        'index.html',
        'story.html',
        'paradigm-shift.html',
        'methodology.html',
        'implementation.html',
        'platform-architecture.html',
        'portfolio-impact.html',
        'call-to-action.html'
    ];
    
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const currentIndex = pages.indexOf(currentPage);
    
    if (currentIndex > 0) {
        window.location.href = pages[currentIndex - 1];
    }
}

/**
 * Fullscreen Utilities
 */
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        enterFullscreen();
    } else {
        exitFullscreen();
    }
}

function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}

function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
}

/**
 * Animations
 */
function initAnimations() {
    // Animate counters
    const counters = document.querySelectorAll('.stat-number, .metric-value');
    counters.forEach(counter => {
        const updateCount = () => {
            const target = parseInt(counter.innerText.replace(/[^0-9]/g, ''));
            if (!isNaN(target)) {
                const increment = target / 100;
                let current = 0;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        counter.innerText = counter.innerText;
                        clearInterval(timer);
                    } else {
                        const prefix = counter.innerText.match(/^[^0-9]*/)[0];
                        const suffix = counter.innerText.match(/[^0-9]*$/)[0];
                        counter.innerText = prefix + Math.floor(current) + suffix;
                    }
                }, 20);
            }
        };
        
        // Trigger animation when element comes into view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCount();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
    
    // Typing effect for terminal output
    const terminalOutputs = document.querySelectorAll('.terminal-line');
    terminalOutputs.forEach((line, index) => {
        line.style.opacity = '0';
        setTimeout(() => {
            line.style.opacity = '1';
            line.style.animation = 'fadeIn 0.3s ease-in';
        }, index * 200);
    });
}

/**
 * Interactive Elements
 */
function initInteractiveElements() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.story-card, .agent-card, .feature-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Interactive timeline
    const timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach(item => {
        item.addEventListener('click', function() {
            this.classList.toggle('expanded');
        });
    });
    
    // Copy code blocks on click
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        block.addEventListener('click', function() {
            const text = this.innerText;
            navigator.clipboard.writeText(text).then(() => {
                // Show copied notification
                const notification = document.createElement('div');
                notification.className = 'copy-notification';
                notification.innerText = 'Copied!';
                this.parentNode.appendChild(notification);
                
                setTimeout(() => {
                    notification.remove();
                }, 2000);
            });
        });
    });
}

/**
 * Mobile Menu
 */
function initMobileMenu() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
}

/**
 * Additional Styles for Presentation Mode
 */
const presentationStyles = document.createElement('style');
presentationStyles.innerHTML = `
    .presentation-controls {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 10000;
    }
    
    .present-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        box-shadow: var(--shadow-lg);
    }
    
    .presentation-nav {
        display: flex;
        align-items: center;
        gap: 16px;
        background: rgba(0, 0, 0, 0.8);
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
    }
    
    .presentation-nav button {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 8px;
    }
    
    .slide-counter {
        font-weight: 600;
        margin: 0 12px;
    }
    
    .presentation-mode {
        overflow: hidden;
    }
    
    .presentation-mode .main-nav {
        display: none;
    }
    
    .presentation-mode .progress-container {
        top: 0;
    }
    
    .presentation-mode section {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .copy-notification {
        position: absolute;
        top: 10px;
        right: 10px;
        background: var(--success-color);
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
        animation: fadeIn 0.3s;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(presentationStyles);

/**
 * Print Functionality
 */
window.addEventListener('beforeprint', () => {
    document.body.classList.add('print-mode');
});

window.addEventListener('afterprint', () => {
    document.body.classList.remove('print-mode');
});

// Export functions for global use
window.togglePresentationMode = togglePresentationMode;
window.exitPresentationMode = exitPresentationMode;
window.nextSlide = nextSlide;
window.previousSlide = previousSlide;