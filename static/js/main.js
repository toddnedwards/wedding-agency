// Mobile Menu Toggle
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

if (hamburger) {
    hamburger.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });
}

// Close mobile menu when a link is clicked
const navLinks = document.querySelectorAll('.nav-menu a');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
    });
});

// Mega menu toggle for touch/mobile interactions
const megaWrappers = document.querySelectorAll('.mega-menu-wrapper');
megaWrappers.forEach(wrapper => {
    const toggle = wrapper.querySelector('.mega-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isOpen = wrapper.classList.contains('open');

        megaWrappers.forEach(item => {
            item.classList.remove('open');
            const itemToggle = item.querySelector('.mega-toggle');
            if (itemToggle) {
                itemToggle.setAttribute('aria-expanded', 'false');
            }
        });

        if (!isOpen) {
            wrapper.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }
    });
});

document.addEventListener('click', (e) => {
    megaWrappers.forEach(wrapper => {
        if (!wrapper.contains(e.target)) {
            wrapper.classList.remove('open');
            const toggle = wrapper.querySelector('.mega-toggle');
            if (toggle) {
                toggle.setAttribute('aria-expanded', 'false');
            }
        }
    });
});

// Form validation
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', (e) => {
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.style.borderColor = 'var(--danger)';
            } else {
                input.style.borderColor = 'var(--border-color)';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Add animation to elements on scroll
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

document.querySelectorAll('.card, section').forEach(element => {
    observer.observe(element);
});

// Close alerts automatically
const alerts = document.querySelectorAll('.alert');
alerts.forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
});