document.addEventListener('DOMContentLoaded', () => {
  // ======================
  // Page Load Animations
  // ======================
  document.querySelectorAll('main, .footer, .footer-top, .footer-content, .footer-bottom')
    .forEach(el => el.classList.add('fade-in'));

  // Animate footer on page load
  const footer = document.querySelector('.footer');
  if (footer) {
    footer.classList.add('slide-up');
  }

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


  // ======================
  // Hero Carousel
  // ======================
  let slideIndex = 0;
  const slides = document.querySelector(".slides");
  const dots = document.querySelectorAll(".dot");
  const totalSlides = dots.length;

  function showSlide(index) {
    if (index >= totalSlides) slideIndex = 0;
    else if (index < 0) slideIndex = totalSlides - 1;
    else slideIndex = index;

    slides.style.transform = `translateX(-${slideIndex * 100}%)`;

    dots.forEach(dot => dot.classList.remove("active"));
    dots[slideIndex].classList.add("active");
  }

  // Next/Prev buttons
  const nextBtn = document.querySelector(".next");
  const prevBtn = document.querySelector(".prev");

  if (nextBtn && prevBtn) {
    nextBtn.addEventListener("click", () => showSlide(slideIndex + 1));
    prevBtn.addEventListener("click", () => showSlide(slideIndex - 1));
  }

  // Dot navigation
  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      showSlide(parseInt(dot.dataset.index));
    });
  });

  // Auto slide every 5 seconds
  setInterval(() => {
    showSlide(slideIndex + 1);
  }, 5000);

  // Init
  showSlide(0);
});

document.addEventListener("DOMContentLoaded", () => {
  const slides = document.querySelectorAll(".slide");
  const prev = document.querySelector(".prev");
  const next = document.querySelector(".next");
  const dotsContainer = document.querySelector(".dots");

  let slideIndex = 0;
  let timer;

  // Create dots
  slides.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.classList.add("dot");
    if (i === 0) dot.classList.add("active");
    dot.dataset.index = i;
    dotsContainer.appendChild(dot);
  });

  const dots = document.querySelectorAll(".dot");

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.classList.remove("active");
      dots[i].classList.remove("active");
    });

    slideIndex = (index + slides.length) % slides.length;
    slides[slideIndex].classList.add("active");
    dots[slideIndex].classList.add("active");
  }

  function nextSlide() {
    showSlide(slideIndex + 1);
  }

  function prevSlide() {
    showSlide(slideIndex - 1);
  }

  function autoSlide() {
    timer = setInterval(nextSlide, 5000);
  }

  // Event listeners
  next.addEventListener("click", () => {
    nextSlide();
    resetTimer();
  });

  prev.addEventListener("click", () => {
    prevSlide();
    resetTimer();
  });

  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      showSlide(parseInt(dot.dataset.index));
      resetTimer();
    });
  });

  function resetTimer() {
    clearInterval(timer);
    autoSlide();
  }

  // Init
  showSlide(0);
  autoSlide();
});



