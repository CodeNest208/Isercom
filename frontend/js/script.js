/*
 * script.js - Global site functionality
 * 
 * Handles:
 * - Navigation (hamburger menu, sticky navbar)
 * - Footer feedback forms (across all pages)
 * - Appointment button authentication checks
 * - General message system
 * - Back to top functionality
 * 
 * Note: Main contact form functionality is handled in contact.js
 */

// Hamburger toggle for responsive menu
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

// State variables for services menu in mobile
let isServicesMenuActive = false;
let originalNavContent = '';

hamburger.addEventListener('click', () => {
  if (isServicesMenuActive) {
    // If services menu is active, restore original nav content
    restoreOriginalNav();
  } else {
    // Normal hamburger toggle
    navLinks.classList.toggle('active');
  }
});

// Function to store original nav content
function storeOriginalNav() {
  if (!originalNavContent) {
    originalNavContent = navLinks.innerHTML;
  }
}

// Function to restore original nav content
function restoreOriginalNav() {
  navLinks.innerHTML = originalNavContent;
  isServicesMenuActive = false;
  navLinks.classList.add('active');
  // Re-initialize services dropdown after restoring content
  initializeServicesDropdown();
}

// Function to show services menu in mobile
function showServicesMenu() {
  const servicesMenuHTML = `
    <div class="services-menu-header">
      <button class="back-to-main-menu" onclick="restoreOriginalNav()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
        Back
      </button>
      <span>Services</span>
    </div>
    <div class="services-menu-content">
      <a href="/frontend/pages/gynaecology.html">Obstetrics and Gynaecological Services</a>
      <a href="/frontend/pages/consultation.html">Consultation & Specialised Clinics</a>
      <a href="/frontend/pages/Antenatal.html">Antenatal Care</a>
      <a href="/frontend/pages/fertility.html">Fertility/IVF</a>
    </div>
  `;
  
  navLinks.innerHTML = servicesMenuHTML;
  isServicesMenuActive = true;
  navLinks.classList.add('active');
}

// Sticky navbar functionality
window.addEventListener('scroll', () => {
  const topBar = document.querySelector('.top-bar');
  const navbar = document.querySelector('.navbar');
  const body = document.body;
  const scrollPosition = window.scrollY;

  if (scrollPosition > 50) {
    // Hide top-bar and make navbar stick to top
    topBar.classList.add('hidden');
    navbar.classList.add('scrolled');
    body.classList.add('scrolled');
  } else {
    // Show top-bar and return navbar to normal position
    topBar.classList.remove('hidden');
    navbar.classList.remove('scrolled');
    body.classList.remove('scrolled');
  }
});

// Back to top button functionality
function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

// Optional: close menu when link is clicked (on mobile)
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      navLinks.classList.remove('active');
    }
  });
});
// Footer feedback form submission handler
document.addEventListener("DOMContentLoaded", function () {
  console.log('Script.js: DOM loaded, setting up footer forms...');
  
  // Handle all footer feedback forms
  const footerForms = document.querySelectorAll('form.feedback-form');
  console.log('Found footer forms:', footerForms.length);
  
  footerForms.forEach((footerForm, index) => {
    console.log(`Setting up footer form ${index + 1}`);
    
    footerForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      console.log('Footer form submitted');
      
      const nameInput = footerForm.querySelector('input[name="name"], input[placeholder*="Name"]');
      const emailInput = footerForm.querySelector('input[name="email"], input[placeholder*="Email"]');
      const messageInput = footerForm.querySelector('textarea[name="message"], textarea[placeholder*="Message"]');
      
      if (!nameInput || !emailInput || !messageInput) {
        showMessage('Form elements not found. Please refresh the page.', 'error');
        return;
      }
      
      const name = nameInput.value.trim();
      const email = emailInput.value.trim();
      const message = messageInput.value.trim();
      
      if (!name || !email || !message) {
        showMessage('Please fill in all fields.', 'error');
        return;
      }
      
      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showMessage('Please enter a valid email address.', 'error');
        return;
      }
      
      const submitButton = footerForm.querySelector('button[type="submit"]');
      const originalText = submitButton ? submitButton.textContent : 'Submit';
      
      try {
        if (submitButton) {
          submitButton.disabled = true;
          submitButton.textContent = 'Sending...';
        }
        
        const response = await fetch('/api/contact/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({
            name: name,
            email: email,
            subject: 'Footer Feedback',
            message: message
          }),
          credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
          showMessage('Thank you for your feedback! We\'ll get back to you soon.', 'success');
          footerForm.reset();
          // Re-auto-fill after reset
          setTimeout(() => autoFillUserInfo(), 100);
        } else {
          throw new Error(result.error || 'Failed to send message');
        }
      } catch (error) {
        console.error('Error sending feedback:', error);
        showMessage('Failed to send feedback. Please try again later.', 'error');
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  });
  
  // Auto-fill user info for footer forms after a short delay to ensure forms are ready
  setTimeout(() => {
    console.log('Auto-filling footer forms...');
    autoFillUserInfo();
  }, 500);
});

// CSRF token helper function
function getCsrfToken() {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  
  if (cookieValue) {
    return cookieValue;
  }
  
  // Fallback: try to get from meta tag
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  if (metaToken) {
    return metaToken.getAttribute('content');
  }
  
  // Fallback: try to get from form input
  const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (inputToken) {
    return inputToken.value;
  }
  
  return '';
}

// Auto-fill footer forms for authenticated users
async function autoFillUserInfo() {
  try {
    const response = await fetch('/api/auth/check/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin'
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.is_authenticated && data.user) {
        console.log('User authenticated, auto-filling footer forms:', data.user);
        
        // Auto-fill footer feedback forms only (not main contact forms)
        const footerForms = document.querySelectorAll('form.feedback-form');
        console.log('Found footer forms:', footerForms.length);
        
        footerForms.forEach((form, index) => {
          console.log(`Processing footer form ${index + 1}`);
          
          const nameInput = form.querySelector('input[name="name"], input[placeholder*="Name"]');
          const emailInput = form.querySelector('input[name="email"], input[placeholder*="Email"]');
          
          console.log('Name input found:', !!nameInput, 'Email input found:', !!emailInput);
          
          if (nameInput && !nameInput.value) {
            const userName = data.user.full_name || 
                           (data.user.first_name && data.user.last_name ? 
                            `${data.user.first_name} ${data.user.last_name}`.trim() : 
                            data.user.first_name || data.user.last_name || '');
            
            if (userName) {
              nameInput.value = userName;
              nameInput.style.backgroundColor = '#f0f8ff'; // Light blue to indicate auto-filled
              console.log('Auto-filled name:', userName);
            }
          }
          
          if (emailInput && !emailInput.value && data.user.email) {
            emailInput.value = data.user.email;
            emailInput.style.backgroundColor = '#f0f8ff'; // Light blue to indicate auto-filled
            console.log('Auto-filled email:', data.user.email);
          }
          
          // Show auto-fill notice if any field was filled
          if ((nameInput && nameInput.value) || (emailInput && emailInput.value)) {
            showFooterAutoFillNotice(form);
          }
        });
      } else {
        console.log('User not authenticated');
      }
    } else {
      console.log('Auth check failed:', response.status);
    }
  } catch (error) {
    console.error('Error auto-filling footer forms:', error);
  }
}

// Show auto-fill notice for footer forms
function showFooterAutoFillNotice(form) {
  // Check if notice already exists for this form
  if (form.querySelector('.footer-auto-fill-notice')) return;
  
  const notice = document.createElement('div');
  notice.className = 'footer-auto-fill-notice';
  notice.innerHTML = '✓ Auto-filled from your account';
  notice.style.cssText = `
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 6px 10px;
    border-radius: 3px;
    font-size: 12px;
    margin-bottom: 10px;
    border: 1px solid #bee5eb;
    text-align: center;
    font-weight: 500;
  `;
  
  // Insert notice before the textarea
  const textarea = form.querySelector('textarea');
  if (textarea) {
    form.insertBefore(notice, textarea);
    
    // Auto-remove notice after 4 seconds
    setTimeout(() => {
      if (notice.parentNode) {
        notice.remove();
      }
    }, 4000);
  }
}

function talkToDoctor() {
  alert("Redirecting to consultation...");
  // window.location.href = 'contact.html'; // Optional redirection
}

// Modal Dialog Functions
function closeMessageModal() {
  const modal = document.getElementById('messageModal');
  if (modal) {
    modal.classList.add('fade-out');
    setTimeout(() => {
      modal.style.display = 'none';
      modal.remove();
    }, 300);
  }
}

// Auto-show modal when page loads (if messages exist)
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('messageModal');
  if (modal) {
    // Modal is already visible by default
    
    // Optional: Auto-close modal after 8 seconds
    setTimeout(() => {
      closeMessageModal();
    }, 8000);
  }
});

// Close modal when clicking outside of it
document.addEventListener('click', function(event) {
  const modal = document.getElementById('messageModal');
  const modalContent = document.querySelector('.message-modal');
  
  if (modal && event.target === modal && !modalContent.contains(event.target)) {
    closeMessageModal();
  }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    closeMessageModal();
  }
});

// Appointment button authentication check
function handleAppointmentClick(event) {
  event.preventDefault();
  checkAuthAndRedirect();
}

// Check authentication and redirect appropriately
async function checkAuthAndRedirect() {
  try {
    let authResponse;
    if (window.apiClient && typeof window.apiClient.checkAuth === 'function') {
      authResponse = await window.apiClient.checkAuth();
    } else {
      const response = await fetch('/api/auth/check/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
      });
      if (response.ok) {
        authResponse = await response.json();
      } else {
        throw new Error('Authentication check failed');
      }
    }

    if (authResponse && authResponse.is_authenticated) {
      if (authResponse.user && authResponse.user.user_type === 'doctor') {
        showMessage('Doctors cannot book appointments. Redirecting to doctor dashboard...', 'info');
        setTimeout(() => {
          window.location.href = '/frontend/pages/doctor_home.html';
        }, 2000);
      } else {
        window.location.href = '/frontend/pages/appointment_form.html';
      }
    } else {
      window.location.href = '/frontend/pages/login.html';
    }
  } catch (error) {
    console.error('Error checking authentication:', error);
    showMessage('Unable to verify authentication. Redirecting to login...', 'error');
    setTimeout(() => {
      window.location.href = '/frontend/pages/login.html';
    }, 2000);
  }
}

// Initialize appointment button handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Find all appointment buttons and add click handlers
  const appointmentButtons = document.querySelectorAll('a[href*="appointment_form.html"], a.appointment[href*="appointment"]');
  
  appointmentButtons.forEach(button => {
    // Only handle buttons that lead to appointment form
    const href = button.getAttribute('href');
    if (href && href.includes('appointment_form.html')) {
      button.addEventListener('click', handleAppointmentClick);
    }
  });
});

// Helper function to show messages (reuse existing if available)
function showMessage(message, type = 'info') {
  // Try to use existing message system if available
  if (typeof window.showMessage === 'function') {
    window.showMessage(message, type);
    return;
  }
  
  // Fallback: create simple message display
  const messageContainer = document.getElementById('messageContainer') || createMessageContainer();
  
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
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
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

// Create message container if it doesn't exist
function createMessageContainer() {
  let container = document.getElementById('messageContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'messageContainer';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
    document.body.appendChild(container);
  }
  return container;
}
  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (messageDiv.parentNode) {
      messageDiv.remove();
    }
  }, 5000);


// Create message container if it doesn't exist
function createMessageContainer() {
  let container = document.getElementById('messageContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'messageContainer';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
    document.body.appendChild(container);
  }
  return container;
}

const servicesLink = document.getElementById('services-link');
const servicesDropdown = document.getElementById('services-dropdown');

// Initialize services dropdown functionality
function initializeServicesDropdown() {
  const servicesLink = document.getElementById('services-link');
  const servicesDropdown = document.getElementById('services-dropdown');
  
  if (servicesLink && servicesDropdown) {
    servicesLink.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Check if we're in mobile view
      if (window.innerWidth <= 768) {
        // Store original content and show services menu
        storeOriginalNav();
        showServicesMenu();
      } else {
        // Desktop behavior - toggle dropdown
        servicesDropdown.style.display = servicesDropdown.style.display === 'block' ? 'none' : 'block';
      }
    });
    
    // Desktop click outside to close dropdown
    document.addEventListener('click', function(event) {
      if (window.innerWidth > 768 && servicesLink && servicesDropdown) {
        if (!servicesLink.contains(event.target) && !servicesDropdown.contains(event.target)) {
          servicesDropdown.style.display = 'none';
        }
      }
    });
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  storeOriginalNav();
  initializeServicesDropdown();
});

// Make functions available globally
window.restoreOriginalNav = restoreOriginalNav;
window.showServicesMenu = showServicesMenu;
