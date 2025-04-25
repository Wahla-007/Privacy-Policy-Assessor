// Remove flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Add transition effect to flash messages
    flashMessages.forEach(message => {
        message.style.transition = 'opacity 0.3s ease';
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Form validation for policy generator
    const policyForm = document.querySelector('.policy-form');
    
    if (policyForm) {
        policyForm.addEventListener('submit', function(event) {
            const websiteName = document.getElementById('website_name').value;
            const websiteUrl = document.getElementById('website_url').value;
            const dataCollected = document.querySelectorAll('input[name="data_collected"]:checked');
            
            let isValid = true;
            
            // Check if website name is provided
            if (!websiteName.trim()) {
                showError('website_name', 'Website name is required');
                isValid = false;
            } else {
                clearError('website_name');
            }
            
            // Check if website URL is provided and valid
            if (!websiteUrl.trim()) {
                showError('website_url', 'Website URL is required');
                isValid = false;
            } else if (!isValidUrl(websiteUrl)) {
                showError('website_url', 'Please enter a valid URL');
                isValid = false;
            } else {
                clearError('website_url');
            }
            
            // Check if at least one data type is selected
            if (dataCollected.length === 0) {
                showError('personal_info', 'Please select at least one type of data collected');
                isValid = false;
            } else {
                clearError('personal_info');
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    }
    
    // Data sale conditional fields
    const dataSaleRadios = document.querySelectorAll('input[name="data_sale"]');
    const doNotSellContainer = document.getElementById('do_not_sell_container');
    
    if (dataSaleRadios.length > 0 && doNotSellContainer) {
        dataSaleRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'yes') {
                    doNotSellContainer.style.display = 'block';
                } else {
                    doNotSellContainer.style.display = 'none';
                }
            });
        });
    }
    
    // Profile form validation
    const profileForm = document.querySelector('.profile-form');
    
    if (profileForm) {
        profileForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password || confirmPassword) {
                if (password !== confirmPassword) {
                    event.preventDefault();
                    showError('confirm_password', 'Passwords do not match');
                } else {
                    clearError('confirm_password');
                }
            }
        });
    }
});

// Helper functions
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    let errorElement = element.nextElementSibling;
    
    // Check if error element already exists
    if (!errorElement || !errorElement.classList.contains('error-message')) {
        errorElement = document.createElement('div');
        errorElement.classList.add('error-message');
        errorElement.style.color = 'var(--danger-color)';
        errorElement.style.fontSize = '0.75rem';
        errorElement.style.marginTop = '0.25rem';
        element.parentNode.insertBefore(errorElement, element.nextSibling);
    }
    
    errorElement.textContent = message;
    element.style.borderColor = 'var(--danger-color)';
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    const errorElement = element.nextElementSibling;
    
    if (errorElement && errorElement.classList.contains('error-message')) {
        errorElement.remove();
    }
    
    element.style.borderColor = 'var(--border-color)';
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch (e) {
        return false;
    }
}

// Add ripple effect styles
const styleElement = document.createElement('style');
styleElement.textContent = `
.btn {
    position: relative;
    overflow: hidden;
}

.ripple {
    position: absolute;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.3);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
    width: 100px;
    height: 100px;
    transform: translate(-50%, -50%);
}

@keyframes ripple {
    0% {
        transform: translate(-50%, -50%) scale(0);
        opacity: 1;
    }
    100% {
        transform: translate(-50%, -50%) scale(3);
        opacity: 0;
    }
}
`;
document.head.appendChild(styleElement);