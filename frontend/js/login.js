document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous errors
        document.getElementById('emailError').textContent = '';
        document.getElementById('passwordError').textContent = '';
        
        // Get form data
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        // Disable submit button
        const submitBtn = loginForm.querySelector('.login-btn');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Signing in...';
        submitBtn.disabled = true;
        
        try {
            const response = await window.apiClient.login(email, password);
            
            if (response.success) {
                // Show role-specific success message
                const userType = response.user?.user_type || 'user';
                let message = 'Login successful! Redirecting...';
                
                if (userType === 'doctor') {
                    message = 'Welcome Doctor! Redirecting to your dashboard...';
                } else if (userType === 'patient') {
                    message = 'Welcome! Redirecting to homepage...';
                }
                
                window.showMessage(message, 'success');
                
                // Use the redirect URL from the backend response
                setTimeout(() => {
                    window.location.href = response.redirect_url || '/frontend/index.html';
                }, 1500);
            } else {
                // Display field-specific errors
                if (response.errors) {
                    if (response.errors.email) {
                        document.getElementById('emailError').textContent = response.errors.email.join(', ');
                    }
                    if (response.errors.password) {
                        document.getElementById('passwordError').textContent = response.errors.password.join(', ');
                    }
                    if (response.errors.non_field_errors) {
                        window.showMessage(response.errors.non_field_errors.join(', '), 'error');
                    }
                } else {
                    window.showMessage(response.message || 'Login failed', 'error');
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            window.showMessage('Network error. Please try again.', 'error');
        } finally {
            // Re-enable submit button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
});