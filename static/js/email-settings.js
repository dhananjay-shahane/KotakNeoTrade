/**
 * Email Settings JavaScript
 * Handles email notification toggle switches and persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    loadEmailSettings();
    setupEmailToggleListeners();
});

function loadEmailSettings() {
    fetch('/api/email/get-settings')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const settings = data.settings;
                
                // Update toggle switches based on saved settings
                const signalsToggle = document.getElementById('emailSignalsToggle');
                const dealsToggle = document.getElementById('emailDealsToggle');
                const subscriptionToggle = document.getElementById('emailSubscriptionToggle');
                const sendTimeInput = document.getElementById('emailSendTime');
                const alternativeEmailInput = document.getElementById('alternativeEmail');
                
                if (signalsToggle) {
                    signalsToggle.checked = settings.send_signals_in_mail;
                }
                
                if (dealsToggle) {
                    dealsToggle.checked = settings.send_deals_in_mail;
                }
                
                if (subscriptionToggle) {
                    subscriptionToggle.checked = settings.subscription;
                }
                
                if (sendTimeInput) {
                    sendTimeInput.value = settings.send_time || '09:00';
                }
                
                if (alternativeEmailInput) {
                    alternativeEmailInput.value = settings.alternative_email || '';
                }
                
                console.log('Email settings loaded successfully');
            } else {
                console.error('Failed to load email settings:', data.message);
                showNotification('Failed to load email settings', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading email settings:', error);
            showNotification('Error loading email settings', 'error');
        });
}

function setupEmailToggleListeners() {
    // Trade signals email toggle
    const signalsToggle = document.getElementById('emailSignalsToggle');
    if (signalsToggle) {
        signalsToggle.addEventListener('change', function() {
            updateEmailSetting('send_signals_in_mail', this.checked);
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
            updateEmailSetting('subscription', this.checked);
        });
    }
    
    // Send time input
    const sendTimeInput = document.getElementById('emailSendTime');
    if (sendTimeInput) {
        sendTimeInput.addEventListener('change', function() {
            updateEmailSetting('send_time', this.value);
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
    
    fetch('/api/email/notification-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Email setting updated successfully', 'success');
            console.log(`Updated ${settingName} to ${settingValue}`);
        } else {
            console.error('Failed to update email setting:', data.message);
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
        'send_signals_in_mail': 'emailSignalsToggle',
        'send_deals_in_mail': 'emailDealsToggle',
        'subscription': 'emailSubscriptionToggle'
    };
    
    const toggleId = toggleMap[settingName];
    if (toggleId) {
        const toggle = document.getElementById(toggleId);
        if (toggle) {
            toggle.checked = !toggle.checked; // Revert to previous state
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