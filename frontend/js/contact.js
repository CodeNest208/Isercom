
/*
 * contact.js - Contact page specific functionality
 * 
 * Handles:
 * - Main contact form submission
 * - Contact form validation (including email validation)
 * - Auto-fill for authenticated users on contact form
 * - Contact form specific message display
 * - CSRF token handling for contact form
 * 
 * Note: Footer feedback forms are handled in script.js
 */

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

document.addEventListener("DOMContentLoaded", function () {
  console.log("Contact.js loaded");
  const form = document.getElementById("contactForm");
  
  if (!form) {
    console.error("Contact form not found!");
    return;
  }
  
  console.log("Contact form found:", form);

  // Check if user is authenticated and auto-fill form
  checkAuthAndFillForm();

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    console.log("Form submitted");

    // Grab the input values
    const name = document.getElementById('contact_name').value.trim();
    const email = document.getElementById('contact_email').value.trim();
    const subject = document.getElementById('contact_subject').value.trim();
    const message = document.getElementById('contact_message').value.trim();

    console.log("Form data:", { name, email, subject, message });

    // Validate required fields
    if (!name || !email || !subject || !message) {
      console.log("Validation failed - missing fields");
      showMessage('Please fill in all fields.', 'error');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      console.log("Validation failed - invalid email");
      showMessage('Please enter a valid email address.', 'error');
      return;
    }

    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Sending...';
    submitBtn.disabled = true;

    console.log("Sending contact form...");

    // Send data to backend API
    sendContactForm(name, email, subject, message)
      .then(response => {
        console.log("Response received:", response);
        if (response.success) {
          showMessage(response.message, 'success');
          form.reset(); // Clear the form
          // Re-fill user info after reset if user is logged in
          checkAuthAndFillForm();
        } else {
          showMessage(response.message, 'error');
        }
      })
      .catch(error => {
        console.error('Error sending contact form:', error);
        showMessage('Failed to send message. Please try again later.', 'error');
      })
      .finally(() => {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      });
  });
});

async function checkAuthAndFillForm() {
  try {
    console.log("Checking user authentication for auto-fill...");
    const apiUrl = window.location.origin + '/api/auth/check/';
    console.log("Making request to:", apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      credentials: 'include', // Include cookies for authentication
      headers: {
        'Content-Type': 'application/json',
      }
    });

    console.log("Response status:", response.status, "OK:", response.ok);

    if (response.ok) {
      const data = await response.json();
      console.log("Full auth check response:", JSON.stringify(data, null, 2));
      
      if (data.is_authenticated && data.user) {
        console.log("User is authenticated! User data:", data.user);
        
        // User is authenticated, auto-fill the form
        const nameField = document.getElementById('contact_name');
        const emailField = document.getElementById('contact_email');
        
        console.log("Name field found:", !!nameField, "Email field found:", !!emailField);
        
        if (nameField && emailField) {
          // Fill name field - check profile.full_name first, then construct from first/last name
          let fullName = '';
          if (data.user.profile && data.user.profile.full_name) {
            fullName = data.user.profile.full_name;
            console.log("Using profile.full_name:", fullName);
          } else if (data.user.first_name || data.user.last_name) {
            fullName = `${data.user.first_name || ''} ${data.user.last_name || ''}`.trim();
            console.log("Constructed name from first/last:", fullName);
          }
          
          if (fullName) {
            nameField.value = fullName;
            nameField.style.backgroundColor = '#f0f8ff'; // Light blue to indicate auto-filled
            console.log("Name field auto-filled with:", fullName);
          } else {
            console.log("No name data available for auto-fill");
          }
          
          // Fill email field
          if (data.user.email) {
            emailField.value = data.user.email;
            emailField.style.backgroundColor = '#f0f8ff'; // Light blue to indicate auto-filled
            console.log("Email field auto-filled with:", data.user.email);
          } else {
            console.log("No email data available for auto-fill");
          }
          
          // Show notice if any field was filled
          if (fullName || data.user.email) {
            console.log("Showing auto-fill notice");
            showAutoFillNotice();
          }
        } else {
          console.log("Form fields not found!");
        }
      } else {
        console.log("User not authenticated. Response data:", data);
      }
    } else {
      console.log("Auth check response not OK:", response.status);
    }
  } catch (error) {
    console.error("Auth check failed:", error);
    // Don't show error to user as this is expected for non-logged-in users
  }
}

function showAutoFillNotice() {
  // Check if notice already exists
  if (document.querySelector('.auto-fill-notice')) return;
  
  const notice = document.createElement('div');
  notice.className = 'auto-fill-notice';
  notice.innerHTML = '✓ Name and email auto-filled from your account';
  notice.style.cssText = `
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 15px;
    border: 1px solid #bee5eb;
    text-align: center;
  `;
  
  const form = document.getElementById("contactForm");
  if (form) {
    form.insertBefore(notice, form.firstChild);
    
    // Auto-remove notice after 5 seconds
    setTimeout(() => {
      if (notice.parentNode) {
        notice.remove();
      }
    }, 5000);
  }
}

async function sendContactForm(name, email, subject, message) {
  try {
    console.log("Making fetch request to /api/contact/");
    // Use relative path that works from any page
    const apiUrl = window.location.origin + '/api/contact/';
    console.log("Full API URL:", apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify({
        name: name,
        email: email,
        subject: subject,
        message: message
      }),
      credentials: 'same-origin'
    });

    console.log("Fetch response status:", response.status);
    console.log("Fetch response ok:", response.ok);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Parsed response data:", data);
    return data;
  } catch (error) {
    console.error("sendContactForm error:", error);
    throw new Error('Network error: ' + error.message);
  }
}

function showMessage(message, type) {
  console.log("showMessage called:", message, type);
  
  // Remove existing messages
  const existingMessage = document.querySelector('.contact-message');
  if (existingMessage) {
    existingMessage.remove();
  }

  // Create new message element
  const messageDiv = document.createElement('div');
  messageDiv.className = `contact-message ${type}`;
  messageDiv.textContent = message;

  // Style the message
  messageDiv.style.cssText = `
    padding: 15px;
    margin: 20px 0;
    border-radius: 5px;
    font-weight: 500;
    text-align: center;
    position: relative;
    z-index: 9999;
    ${type === 'success' 
      ? 'background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;' 
      : 'background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;'
    }
  `;

  // Insert message after the form
  const form = document.getElementById("contactForm");
  if (form && form.parentNode) {
    form.parentNode.insertBefore(messageDiv, form.nextSibling);
    console.log("Message inserted after form");
  } else {
    // Fallback: append to body
    document.body.appendChild(messageDiv);
    console.log("Message appended to body");
  }

  // Auto-remove success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      if (messageDiv.parentNode) {
        messageDiv.remove();
      }
    }, 5000);
  }
}

