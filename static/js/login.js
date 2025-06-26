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