
function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
  // Page load animation
  document.querySelectorAll('main, .footer, .footer-top, .footer-content, .footer-bottom')
    .forEach(el => el.classList.add('fade-in'));

  // Scroll-triggered animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, {
    threshold: 0.1
  });

  document.querySelectorAll('.fade-in, .footer, .footer-top, .footer-content, .footer-bottom')
    .forEach(el => observer.observe(el));
});
