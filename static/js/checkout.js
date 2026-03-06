/**
 * Checkout Form Validation and Payment Method Handling
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('checkoutForm');
    const paymentMethods = document.querySelectorAll('input[name="payment_method"]');
    const upiDetails = document.getElementById('upiDetails');
    const cardDetails = document.getElementById('cardDetails');
    const contactInput = document.getElementById('contact');
    const pincodeInput = document.getElementById('pincode');
    const cardNumberInput = document.getElementById('card_number');
    const expiryInput = document.getElementById('expiry');
    const cvvInput = document.getElementById('cvv');
    const upiIdInput = document.getElementById('upi_id');

    // Payment method toggle
    paymentMethods.forEach(radio => {
        radio.addEventListener('change', function() {
            upiDetails.style.display = 'none';
            cardDetails.style.display = 'none';
            
            // Clear required attributes
            upiIdInput.removeAttribute('required');
            cardNumberInput.removeAttribute('required');
            expiryInput.removeAttribute('required');
            cvvInput.removeAttribute('required');

            if (this.value === 'upi') {
                upiDetails.style.display = 'block';
                upiIdInput.setAttribute('required', 'required');
            } else if (this.value === 'card') {
                cardDetails.style.display = 'block';
                cardNumberInput.setAttribute('required', 'required');
                expiryInput.setAttribute('required', 'required');
                cvvInput.setAttribute('required', 'required');
            }
        });
    });

    // Phone number validation (only digits, max 10)
    if (contactInput) {
        contactInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });
    }

    // Pincode validation (only digits, max 6)
    if (pincodeInput) {
        pincodeInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
        });
    }

    // Card number formatting
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 16) {
                this.value = this.value.slice(0, 16);
            }
        });
    }

    // Expiry formatting (MM/YY)
    if (expiryInput) {
        expiryInput.addEventListener('input', function() {
            let value = this.value.replace(/[^0-9]/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            this.value = value;
        });
    }

    // CVV validation (only digits, max 3)
    if (cvvInput) {
        cvvInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 3) {
                this.value = this.value.slice(0, 3);
            }
        });
    }

    // Form validation
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();

            // Check if form is valid
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }

            // Additional custom validation
            const selectedPayment = document.querySelector('input[name="payment_method"]:checked').value;
            
            if (selectedPayment === 'upi') {
                const upiPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$/;
                if (!upiPattern.test(upiIdInput.value)) {
                    upiIdInput.setCustomValidity('Please enter a valid UPI ID (e.g., name@paytm)');
                    upiIdInput.reportValidity();
                    form.classList.add('was-validated');
                    return;
                }
            }

            if (selectedPayment === 'card') {
                if (cardNumberInput.value.length !== 16) {
                    cardNumberInput.setCustomValidity('Card number must be 16 digits');
                    cardNumberInput.reportValidity();
                    form.classList.add('was-validated');
                    return;
                }
                if (expiryInput.value.length !== 5) {
                    expiryInput.setCustomValidity('Please enter expiry in MM/YY format');
                    expiryInput.reportValidity();
                    form.classList.add('was-validated');
                    return;
                }
                if (cvvInput.value.length !== 3) {
                    cvvInput.setCustomValidity('CVV must be 3 digits');
                    cvvInput.reportValidity();
                    form.classList.add('was-validated');
                    return;
                }
            }

            // Show loading spinner
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Placing Order...';

            // Submit form
            form.submit();
        });
    }
});
