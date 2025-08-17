// Global variables
let doctors = [];
let services = [];

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication first - redirect if not authenticated
    const isAuthenticated = await checkAuthenticationAndRedirect();
    if (!isAuthenticated) {
        return; // Stop execution if redirecting
    }
    
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('id_date').setAttribute('min', today);
    
    // Update navigation
    await updateNavigation();
    
    // Load initial data
    await loadDoctors();
    await loadServices();
    
    // Set up form submission
    setupFormSubmission();
});

// Check authentication and redirect if necessary
async function checkAuthenticationAndRedirect() {
    try {
        const authResponse = await window.apiClient.checkAuth();
        
        if (!authResponse.is_authenticated) {
            // User is not authenticated, redirect to login
            showMessage('Please sign in to book an appointment.', 'info');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
            return false;
        }
        
        // Check if user is a patient (only patients should book appointments)
        if (authResponse.user.user_type === 'doctor') {
            showMessage('Doctors cannot book appointments. Redirecting to doctor dashboard.', 'info');
            setTimeout(() => {
                window.location.href = 'doctor_home.html';
            }, 2000);
            return false;
        }
        
        return true; // User is authenticated and is a patient
        
    } catch (error) {
        console.error('Error checking authentication:', error);
        showMessage('Unable to verify authentication. Redirecting to login.', 'error');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return false;
    }
}

// Update navigation based on authentication status
async function updateNavigation() {
    try {
        const authResponse = await window.apiClient.checkAuth();
        const authNav = document.getElementById('authNavigation');
        
        if (authResponse.is_authenticated) {
            authNav.innerHTML = `
                <a href="logout.html" class="appointment">Sign Out</a>
            `;
        } else {
            // This shouldn't happen since we check auth first, but just in case
            authNav.innerHTML = `
                <a href="login.html" class="appointment">Login</a>
            `;
        }
    } catch (error) {
        console.error('Error updating navigation:', error);
        // Default to sign out since user should be authenticated to reach this point
        const authNav = document.getElementById('authNavigation');
        authNav.innerHTML = `
            <a href="logout.html" class="appointment">Sign Out</a>
        `;
    }
}

// Load doctors from the API
async function loadDoctors() {
    try {
        const response = await fetch('/api/doctors/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                doctors = result.data;
                populateDoctorsSelect();
            } else {
                console.error('Failed to load doctors:', result.message);
                loadFallbackDoctors();
            }
        } else {
            console.error('Failed to load doctors');
            loadFallbackDoctors();
        }
    } catch (error) {
        console.error('Error loading doctors:', error);
        loadFallbackDoctors();
    }
}

// Load fallback doctors
function loadFallbackDoctors() {
    doctors = [
        {
            id: 1,
            user: { first_name: 'John', last_name: 'Smith' },
            speciality: 'General Practice'
        },
        {
            id: 2,
            user: { first_name: 'Sarah', last_name: 'Johnson' },
            speciality: 'Gynecology'
        }
    ];
    populateDoctorsSelect();
}

// Populate doctors select dropdown
function populateDoctorsSelect() {
    const doctorSelect = document.getElementById('id_doctor');
    doctorSelect.innerHTML = '<option value="">Choose a doctor...</option>';
    
    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.id;
        option.textContent = `Dr. ${doctor.user.first_name} ${doctor.user.last_name}`;
        if (doctor.speciality) {
            option.textContent += ` - ${doctor.speciality}`;
        }
        doctorSelect.appendChild(option);
    });
}

// Load services from the API
async function loadServices() {
    try {
        const response = await fetch('/api/services/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                services = result.data;
                populateServicesSelect();
            } else {
                console.error('Failed to load services:', result.message);
                loadFallbackServices();
            }
        } else {
            console.error('Failed to load services');
            loadFallbackServices();
        }
    } catch (error) {
        console.error('Error loading services:', error);
        loadFallbackServices();
    }
}

// Load fallback services
function loadFallbackServices() {
    services = [
        { id: 1, name: 'General Consultation', description: 'General health checkup' },
        { id: 2, name: 'Prenatal Care', description: 'Pregnancy care and monitoring' },
        { id: 3, name: 'Gynecological Exam', description: 'Women\'s health examination' },
        { id: 4, name: 'Follow-up Visit', description: 'Follow-up after treatment' }
    ];
    populateServicesSelect();
}

// Populate services select dropdown
function populateServicesSelect() {
    const serviceSelect = document.getElementById('id_service');
    serviceSelect.innerHTML = '<option value="">Choose a service...</option>';
    
    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service.id;
        option.textContent = service.name;
        serviceSelect.appendChild(option);
    });
}

// Set up form submission
function setupFormSubmission() {
    const form = document.getElementById('appointmentForm');
    form.addEventListener('submit', handleFormSubmit);
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Clear previous errors
    clearFormErrors();
    
    // Get form data
    const formData = new FormData(event.target);
    const appointmentData = {
        date: formData.get('date'),
        time: formData.get('time'),
        doctor: formData.get('doctor'),
        service: formData.get('service'),
        notes: formData.get('notes') || ''
    };
    console.log(appointmentData);

    // Validate form data
    if (!validateFormData(appointmentData)) {
        return;
    }

    try {
        // Show loading state
        const submitButton = document.getElementById('sent');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Booking...';
        submitButton.disabled = true;

        // Submit appointment
        const response = await fetch('/api/appointments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': await getCSRFToken()
            },
            body: JSON.stringify(appointmentData)
        });
        
        const result = await response.json();
        console.log(response);
        console.log(result);

        if (response.ok && result.success) {
            // Success
            showMessage(result.message || 'Appointment booked successfully!', 'success');
            
            // Store appointment details for the success page
            const selectedDoctor = doctors.find(d => d.id == appointmentData.doctor);
            const selectedService = services.find(s => s.id == appointmentData.service);
            
            const appointmentSummary = {
                date: appointmentData.date,
                time: appointmentData.time,
                doctorName: selectedDoctor ? `Dr. ${selectedDoctor.user.first_name} ${selectedDoctor.user.last_name}` : null,
                serviceName: selectedService ? selectedService.name : null,
                notes: appointmentData.notes
            };
            
            localStorage.setItem('lastAppointmentBooking', JSON.stringify(appointmentSummary));
            
            // Reset form
            event.target.reset();
            
            // Redirect to success page after a short delay
            setTimeout(() => {
                window.location.href = 'appointment_successful.html';
            }, 2000);
        } else {
            // Error
            if (result.errors) {
                displayFormErrors(result.errors);
            } else {
                showMessage(result.message || 'Failed to book appointment. Please try again.', 'error');
            }
        }

        // Restore button
        submitButton.textContent = originalText;
        submitButton.disabled = false;

    } catch (error) {
        console.error('Error submitting appointment:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
        
        // Restore button
        const submitButton = document.getElementById('sent');
        submitButton.textContent = 'Book Appointment';
        submitButton.disabled = false;
    }
}

// Validate form data
function validateFormData(data) {
    const errors = [];

    if (!data.date) {
        errors.push('Please select a date');
    } else {
        const selectedDate = new Date(data.date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate < today) {
            errors.push('Please select a future date');
        }
    }

    if (!data.time) {
        errors.push('Please select a time');
    }

    if (!data.doctor) {
        errors.push('Please select a doctor');
    }

    if (!data.service) {
        errors.push('Please select a service');
    }

    if (errors.length > 0) {
        displayFormErrors({ general: errors });
        return false;
    }

    return true;
}

// Display form errors
function displayFormErrors(errors) {
    const errorContainer = document.getElementById('formErrors');
    errorContainer.innerHTML = '';

    Object.keys(errors).forEach(field => {
        errors[field].forEach(error => {
            const errorElement = document.createElement('p');
            errorElement.style.color = '#d32f2f';
            errorElement.style.fontSize = '14px';
            errorElement.style.margin = '5px 0';
            errorElement.textContent = error;
            errorContainer.appendChild(errorElement);
        });
    });

    errorContainer.style.display = 'block';
}

// Clear form errors
function clearFormErrors() {
    const errorContainer = document.getElementById('formErrors');
    errorContainer.innerHTML = '';
    errorContainer.style.display = 'none';
}

// Show message
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('messageContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
        background: ${type === 'error' ? '#f8d7da' : type === 'success' ? '#d4edda' : '#d1ecf1'};
        color: ${type === 'error' ? '#721c24' : type === 'success' ? '#155724' : '#0c5460'};
        padding: 12px 20px;
        margin-bottom: 10px;
        border-radius: 5px;
        border: 1px solid ${type === 'error' ? '#f5c6cb' : type === 'success' ? '#c3e6cb' : '#bee5eb'};
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        max-width: 300px;
    `;
    
    messageDiv.innerHTML = `
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 18px; cursor: pointer; margin-left: 10px;">&times;</button>
        ${message}
    `;
    
    messageContainer.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Get CSRF token
async function getCSRFToken() {
    try {
        const response = await fetch('/api/csrf-token/');
        const data = await response.json();
        return data.csrfToken;
    } catch (error) {
        console.error('Error getting CSRF token:', error);
        return '';
    }
}