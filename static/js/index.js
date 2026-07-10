// ── Slideshow ──────────────────────────────────────────────
// Add your image paths here. Use as many as you like.
const SLIDE_IMAGES = [
  '/static/img/gallery1.jpg',
  '/static/img/gallery2.jpg',
  '/static/img/gallery3.jpg',
  '/static/img/gallery4.jpg',
  '/static/img/gallery5.jpg',
  '/static/img/gallery6.jpg',
  '/static/img/gallery7.jpg',
  '/static/img/gallery8.jpg',
  '/static/img/gallery9.jpg',
  '/static/img/gallery10.jpg',
  '/static/img/gallery11.jpg',
  '/static/img/gallery12.jpg',
  '/static/img/gallery13.jpg',
  '/static/img/gallery14.jpg',
  '/static/img/gallery15.jpg',
  '/static/img/gallery16.jpg',
];

const SLIDE_DURATION = 8000; // ms — must match animation duration in CSS

function slideshow() {
    
  const container = document.querySelector('.main_page');
  let current = 0;
  console.log(container)

  function showSlide(index) {
    const old = container.querySelector('.done');
    if (old) old.remove();

    const prev = container.querySelector('.slide');
    if (prev) prev.classList.add('done');

    const slide = document.createElement('div');
    slide.className = 'slide';
    slide.style.backgroundImage = `url('${SLIDE_IMAGES[index]}')`;
    container.prepend(slide);
  }

  showSlide(current);
  setInterval(() => {
    current = (current + 1) % SLIDE_IMAGES.length;
    showSlide(current);
  }, SLIDE_DURATION);
}

window.addEventListener('load', slideshow)

// ── Countdown ──────────────────────────────────────────────
setInterval(update, 1000)

function update() {
    seconds = parseInt(document.getElementById("second_count").textContent) - 1
    minutes = parseInt(document.getElementById("minute_count").textContent)
    hours = parseInt(document.getElementById("hour_count").textContent)
    days = parseInt(document.getElementById("day_count").textContent)

    if (seconds < 0) {
        minutes -= 1
        seconds = 59
    }

    if (minutes < 0) {
        hours -= 1
        minutes = 59
    }

    if (hours < 0) {
        days -= 1
        hours = 23
    }
    
    document.getElementById("second_count").textContent = seconds
    document.getElementById("minute_count").textContent = minutes
    document.getElementById("hour_count").textContent = hours
    document.getElementById("day_count").textContent = days
}