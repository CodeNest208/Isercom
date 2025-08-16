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


