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
// Contact form submission handler
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contactForm");

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Grab the input values
    const name = form.querySelector('input[placeholder="Name"]').value.trim();
    const email = form.querySelector('input[placeholder="Email"]').value.trim();
    const subject = form.querySelector('input[placeholder="Subject"]').value.trim();
    const message = form.querySelector('textarea').value.trim();

    // Basic validation
    if (!name || !email || !subject || !message) {
      alert("Please fill in all fields.");
      return;
    }

    // Simulate sending form (you can replace this with a real request)
    alert(`Thanks ${name}! Your message has been submitted successfully.`);

    // Optionally clear the form
    form.reset();
  });
});
// Contact form submission handler
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contactForm");

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Grab the input values
    const name = form.querySelector('input[placeholder="Name"]').value.trim();
    const email = form.querySelector('input[placeholder="Email"]').value.trim();
    const subject = form.querySelector('input[placeholder="Subject"]').value.trim();
    const message = form.querySelector('textarea').value.trim();

    // Basic validation
    if (!name || !email || !subject || !message) {
      alert("Please fill in all fields.");
      return;
    }

    // Simulate sending form (you can replace this with a real request)
    alert(`Thanks ${name}! Your message has been submitted successfully.`);

    // Optionally clear the form
    form.reset();
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
if (servicesLink && servicesDropdown) {
  servicesLink.addEventListener('click', function(e) {
    e.preventDefault();
    servicesDropdown.style.display = servicesDropdown.style.display === 'block' ? 'none' : 'block';
  });
  document.addEventListener('click', function(event) {
    if (!servicesLink.contains(event.target) && !servicesDropdown.contains(event.target)) {
      servicesDropdown.style.display = 'none';
    }
  });
}
