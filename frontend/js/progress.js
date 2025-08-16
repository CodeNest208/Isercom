// Progress Bar JavaScript
let currentStep = 1;
const totalSteps = 4;

// Function to set current step (can be called from other files)
function setCurrentStep(step) {
    if (step >= 1 && step <= totalSteps) {
        currentStep = step;
        updateProgressBar();
    }
}

// Initialize progress bar on page load
document.addEventListener('DOMContentLoaded', function() {
    updateProgressBar();
});

// Function to change step
function changeStep(direction) {
    const newStep = currentStep + direction;
    
    if (newStep >= 1 && newStep <= totalSteps) {
        currentStep = newStep;
        updateProgressBar();
    }
}

// Function to go to specific step
function goToStep(step) {
    if (step >= 1 && step <= totalSteps) {
        currentStep = step;
        updateProgressBar();
    }
}

// Function to update progress bar display
function updateProgressBar() {
    // Update progress fill
    const progressFill1 = document.getElementById('progressFill1');
    const progressFill2 = document.getElementById('progressFill2');
    const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
    if (progressFill1) {
        progressFill1.style.width = progressPercentage + '%';
    }
    if (progressFill2) {
        progressFill2.style.width = progressPercentage + '%';
    }
    
    // Update step indicators
    const steps1 = document.querySelectorAll('.step1');
    const steps2 = document.querySelectorAll('.step2');
    const steps = [...steps1, ...steps2];
    steps.forEach((step, index) => {
        const stepNumber = index + 1;
        
        // Remove all classes
        step.classList.remove('active', 'completed');
        
        if (stepNumber < currentStep) {
            step.classList.add('completed');
        } else if (stepNumber === currentStep) {
            step.classList.add('active');
        }
    });
    
    // Update button states
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (prevBtn) {
        prevBtn.disabled = currentStep === 1;
    }
    
    if (nextBtn) {
        if (currentStep === totalSteps) {
            nextBtn.textContent = 'Complete';
            nextBtn.onclick = function() {
                alert('Registration completed!');
            };
        } else {
            nextBtn.textContent = 'Next';
            nextBtn.onclick = function() {
                changeStep(1);
            };
        }
    }
}

// Function to simulate automatic progress (optional)
function autoProgress() {
    const interval = setInterval(() => {
        if (currentStep < totalSteps) {
            changeStep(1);
        } else {
            clearInterval(interval);
        }
    }, 2000); // Progress every 2 seconds
}

// Export functions for external use
window.changeStep = changeStep;
window.goToStep = goToStep;
window.autoProgress = autoProgress;
window.setCurrentStep = setCurrentStep;
window.updateProgressBar = updateProgressBar;
