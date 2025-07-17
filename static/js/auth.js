// Authentication page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Setup broker card selection
    setupBrokerCardSelection();
    
    // Setup form enhancements
    setupFormEnhancements();
});

function setupBrokerCardSelection() {
    const brokerCards = document.querySelectorAll('.broker-card');
    
    brokerCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove active class from all cards
            brokerCards.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked card
            this.classList.add('active');
            
            // Get broker type
            const brokerType = this.dataset.broker;
            
            // Update form based on broker selection
            updateFormForBroker(brokerType);
            
            // Store selected broker
            localStorage.setItem('selectedBroker', brokerType);
        });
    });
    
    // Load previously selected broker
    const savedBroker = localStorage.getItem('selectedBroker');
    if (savedBroker) {
        const savedCard = document.querySelector(`[data-broker="${savedBroker}"]`);
        if (savedCard) {
            brokerCards.forEach(c => c.classList.remove('active'));
            savedCard.classList.add('active');
            updateFormForBroker(savedBroker);
        }
    }
}

function updateFormForBroker(brokerType) {
    const authCard = document.querySelector('.auth-card');
    if (!authCard) return;
    
    // Update form header based on broker
    const authHeader = authCard.querySelector('.auth-header h4');
    if (authHeader) {
        switch(brokerType) {
            case 'kotak':
                authHeader.innerHTML = '<i class="fas fa-shield-alt me-2"></i>Kotak Neo Login';
                break;
            case 'upstox':
                authHeader.innerHTML = '<i class="fas fa-chart-line me-2"></i>Upstox Login';
                break;
            case 'angel':
                authHeader.innerHTML = '<i class="fas fa-wings me-2"></i>Angel One Login';
                break;
            case 'zerodha':
                authHeader.innerHTML = '<i class="fas fa-bolt me-2"></i>Zerodha Login';
                break;
        }
    }
    
    // Update form action or add broker-specific logic
    const form = authCard.querySelector('form');
    if (form) {
        // Add broker type as hidden input
        let brokerInput = form.querySelector('input[name="broker_type"]');
        if (!brokerInput) {
            brokerInput = document.createElement('input');
            brokerInput.type = 'hidden';
            brokerInput.name = 'broker_type';
            form.appendChild(brokerInput);
        }
        brokerInput.value = brokerType;
    }
}

function setupFormEnhancements() {
    // Enhanced form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Signing In...';
                
                // Re-enable button after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });
    
    // Enhanced password toggle
    const passwordToggles = document.querySelectorAll('.password-toggle-btn');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
    
    // Real-time form validation
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateInput(this);
            }
        });
    });
}

function validateInput(input) {
    const value = input.value.trim();
    
    // Remove existing validation classes
    input.classList.remove('is-valid', 'is-invalid');
    
    // Basic validation
    if (input.hasAttribute('required') && !value) {
        input.classList.add('is-invalid');
        return false;
    }
    
    // Email validation
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            input.classList.add('is-invalid');
            return false;
        }
    }
    
    // Password validation
    if (input.type === 'password' && value && value.length < 6) {
        input.classList.add('is-invalid');
        return false;
    }
    
    // If all validations pass
    if (value) {
        input.classList.add('is-valid');
    }
    
    return true;
}

// Add smooth scrolling for broker cards
function smoothScrollToCard(direction) {
    const container = document.querySelector('.broker-cards-container');
    if (!container) return;
    
    const scrollAmount = container.clientWidth * 0.8;
    const currentScroll = container.scrollLeft;
    
    if (direction === 'left') {
        container.scrollTo({
            left: currentScroll - scrollAmount,
            behavior: 'smooth'
        });
    } else {
        container.scrollTo({
            left: currentScroll + scrollAmount,
            behavior: 'smooth'
        });
    }
}

// Add keyboard navigation for broker cards
document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const activeCard = document.querySelector('.broker-card.active');
        if (!activeCard) return;
        
        const cards = Array.from(document.querySelectorAll('.broker-card'));
        const currentIndex = cards.indexOf(activeCard);
        
        let newIndex;
        if (e.key === 'ArrowLeft') {
            newIndex = currentIndex > 0 ? currentIndex - 1 : cards.length - 1;
        } else {
            newIndex = currentIndex < cards.length - 1 ? currentIndex + 1 : 0;
        }
        
        cards[newIndex].click();
        cards[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});