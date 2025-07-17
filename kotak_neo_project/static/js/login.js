document.addEventListener("DOMContentLoaded", function () {
            // TOTP input formatting
            var totpInput = document.getElementById("totp");
            var mpinInput = document.getElementById("mpin");

            // Auto-format TOTP input
            totpInput.addEventListener("input", function (e) {
                var value = e.target.value.replace(/\D/g, "");
                if (value.length > 6) value = value.substr(0, 6);
                e.target.value = value;
            });

            // Auto-format mobile number input
            var mobileInput = document.getElementById("mobile_number");
            mobileInput.addEventListener("input", function (e) {
                var value = e.target.value.replace(/\D/g, "");
                if (value.length > 10) value = value.substr(0, 10);
                e.target.value = value;
            });

            // Auto-format MPIN input (6 digits)
            mpinInput.addEventListener("input", function (e) {
                var value = e.target.value.replace(/\D/g, "");
                if (value.length > 6) value = value.substr(0, 6);
                e.target.value = value;

                // Auto-focus to TOTP when MPIN is complete
                if (value.length === 6) {
                    totpInput.focus();
                }
            });

            // Form submission loading state
            var form = document.getElementById("totpForm");
            form.addEventListener("submit", function (e) {
                var submitBtn = document.getElementById("totpSubmit");
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="btn-spinner me-2"></span>Authenticating...';
            });

            // Auto-focus first input
            document.getElementById("mobile_number").focus();
        });
// UCC Validation
document.addEventListener('DOMContentLoaded', function() {
    const uccInput = document.getElementById('ucc');
    const totpForm = document.getElementById('totpForm');
    
    if (uccInput) {
        // Convert UCC to uppercase as user types
        uccInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^A-Za-z0-9]/g, ''); // Remove non-alphanumeric
            e.target.value = value.toUpperCase();
            
            // Validate UCC length and format
            if (value.length < 5 || value.length > 6) {
                e.target.setCustomValidity('UCC must be 5-6 alphanumeric characters');
            } else {
                e.target.setCustomValidity('');
            }
        });
    }
    
    // Form validation before submission
    if (totpForm) {
        totpForm.addEventListener('submit', function(e) {
            const ucc = document.getElementById('ucc').value;
            const mobileNumber = document.getElementById('mobile_number').value;
            const totp = document.getElementById('totp').value;
            const mpin = document.getElementById('mpin').value;
            
            // Validate UCC
            if (!ucc || ucc.length < 5 || ucc.length > 6 || !/^[A-Za-z0-9]+$/.test(ucc)) {
                alert('Please enter a valid UCC (5-6 alphanumeric characters)');
                e.preventDefault();
                return false;
            }
            
            // Validate mobile number
            if (!mobileNumber || mobileNumber.length !== 10 || !/^\d+$/.test(mobileNumber)) {
                alert('Please enter a valid 10-digit mobile number');
                e.preventDefault();
                return false;
            }
            
            // Validate TOTP
            if (!totp || totp.length !== 6 || !/^\d+$/.test(totp)) {
                alert('Please enter a valid 6-digit TOTP code from your authenticator app');
                document.getElementById('totp').focus();
                e.preventDefault();
                return false;
            }
            
            // Validate MPIN
            if (!mpin || mpin.length !== 6 || !/^\d+$/.test(mpin)) {
                alert('Please enter a valid 6-digit MPIN');
                e.preventDefault();
                return false;
            }
            
            return true;
        });
    }
});
