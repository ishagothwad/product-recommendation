/**
 * ShopSmart - Global app utilities
 * Toast notifications, add-to-cart, cart count
 */

document.addEventListener('DOMContentLoaded', function () {
    initCartCount();
    initAddToCart();
    initSettingsModal();
    initSearchForms();
    initAuthGuards();
    initAuthForms();
});

function isAuthenticated() {
    return document.body && document.body.dataset && document.body.dataset.authenticated === '1';
}

function initAuthGuards() {
    // Any element with data-require-auth will trigger sign-in for guests
    document.addEventListener('click', function (e) {
        const gated = e.target.closest('[data-require-auth]');
        if (!gated) return;
        if (isAuthenticated()) return;

        e.preventDefault();
        if (typeof showToast === 'function') {
            showToast('Please sign in to continue', 'danger');
        }

        const modalEl = document.getElementById('signinModal');
        if (modalEl && window.bootstrap && typeof bootstrap.Modal === 'function') {
            new bootstrap.Modal(modalEl).show();
        }
    });
}

function initCartCount() {
    const cartBadge = document.getElementById('cart-count');
    if (!cartBadge) return;
    
    const cartData = cartBadge.getAttribute('data-cart-data');
    if (cartData) {
        try {
            const cart = JSON.parse(cartData);
            const totalQty = Object.values(cart).reduce((sum, item) => sum + (item.quantity || 1), 0);
            updateCartCount(totalQty);
        } catch (e) {
            // If parsing fails, keep the initial value
        }
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;
    toast.setAttribute('role', 'alert');
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-info-circle';
    toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateCartCount(count) {
    const el = document.getElementById('cart-count');
    if (el) {
        el.textContent = count || 0;
        el.style.display = (count && count > 0) ? 'inline' : 'none';
    }
}

function initAddToCart() {
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.add-to-cart');
        if (!btn || btn.disabled) return;

        const id = btn.dataset.id;
        const name = btn.dataset.name;
        const brand = btn.dataset.brand || '';
        const price = btn.dataset.price || '0';
        const image = btn.dataset.image || '';

        fetch('/add_to_cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, name, brand, price, image })
        })
        .then(res => res.json())
        .then(data => {
            updateCartCount(data.cart_count);
            showToast('Added to cart!');
            btn.classList.add('added');
            btn.disabled = true;
            const icon = btn.querySelector('i');
            if (icon) icon.className = 'fas fa-check me-1';
        })
        .catch(() => showToast('Could not add to cart', 'danger'));
    });
}

function initSettingsModal() {
    const settingsModal = document.getElementById('settingsModal');
    if (!settingsModal) return;

    const applyBtn = document.getElementById('applyTheme');
    if (applyBtn) {
        applyBtn.addEventListener('click', function () {
            const theme = document.querySelector('input[name="theme"]:checked')?.value || 'default';
            document.body.style.backgroundColor = theme === 'black' ? '#111' : theme === 'green' ? '#065f46' : '#f9fafb';
            document.body.style.color = theme !== 'default' ? 'white' : '#111827';
            bootstrap.Modal.getInstance(settingsModal)?.hide();
        });
    }

    ['zoomIn', 'zoomOut'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', () => {
                document.body.style.zoom = id === 'zoomIn' ? '115%' : '100%';
            });
        }
    });
}

function showLoadingSpinner() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoadingSpinner() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

function initSearchForms() {
    document.querySelectorAll('form[action*="recommendations"], form[action*="reccom"]').forEach(form => {
        form.addEventListener('submit', function() {
            showLoadingSpinner();
        });
    });
}

function initAuthForms() {
    // Set return URL when modals open
    const signinModal = document.getElementById('signinModal');
    const signupModal = document.getElementById('signupModal');
    
    if (signinModal) {
        signinModal.addEventListener('show.bs.modal', function() {
            const returnUrl = window.location.pathname === '/checkout' ? '/checkout' : window.location.pathname;
            document.getElementById('signinReturnUrl').value = returnUrl;
        });
    }
    
    if (signupModal) {
        signupModal.addEventListener('show.bs.modal', function() {
            const returnUrl = window.location.pathname === '/checkout' ? '/checkout' : window.location.pathname;
            document.getElementById('signupReturnUrl').value = returnUrl;
        });
    }

    // Handle sign-in form submission
    const signinForm = document.getElementById('signinForm');
    if (signinForm) {
        signinForm.addEventListener('submit', function(e) {
            // Validate form before submission
            if (!this.checkValidity()) {
                e.preventDefault();
                this.classList.add('was-validated');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = submitBtn.querySelector('.spinner-border');
            const errorDiv = document.getElementById('signinError');
            
            if (spinner) spinner.classList.remove('d-none');
            submitBtn.disabled = true;
            if (errorDiv) {
                errorDiv.classList.add('d-none');
                errorDiv.textContent = '';
            }
            
            // Let form submit normally - browser will handle redirect
            // No need to preventDefault() - form will submit and redirect naturally
        });
    }

    // Handle sign-up form submission
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            // Validate form before submission
            if (!this.checkValidity()) {
                e.preventDefault();
                this.classList.add('was-validated');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = submitBtn.querySelector('.spinner-border');
            if (spinner) spinner.classList.remove('d-none');
            submitBtn.disabled = true;
            
            // Let form submit normally - browser will handle redirect
            // No need to preventDefault() - form will submit and redirect naturally
        });
    }
}

// Initialize auth forms
document.addEventListener('DOMContentLoaded', function() {
    initAuthForms();
});
