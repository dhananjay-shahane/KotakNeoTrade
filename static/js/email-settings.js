/**
 * Email Settings JavaScript
 * Handles email notification toggle switch and persistence using external_users table
 */

document.addEventListener('DOMContentLoaded', function() {
    loadEmailSettings();
    setupEmailToggleListeners();
});

function loadEmailSettings() {
    console.log('🔄 Loading email notification settings...');
    
    fetch('/api/check-email-notification-status', {
        method: 'GET',
        credentials: 'same-origin',  // Include session cookies
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(response => {
            if (response.status === 401) {
                console.warn('❌ User not authenticated for email settings');
                setDefaultEmailSettings();
                return { success: false, authenticated: false, error: 'Not authenticated' };
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.authenticated) {
                const status = data.status;
                
                // Update toggle switch based on saved settings from database
                const emailNotificationToggle = document.getElementById('emailNotificationToggle');
                
                if (emailNotificationToggle) {
                    // Explicitly set the boolean value
                    const isEnabled = Boolean(status.email_notification);
                    emailNotificationToggle.checked = isEnabled;
                    console.log('✅ Email notification toggle loaded from database:', isEnabled);
                }
                
                // Update email field if available
                if (status.user_email) {
                    const userEmailInput = document.getElementById('userEmail');
                    if (userEmailInput) {
                        userEmailInput.value = status.user_email;
                    }
                }
                
                console.log('✅ Email settings loaded successfully from database:', status);
            } else {
                if (data.authenticated === false) {
                    console.warn('❌ Authentication required for email settings');
                } else {
                    console.error('❌ Failed to load email settings:', data.error);
                }
                setDefaultEmailSettings();
            }
        })
        .catch(error => {
            console.error('❌ Error loading email settings:', error);
            setDefaultEmailSettings();
        });
}

function setDefaultEmailSettings() {
    // Set safe defaults when settings cannot be loaded
    const emailNotificationToggle = document.getElementById('emailNotificationToggle');
    if (emailNotificationToggle) {
        emailNotificationToggle.checked = false; // Default to off for safety
        console.log('Set default email notification toggle to: false');
    }
}

function setupEmailToggleListeners() {
    const saveButton = document.getElementById('saveEmailSettings');
    const emailNotificationToggle = document.getElementById('emailNotificationToggle');
    
    if (saveButton) {
        saveButton.addEventListener('click', saveEmailSettings);
    }
    
    // Auto-save when toggle changes
    if (emailNotificationToggle) {
        emailNotificationToggle.addEventListener('change', function() {
            console.log('Email notification toggle changed:', this.checked);
            saveEmailSettings();
        });
    }
}

function saveEmailSettings() {
    const emailNotificationToggle = document.getElementById('emailNotificationToggle');
    
    if (!emailNotificationToggle) {
        console.error('❌ Email notification toggle not found');
        return;
    }
    
    // Get the explicit boolean value
    const isEnabled = Boolean(emailNotificationToggle.checked);
    
    const settings = {
        email_notification: isEnabled
    };
    
    console.log('💾 Saving email notification status:', isEnabled);
    
    fetch('/api/update-email-notification-status', {
        method: 'POST',
        credentials: 'same-origin',  // Include session cookies
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        if (response.status === 401) {
            console.warn('❌ User not authenticated for saving email settings');
            showAlert('Please login to save email settings', 'warning');
            return { success: false, authenticated: false, error: 'Not authenticated' };
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('✅ Email notification status saved to database:', data.status.email_notification);
            showAlert('Email notification setting saved successfully', 'success');
        } else {
            if (data.authenticated === false) {
                console.warn('❌ Authentication required for saving email settings');
                showAlert('Please login to save email settings', 'warning');
            } else {
                console.error('❌ Failed to save email settings:', data.error);
                showAlert('Failed to save email settings: ' + data.error, 'error');
            }
        }
    })
    .catch(error => {
        console.error('❌ Error saving email settings:', error);
        showAlert('Error saving email settings', 'error');
    });
}

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}