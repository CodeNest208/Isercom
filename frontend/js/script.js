// Hamburger toggle for responsive menu
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('active');
});

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
  // Initialize footer form functionality
  initializeFooterForm();
  
  // Auto-fill footer form if user is authenticated
  const footerForm = document.querySelector('footer form, .footer form, #footerForm');
  if (footerForm) {
    checkAuthAndFillFooterForm(footerForm);
  }
  
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

// Footer form email functionality
function initializeFooterForm() {
  const footerForm = document.querySelector('footer form, .footer form, #footerForm');
  
  if (footerForm) {
    console.log("Footer form found, initializing email functionality");
    
    footerForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleFooterFormSubmission(footerForm);
    });
  } else {
    console.log("No footer form found");
  }
}

async function handleFooterFormSubmission(form) {
  try {
    console.log("Footer form submitted");
    
    // Get form fields - adapt these selectors based on your footer form structure
    const nameField = form.querySelector('input[name="name"], input[placeholder*="name" i], input[placeholder*="Name"], #footer_name');
    const emailField = form.querySelector('input[name="email"], input[type="email"], input[placeholder*="email" i], #footer_email');
    const messageField = form.querySelector('textarea, input[name="message"], input[placeholder*="message" i], #footer_message');
    const subjectField = form.querySelector('input[name="subject"], input[placeholder*="subject" i], #footer_subject');
    
    // Extract values
    const name = nameField ? nameField.value.trim() : '';
    const email = emailField ? emailField.value.trim() : '';
    const message = messageField ? messageField.value.trim() : '';
    const subject = subjectField ? subjectField.value.trim() : 'Footer Contact Form Submission';
    
    console.log("Footer form data:", { name, email, subject, message });
    
    // Validate required fields
    if (!email || !message) {
      showMessage('Please fill in at least your email and message.', 'error');
      return;
    }
    
    // If no name provided, use email as fallback
    const finalName = name || email.split('@')[0] || 'Website Visitor';
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"], button, input[type="submit"]');
    let originalText = 'Submit';
    if (submitBtn) {
      originalText = submitBtn.textContent || submitBtn.value || 'Submit';
      if (submitBtn.textContent) {
        submitBtn.textContent = 'Sending...';
      } else if (submitBtn.value) {
        submitBtn.value = 'Sending...';
      }
      submitBtn.disabled = true;
    }
    
    console.log("Sending footer form data...");
    
    // Send to the same contact API
    const response = await sendFooterFormData(finalName, email, subject, message);
    
    if (response.success) {
      showMessage('Thank you for your message! We will get back to you soon.', 'success');
      form.reset();
      
      // Check if user is authenticated and auto-fill email again
      await checkAuthAndFillFooterForm(form);
    } else {
      showMessage(response.message || 'Failed to send message. Please try again.', 'error');
    }
    
  } catch (error) {
    console.error('Footer form submission error:', error);
    showMessage('Failed to send message. Please try again later.', 'error');
  } finally {
    // Reset button state
    const submitBtn = form.querySelector('button[type="submit"], button, input[type="submit"]');
    if (submitBtn) {
      if (submitBtn.textContent && submitBtn.textContent === 'Sending...') {
        submitBtn.textContent = originalText;
      } else if (submitBtn.value && submitBtn.value === 'Sending...') {
        submitBtn.value = originalText;
      }
      submitBtn.disabled = false;
    }
  }
}

async function sendFooterFormData(name, email, subject, message) {
  try {
    const apiUrl = window.location.origin + '/api/contact/';
    console.log("Sending footer form to API:", apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        name: name,
        email: email,
        subject: subject,
        message: message
      })
    });
    
    console.log("Footer form API response status:", response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log("Footer form API response data:", data);
    return data;
    
  } catch (error) {
    console.error("Footer form API error:", error);
    throw new Error('Network error: ' + error.message);
  }
}

async function checkAuthAndFillFooterForm(form) {
  try {
    console.log("Checking authentication for footer form auto-fill...");
    
    const response = await fetch('/api/auth/check/', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      
      if (data.is_authenticated && data.user) {
        console.log("Auto-filling footer form for authenticated user");
        
        const nameField = form.querySelector('input[name="name"], input[placeholder*="name" i], #footer_name');
        const emailField = form.querySelector('input[name="email"], input[type="email"], input[placeholder*="email" i], #footer_email');
        
        if (nameField || emailField) {
          // Fill name field
          let fullName = '';
          if (data.user.profile && data.user.profile.full_name) {
            fullName = data.user.profile.full_name;
          } else if (data.user.first_name || data.user.last_name) {
            fullName = `${data.user.first_name || ''} ${data.user.last_name || ''}`.trim();
          }
          
          if (fullName && nameField) {
            nameField.value = fullName;
            nameField.style.backgroundColor = '#f0f8ff';
          }
          
          // Fill email field
          if (data.user.email && emailField) {
            emailField.value = data.user.email;
            emailField.style.backgroundColor = '#f0f8ff';
          }
          
          console.log("Footer form auto-filled with user data");
        }
      }
    }
  } catch (error) {
    console.log("Footer form auth check failed:", error.message);
  }
}


