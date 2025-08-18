// API Client for isercom_website
class APIClient {
    constructor() {
        this.baseURL = '/api';
        this.csrfToken = null;
        this.initializeCSRF();
    }

    // Initialize CSRF token
    async initializeCSRF() {
        this.csrfToken = await this.getCSRFToken();
        console.log('CSRF token initialized:', this.csrfToken ? 'Present' : 'Missing');
    }

    // Get CSRF token from cookie or API
    async getCSRFToken() {
        // First try to get from cookie
        const cookie = document.cookie
            .split(';')
            .find(row => row.trim().startsWith('csrftoken='));
        
        if (cookie) {
            return cookie.split('=')[1];
        }
        
        // If no cookie, get from API
        try {
            const response = await fetch('/api/csrf-token/', {
                credentials: 'same-origin'
            });
            if (response.ok) {
                const data = await response.json();
                return data.csrfToken;
            }
        } catch (error) {
            console.error('Error getting CSRF token from API:', error);
        }
        
        return null;
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        console.log(`Making API request to: ${url}`);
        
        // Ensure CSRF token is available
        if (!this.csrfToken) {
            this.csrfToken = await this.getCSRFToken();
        }
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken || '',
            },
            credentials: 'same-origin',
        };

        const finalOptions = { ...defaultOptions, ...options };
        console.log('Request options:', finalOptions);
        
        try {
            const response = await fetch(url, finalOptions);
            console.log(`Response status: ${response.status}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`HTTP error! status: ${response.status}, body: ${errorText}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('Response data:', result);
            return result;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Home page data
    async getHomeData() {
        return this.request('/home/');
    }

    // Authentication check
    async checkAuth() {
        return this.request('/auth/check/');
    }

    // Login
    async login(email, password) {
        return this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    // Register
    async register(userData) {
        return this.request('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    // Logout
    async logout() {
        return this.request('/auth/logout/', {
            method: 'POST'
        });
    }

    // Get doctor appointments
    async getDoctorAppointments() {
        try {
            console.log('Calling API endpoint: /api/doctor/appointments/');
            const result = await this.request('/doctor/appointments/');
            console.log('API result received:', result);
            return result;
        } catch (error) {
            console.error('Error fetching doctor appointments:', error);
            return { success: false, appointments: [], error: error.message };
        }
    }
}

// Create global API client instance
window.apiClient = new APIClient();

// Helper functions for common operations
window.showMessage = function(message, type = 'info') {
    // Create or update message display
    let messageDiv = document.getElementById('api-message');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'api-message';
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            max-width: 300px;
            word-wrap: break-word;
        `;
        document.body.appendChild(messageDiv);
    }

    // Set message type styling
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
};

// Auth state management
window.updateAuthUI = function(isAuthenticated, userData = null) {
    // Update navigation or UI elements based on auth state
    const authElements = document.querySelectorAll('[data-auth-required]');
    const guestElements = document.querySelectorAll('[data-guest-only]');

    authElements.forEach(el => {
        el.style.display = isAuthenticated ? 'block' : 'none';
    });

    guestElements.forEach(el => {
        el.style.display = isAuthenticated ? 'none' : 'block';
    });

    // Handle role-based navigation
    if (isAuthenticated && userData) {
        // Check if user is on wrong page for their role
        const currentPath = window.location.pathname;
        
        if (userData.user_type === 'doctor') {
            // Doctor should be on doctor_home page or doctor_appointments page
            if (!currentPath.includes('doctor_home') && !currentPath.includes('doctor_appointments')) {
                // Only redirect if not already on a doctor page
                if (!currentPath.includes('logout')) {
                    window.location.href = '/frontend/pages/doctor_home.html';
                    return;
                }
            }
        } else if (userData.user_type === 'patient') {
            // Patient should be on index page (or other patient pages)
            if (currentPath.includes('doctor_home') || currentPath.includes('doctor_appointments')) {
                // Redirect doctors to patient home
                if (!currentPath.includes('logout')) {
                    window.location.href = '/frontend/index.html';
                    return;
                }
            }
        }
        
        // Update user info display if present
        const userInfoElement = document.getElementById('user-info');
        if (userInfoElement) {
            userInfoElement.textContent = `Welcome, ${userData.profile?.full_name || userData.username}`;
        }
        
        // Add logout link to authenticated nav if needed
        const navLinks = document.getElementById('navLinks');
        if (navLinks && !document.querySelector('[data-auth-required]')) {
            const logoutLink = document.createElement('a');
            logoutLink.href = '/frontend/pages/logout.html';
            logoutLink.className = 'appointment';
            logoutLink.textContent = 'Sign Out';
            logoutLink.setAttribute('data-auth-required', '');
            navLinks.appendChild(logoutLink);
        }
        
        // Update login/logout links based on user role
        const loginLink = document.querySelector('a[href*="login.html"]');
        const logoutLink = document.querySelector('a[href*="logout.html"]');
        
        if (loginLink) {
            if (userData.user_type === 'doctor') {
                loginLink.textContent = 'Doctor Dashboard';
                loginLink.href = '/frontend/pages/doctor_home.html';
            } else {
                loginLink.style.display = 'none';
            }
        }
        
        if (logoutLink) {
            logoutLink.style.display = 'block';
            if (userData.user_type === 'doctor') {
                logoutLink.textContent = 'Sign Out';
            } else {
                logoutLink.textContent = 'Sign Out';
            }
        }
    }
};

// Create global instance
console.log('Creating global API client instance...');
window.apiClient = new APIClient();
console.log('API client created:', window.apiClient);
