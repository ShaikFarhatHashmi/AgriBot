/* static/js/auth.js — Authentication Page Interactions */
/**
 * static/js/auth.js — Authentication Page Interactions
 * =====================================================
 * Handles password visibility toggle, mobile menu, and tab switching
 */

/**
 * Toggle password visibility
 * @param {string} inputId - ID of the password input
 * @param {HTMLElement} element - The eye icon element
 */
function togglePwd(inputId, element) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        element.classList.remove("fa-eye");
        element.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        element.classList.remove("fa-eye-slash");
        element.classList.add("fa-eye");
    }
}

/**
 * Toggle mobile menu
 */
function toggleMobileMenu() {
    const leftPanel = document.querySelector('.left-panel');
    const rightPanel = document.querySelector('.right-panel');
    
    if (leftPanel.style.display === 'none' || leftPanel.style.display === '') {
        leftPanel.style.display = 'flex';
        rightPanel.style.display = 'flex';
    } else {
        leftPanel.style.display = 'none';
        rightPanel.style.display = 'none';
    }
}

/**
 * Switch between tabs
 * @param {string} tab - The tab to switch to (signup or login)
 */
function switchTab(tab) {
    const signupTab = document.getElementById('signup-tab');
    const loginTab = document.getElementById('login-tab');
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
    const signupSteps = document.getElementById('signup-steps');
    const loginFeatures = document.getElementById('login-features');
    const brandDescription = document.getElementById('brand-description');
    
    if (tab === 'signup') {
        // Switch to signup
        signupTab.classList.add('active');
        loginTab.classList.remove('active');
        
        signupForm.style.display = 'block';
        loginForm.style.display = 'none';
        
        signupSteps.style.display = 'block';
        loginFeatures.style.display = 'none';
        
        if (brandDescription) {
            brandDescription.textContent = 'Join thousands of farmers getting smarter advice with AI.';
        }
        
        // Update page title
        document.title = 'AgriBot — Sign Up';
        
    } else if (tab === 'login') {
        // Switch to login
        loginTab.classList.add('active');
        signupTab.classList.remove('active');
        
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        
        loginFeatures.style.display = 'block';
        signupSteps.style.display = 'none';
        
        if (brandDescription) {
            brandDescription.textContent = 'Your AI-powered agricultural assistant for smarter, data-driven farming decisions.';
        }
        
        // Update page title
        document.title = 'AgriBot — Login';
    }
    
    // Add animation effect
    const activeForm = tab === 'signup' ? signupForm : loginForm;
    activeForm.style.animation = 'none';
    setTimeout(() => {
        activeForm.style.animation = 'fadeIn 0.4s ease';
    }, 10);
}

/**
 * Preview selected profile photo before upload
 * @param {HTMLInputElement} input - The file input element
 */
function previewPhoto(input) {
    const preview = document.getElementById("photoPreview");
    if (!preview || !input.files || !input.files[0]) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        preview.innerHTML = `<img src="${e.target.result}" alt="Profile Photo">`;
    };
    reader.readAsDataURL(input.files[0]);
}

/* Confirm password match on signup */
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form[action*='signup']");
    if (!form) return;

    form.addEventListener("submit", function (e) {
        const pwd     = document.getElementById("signup-password");
        const confirm = document.getElementById("signup-confirm");
        if (pwd && confirm && pwd.value !== confirm.value) {
            e.preventDefault();
            alert("Passwords do not match. Please check and try again.");
            confirm.focus();
        }
    });
    
    // Add input focus effects
    const inputs = document.querySelectorAll('input[type="email"], input[type="password"], input[type="text"], input[type="tel"]');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            const icon = this.parentElement.querySelector('.icon');
            if (icon) icon.style.color = 'var(--blue-bright)';
        });
        
        input.addEventListener('blur', function() {
            const icon = this.parentElement.querySelector('.icon');
            if (icon) icon.style.color = 'var(--text-muted)';
        });
    });
    
    // Add button hover effects
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Check URL hash for initial tab
    if (window.location.hash === '#login') {
        switchTab('login');
    }
});