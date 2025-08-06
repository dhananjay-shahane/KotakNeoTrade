/**
 * Email Settings JavaScript
 * Handles email notification toggle switches and persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    loadEmailSettings();
    setupEmailToggleListeners();
});

function loadEmailSettings() {
    fetch('/api/email-settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;
                
                // Update toggle switch based on saved settings
                const emailNotificationToggle = document.getElementById('emailNotificationToggle');
                
                if (emailNotificationToggle) {
                    emailNotificationToggle.checked = settings.email_notification || false;
                }
                
                if (settings.user_email) {
                    const userEmailInput = document.getElementById('userEmail');
                    if (userEmailInput) {
                        userEmailInput.value = settings.user_email;
                    }
                }
                
                console.log('Email settings loaded successfully');
            } else {
                console.error('Failed to load email settings:', data.error);
                showNotification('Failed to load email settings', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading email settings:', error);
            showNotification('Error loading email settings', 'error');
        });
}

function setupEmailToggleListeners() {
    // Trade signals email toggle (using same setting as deals for now)
    const signalsToggle = document.getElementById('emailSignalsToggle');
    if (signalsToggle) {
        signalsToggle.addEventListener('change', function() {
            updateEmailSetting('send_deals_in_mail', this.checked);
        });
    }
    
    // Deal notifications email toggle
    const dealsToggle = document.getElementById('emailDealsToggle');
    if (dealsToggle) {
        dealsToggle.addEventListener('change', function() {
            updateEmailSetting('send_deals_in_mail', this.checked);
        });
    }
    
    // Daily subscription email toggle
    const subscriptionToggle = document.getElementById('emailSubscriptionToggle');
    if (subscriptionToggle) {
        subscriptionToggle.addEventListener('change', function() {
            updateEmailSetting('send_daily_change_data', this.checked);
        });
    }
    
    // Send time input
    const sendTimeInput = document.getElementById('emailSendTime');
    if (sendTimeInput) {
        sendTimeInput.addEventListener('change', function() {
            updateEmailSetting('daily_email_time', this.value);
        });
    }
    
    // Alternative email input
    const alternativeEmailInput = document.getElementById('alternativeEmail');
    if (alternativeEmailInput) {
        alternativeEmailInput.addEventListener('blur', function() {
            updateEmailSetting('alternative_email', this.value);
        });
    }
}

function updateEmailSetting(settingName, settingValue) {
    const data = {};
    data[settingName] = settingValue;
    
    fetch('/api/email-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Email setting updated successfully', 'success');
            console.log(`Updated ${settingName} to ${settingValue}`);
        } else {
            console.error('Failed to update email setting:', data.error);
            showNotification('Failed to update email setting', 'error');
            // Revert the toggle if update failed
            revertToggle(settingName);
        }
    })
    .catch(error => {
        console.error('Error updating email setting:', error);
        showNotification('Error updating email setting', 'error');
        // Revert the toggle if update failed
        revertToggle(settingName);
    });
}

function revertToggle(settingName) {
    // Revert the toggle state if the server update failed
    const toggleMap = {
        'send_deals_in_mail': ['emailSignalsToggle', 'emailDealsToggle'],
        'send_daily_change_data': 'emailSubscriptionToggle',
        'daily_email_time': 'emailSendTime',
        'alternative_email': 'alternativeEmail'
    };
    
    const toggleIds = toggleMap[settingName];
    if (toggleIds) {
        if (Array.isArray(toggleIds)) {
            // Handle multiple toggles for the same setting
            toggleIds.forEach(toggleId => {
                const toggle = document.getElementById(toggleId);
                if (toggle && toggle.type === 'checkbox') {
                    toggle.checked = !toggle.checked; // Revert to previous state
                }
            });
        } else {
            // Handle single toggle
            const toggle = document.getElementById(toggleIds);
            if (toggle) {
                if (toggle.type === 'checkbox') {
                    toggle.checked = !toggle.checked; // Revert to previous state
                } else {
                    // For input fields, we would need to store previous value
                    console.log('Cannot revert non-checkbox input');
                }
            }
        }
    }
}

function showNotification(message, type = 'info') {
    // Check if SweetAlert2 is available
    if (typeof Swal !== 'undefined') {
        const icon = type === 'success' ? 'success' : type === 'error' ? 'error' : 'info';
        Swal.fire({
            title: type.charAt(0).toUpperCase() + type.slice(1),
            text: message,
            icon: icon,
            timer: 3000,
            showConfirmButton: false,
            toast: true,
            position: 'top-end'
        });
    } else {
        // Fallback to alert
        alert(message);
    }
}

// Export functions for use in other scripts
window.emailSettings = {
    loadEmailSettings,
    updateEmailSetting
};