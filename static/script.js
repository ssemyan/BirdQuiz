// Cache DOM element references
const feedbackEl = document.getElementById('feedback');
const imageContainer = document.getElementById('imageContainer');
const optionsContainer = document.getElementById('optionsContainer');
const nextButton = document.getElementById('nextButton');
const setupSection = document.getElementById('setupSection');
const quizSection = document.getElementById('quizSection');
const menuButton = document.getElementById('menuButton');
const errorDiv = document.getElementById('errorMessage');
const csvPathInput = document.getElementById('csvPath');
const correctCountEl = document.getElementById('correctCount');
const incorrectCountEl = document.getElementById('incorrectCount');
const quizTitle = document.getElementById('quizTitle');

let correctCount = 0;
let incorrectCount = 0;
let currentQuestion = null;
let answered = false;
let quizLabel = null;

function loadWashingtonBirds() {
    csvPathInput.value = 'wa_birds.csv';
    quizLabel = 'Washington Birds';
    loadCSV();
}

function loadBackyardBirds() {
    csvPathInput.value = 'backyard_birds.csv';
    quizLabel = 'Common Backyard Birds';
    loadCSV();
}

async function loadCSV() {
    const csvPath = csvPathInput.value.trim();
    
    if (!csvPath) {
        showError('Please enter a CSV file path');
        return;
    }

    showError('');

    try {
        const response = await fetch('/api/load-csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_path: csvPath })
        });

        const data = await response.json();

        if (data.success) {
            correctCount = 0;
            incorrectCount = 0;
            quizTitle.textContent = '🐦 Bird Quiz - ' + (quizLabel || 'Custom');
            quizLabel = null;
            setupSection.style.display = 'none';
            quizSection.style.display = 'block';
            menuButton.classList.add('show');
            nextQuestion();
        } else {
            showError(data.error || 'Failed to load CSV');
        }
    } catch (error) {
        showError('Error loading CSV: ' + error.message);
    }
}

async function nextQuestion() {
    answered = false;
    feedbackEl.className = 'feedback';
    feedbackEl.innerHTML = '';
    nextButton.classList.remove('show');

    // Clear images and show loading text
    imageContainer.innerHTML = '<p>Loading images...</p>';
    
    // Clear options
    optionsContainer.innerHTML = '';

    try {
        const response = await fetch('/api/quiz-question');
        const data = await response.json();

        if (data.success) {
            currentQuestion = data;
            displayQuestion(data);
        } else {
            showError('Error loading question');
        }
    } catch (error) {
        showError('Error: ' + error.message);
    }
}

function displayQuestion(question) {
    // Display images
    imageContainer.innerHTML = '';
    
    if (question.images && question.images.image_urls && question.images.image_urls.length > 0) {
        question.images.image_urls.forEach(imageUrl => {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = question.correct_answer;
            img.onclick = function() {
                openImageModal(imageUrl);
            };
            img.onerror = function() {
                img.style.display = 'none';
            };
            imageContainer.appendChild(img);
        });
        
        if (imageContainer.children.length === 0) {
            imageContainer.innerHTML = '<p class="no-images">Images could not be loaded.</p>';
        }
    } else {
        imageContainer.innerHTML = '<p class="no-images">Images not available.</p>';
    }

    // Display options
    optionsContainer.innerHTML = '';

    question.options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'option-button';
        button.textContent = option;
        button.onclick = () => selectOption(button, option);
        optionsContainer.appendChild(button);
    });
}

function selectOption(button, option) {
    if (answered) return;

    answered = true;

    // Disable all buttons
    document.querySelectorAll('.option-button').forEach(btn => {
        btn.disabled = true;
    });

    // Check answer
    const isCorrect = option.toLowerCase() === currentQuestion.correct_answer.toLowerCase();

    if (isCorrect) {
        correctCount++;
        button.classList.add('correct');
        feedbackEl.className = 'feedback correct';
        feedbackEl.innerHTML = '✓ Correct!';
    } else {
        incorrectCount++;
        button.classList.add('incorrect');
        // Highlight correct answer
        document.querySelectorAll('.option-button').forEach(btn => {
            if (btn.textContent.toLowerCase() === currentQuestion.correct_answer.toLowerCase()) {
                btn.classList.add('correct');
            }
        });
        feedbackEl.className = 'feedback incorrect';
        feedbackEl.innerHTML = `✗ Incorrect! The correct answer is: ${currentQuestion.correct_answer}`;
    }

    correctCountEl.textContent = correctCount;
    incorrectCountEl.textContent = incorrectCount;
    nextButton.classList.add('show');
}

function resetQuiz() {
    setupSection.style.display = 'block';
    quizSection.style.display = 'none';
    csvPathInput.value = 'ebird_world_year_list.csv';
    quizTitle.textContent = '🐦 Bird Identification Quiz';
    menuButton.classList.remove('show');
    closeMenu();
}

function toggleMenu() {
    document.getElementById('menu').classList.toggle('show');
}

function closeMenu() {
    document.getElementById('menu').classList.remove('show');
}

function showError(message) {
    if (message) {
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
    } else {
        errorDiv.classList.remove('show');
    }
}

// Modal functions
function openImageModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    modalImage.src = imageUrl;
    modal.classList.add('show');
}

function closeImageModal() {
    document.getElementById('imageModal').classList.remove('show');
}

// Close modal and menu when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target === modal) {
        closeImageModal();
    }

    const menuBtn = document.getElementById('menuButton');
    const menu = document.getElementById('menu');
    if (event.target !== menuBtn && event.target !== menu && !menu.contains(event.target)) {
        closeMenu();
    }
};
