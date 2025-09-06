document.addEventListener('DOMContentLoaded', function() {
    const editBtn = document.getElementById('editProfileBtn');
    const cancelBtn = document.getElementById('cancelEditBtn');
    const saveBtn = document.getElementById('saveChangesBtn');
    const editActions = document.getElementById('editActions');

    let isEditing = false;
    let currentUserData = {};

    // Load user profile on page load
    loadUserProfile();

    // Edit profile functionality
    editBtn.addEventListener('click', function() {
        toggleEditMode(true);
    });

    cancelBtn.addEventListener('click', function() {
        toggleEditMode(false);
        // Restore original values
        populateFields(currentUserData);
        const displays = document.querySelectorAll('[id$="Display"]');
        const edits = document.querySelectorAll('[id$="Edit"]');

        displays.forEach(display => {
            display.style.display = 'flex';
        });

        edits.forEach(edit => {
            edit.style.display = 'none';
        });
    });

    saveBtn.addEventListener('click', function() {
        saveProfile();
    });

    function loadUserProfile() {
        // Show loading state
        document.getElementById('userName').textContent = 'Loading...';
        document.getElementById('userEmail').textContent = 'Loading...';
        
        // Get user data from API
        fetch('/api/user/profile/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    // User not authenticated, redirect to login
                    window.location.href = './login.html';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success !== false) {
                currentUserData = data;
                populateFields(data);
            } else {
                throw new Error(data.message || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            showMessage('Error loading profile data: ' + error.message, 'error');
        });
    }

    function populateFields(userData) {
        // Helper function to safely set element content
        function safeSetContent(elementId, content) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = content;
            } else {
                console.warn(`Element with ID '${elementId}' not found`);
            }
        }
        
        // Helper function to safely set element value
        function safeSetValue(elementId, value) {
            const element = document.getElementById(elementId);
            if (element) {
                element.value = value;
            } else {
                console.warn(`Element with ID '${elementId}' not found`);
            }
        }
        
        // Safely get full name
        const firstName = userData.first_name || '';
        const lastName = userData.last_name || '';
        const fullName = (firstName + ' ' + lastName).trim() || 'User';
        
        // Update header info
        safeSetContent('userName', fullName);
        safeSetContent('userEmail', userData.email || '');
        
        // Update display fields
        safeSetContent('fullNameDisplay', fullName !== 'User' ? fullName : 'Not provided');
        safeSetContent('phoneDisplay', userData.phone || 'Not provided');
        
        // Format date of birth
        if (userData.date_of_birth) {
            try {
                const dobDate = new Date(userData.date_of_birth);
                safeSetContent('dobDisplay', dobDate.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                }));
            } catch (e) {
                console.error('Error formatting date:', e);
                safeSetContent('dobDisplay', userData.date_of_birth);
            }
        } else {
            safeSetContent('dobDisplay', 'Not provided');
        }
        
        safeSetContent('addressDisplay', userData.address || 'Not provided');
        
        // Update edit fields
        safeSetValue('fullNameEdit', fullName !== 'User' ? fullName : '');
        safeSetValue('phoneEdit', userData.phone || '');
        safeSetValue('dobEdit', userData.date_of_birth || '');
        safeSetValue('addressEdit', userData.address || '');
    }

    function toggleEditMode(editing) {
        isEditing = editing;
        const displays = document.querySelectorAll('[id$="Display"]');
        const edits = document.querySelectorAll('[id$="Edit"]');

        displays.forEach(display => {
            display.style.display = editing ? 'none' : 'inline';
        });

        edits.forEach(edit => {
            edit.style.display = editing ? 'inline' : 'none';
        });

        editActions.style.display = editing ? 'flex' : 'none';
        editBtn.style.display = editing ? 'none' : 'inline-block';
    }

    function saveProfile() {
        // Get edited values
        const fullName = document.getElementById('fullNameEdit').value.trim();
        const nameParts = fullName.split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';
        
        const formData = {
            first_name: firstName,
            last_name: lastName,
            phone: document.getElementById('phoneEdit').value.trim(),
            date_of_birth: document.getElementById('dobEdit').value,
            address: document.getElementById('addressEdit').value.trim()
        };

        // Validate required fields
        if (!formData.first_name) {
            showMessage('Please fill in your name.', 'error');
            return;
        }

        // Show saving state
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;

        // Send update to API
        fetch('/api/user/profile/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                });
            }

            return response.json();
        })
        .then(data => {
            currentUserData = data;
            populateFields(data);
            toggleEditMode(false);
            showMessage('Profile updated successfully!', 'success');
            const displays = document.querySelectorAll('[id$="Display"]');
            const edits = document.querySelectorAll('[id$="Edit"]');

            displays.forEach(display => {
                display.style.display = 'flex';
            });

            edits.forEach(edit => {
                edit.style.display = 'none';
            });
        })
        .catch(error => {
            console.error('Error saving profile:', error);
            showMessage(error.message || 'Error saving profile. Please try again.', 'error');
        })
        .finally(() => {
            saveBtn.textContent = 'Save Changes';
            saveBtn.disabled = false;
        });

    }

    function showMessage(message, type) {
        // Create or update message element
        let messageElement = document.getElementById('profileMessage');
        if (!messageElement) {
            messageElement = document.createElement('div');
            messageElement.id = 'profileMessage';
            messageElement.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                z-index: 1000;
                font-weight: 500;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
            `;
            document.body.appendChild(messageElement);
        }

        messageElement.textContent = message;
        messageElement.className = type === 'success' ? 'message-success' : 'message-error';
        
        if (type === 'success') {
            messageElement.style.backgroundColor = '#d4edda';
            messageElement.style.color = '#155724';
            messageElement.style.border = '1px solid #c3e6cb';
        } else {
            messageElement.style.backgroundColor = '#f8d7da';
            messageElement.style.color = '#721c24';
            messageElement.style.border = '1px solid #f5c6cb';
        }

        messageElement.style.display = 'block';
        messageElement.style.opacity = '1';

        // Hide message after 5 seconds
        setTimeout(() => {
            messageElement.style.opacity = '0';
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 300);
        }, 5000);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Navigation buttons
    document.getElementById('bookAppointmentBtn').addEventListener('click', function() {
        window.location.href = './appointment_form.html';
    });

    document.getElementById('viewAppointmentsBtn').addEventListener('click', function() {
        window.location.href = './my_appointments.html';
    });
});