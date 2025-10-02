// AI Learning Platform - JavaScript Functionality
// PromptPal Frontend Starter Code

// DOM Elements
const navbar = document.querySelector('.navbar');
const navLinks = document.querySelectorAll('.nav-link');
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeTabs();
    initializeAnimations();
    initializeChatbot();
});

// Navigation Functions
function initializeNavigation() {
    // Handle scroll effects
    window.addEventListener('scroll', handleScroll);
    
    // Handle navigation clicks
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavClick);
    });
    
    // Handle hamburger menu
    if (hamburger) {
        hamburger.addEventListener('click', toggleMobileMenu);
    }
}

function handleScroll() {
    const scrollTop = window.pageYOffset;
    
    // Navbar background opacity
    if (scrollTop > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
    }
    
    // Update active nav link based on scroll position
    updateActiveNavLink();
}

function handleNavClick(e) {
    e.preventDefault();
    const targetId = e.target.getAttribute('href');
    const targetSection = document.querySelector(targetId);
    
    if (targetSection) {
        // Smooth scroll to section
        targetSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
        
        // Update active state
        navLinks.forEach(link => link.classList.remove('active'));
        e.target.classList.add('active');
    }
}

function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const scrollPos = window.scrollY + 100;
    
    sections.forEach(section => {
        const top = section.offsetTop;
        const height = section.offsetHeight;
        const id = section.getAttribute('id');
        
        if (scrollPos >= top && scrollPos < top + height) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${id}`) {
                    link.classList.add('active');
                }
            });
        }
    });
}

function toggleMobileMenu() {
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Tab System
function initializeTabs() {
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// Animation Functions
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.feature-card, .course-card, .resource-card');
    animatedElements.forEach(el => observer.observe(el));
}

// Quick question function
function askQuickQuestion(question) {
    const chatInput = document.getElementById('chat-input');
    chatInput.value = question;
    sendMessage();
}

// Copy to clipboard function
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Prompt copied to clipboard!', 'success');
        
        // Update button text temporarily
        const copyBtn = document.querySelector('.copy-btn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        copyBtn.style.background = '#10b981';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
        
    }).catch(function() {
        showNotification('Failed to copy to clipboard', 'error');
    });
}

// Enhanced generatePrompt function
function generatePrompt() {
    const input = document.getElementById('prompt-input').value.trim();
    const output = document.getElementById('generated-prompt');
    const copyBtn = document.querySelector('.copy-btn');
    
    if (!input) {
        showNotification('Please enter an idea first!', 'warning');
        return;
    }
    
    // Show loading state
    output.innerHTML = '<span class="loading"></span> Generating enhanced prompt...';
    copyBtn.style.display = 'none';
    
    // Simulate AI prompt generation
    setTimeout(() => {
        const enhancedPrompt = generateEnhancedPrompt(input);
        output.innerHTML = enhancedPrompt;
        copyBtn.style.display = 'inline-flex';
        showNotification('Enhanced prompt generated successfully!', 'success');
        trackEvent('prompt_generated', { original_length: input.length, enhanced_length: enhancedPrompt.length });
    }, 1500);
}

// AI Playground Functions
function generatePrompt() {
    const input = document.getElementById('prompt-input').value.trim();
    const output = document.getElementById('generated-prompt');
    
    if (!input) {
        showNotification('Please enter an idea first!', 'warning');
        return;
    }
    
    // Show loading state
    output.innerHTML = '<span class="loading"></span> Generating enhanced prompt...';
    
    // Simulate AI prompt generation
    setTimeout(() => {
        const enhancedPrompt = generateEnhancedPrompt(input);
        output.innerHTML = enhancedPrompt;
        showNotification('Prompt generated successfully!', 'success');
        trackEvent('prompt_generated');
    }, 1500);
}

function generateEnhancedPrompt(userInput) {
    // Simple prompt enhancement logic
    const enhancements = [
        "Create a detailed and comprehensive",
        "Design an innovative and user-friendly",
        "Develop a professional and modern",
        "Build an interactive and engaging"
    ];
    
    const contexts = [
        "suitable for beginners and experts alike",
        "with step-by-step explanations",
        "including real-world applications",
        "with practical examples and use cases"
    ];
    
    const randomEnhancement = enhancements[Math.floor(Math.random() * enhancements.length)];
    const randomContext = contexts[Math.floor(Math.random() * contexts.length)];
    
    return `${randomEnhancement} ${userInput} ${randomContext}. Include visual elements, clear explanations, and interactive components to enhance user understanding and engagement.`;
}

function explainImageGeneration() {
    const prompt = document.getElementById('image-prompt').value.trim();
    const output = document.getElementById('image-explanation');
    
    if (!prompt) {
        showNotification('Please enter an image description first!', 'warning');
        return;
    }
    
    // Show loading state
    output.innerHTML = '<span class="loading"></span> Analyzing image generation process...';
    
    setTimeout(() => {
        const explanation = generateImageExplanation(prompt);
        output.innerHTML = explanation;
        showNotification('Image generation process explained!', 'success');
        trackEvent('image_explanation_generated');
    }, 2000);
}

function generateImageExplanation(prompt) {
    return `
        <div class="explanation-steps">
            <h5>🧠 How AI would generate "${prompt}":</h5>
            <ol>
                <li><strong>Text Processing:</strong> The AI breaks down your description into key concepts and visual elements.</li>
                <li><strong>Neural Network Analysis:</strong> Multiple layers analyze relationships between objects, colors, styles, and composition.</li>
                <li><strong>Latent Space Mapping:</strong> The AI maps your description to a multidimensional space of possible images.</li>
                <li><strong>Iterative Refinement:</strong> Through multiple passes, the AI refines details, lighting, and coherence.</li>
                <li><strong>Final Generation:</strong> The AI produces the final image combining all learned patterns and your specific requirements.</li>
            </ol>
            <p><em>Modern AI image generators use techniques like Stable Diffusion, DALL-E, or Midjourney algorithms to create stunning visuals from text descriptions.</em></p>
        </div>
    `;
}

// Chatbot Functions
let chatHistory = [];

function initializeChatbot() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Generate AI response
    setTimeout(() => {
        const response = generateAIResponse(message);
        hideTypingIndicator();
        addMessageToChat(response, 'bot');
        trackEvent('chat_message_sent');
    }, 1500);
}

function addMessageToChat(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (sender === 'bot') {
        messageContent.innerHTML = `
            <i class="fas fa-robot"></i>
            <p>${message}</p>
        `;
    } else {
        messageContent.innerHTML = `
            <i class="fas fa-user"></i>
            <p>${message}</p>
        `;
    }
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Store in chat history
    chatHistory.push({ message, sender, timestamp: new Date() });
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-robot"></i>
            <p><span class="loading"></span> AI is thinking...</p>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function generateAIResponse(userMessage) {
    const responses = {
        greeting: [
            "Hello! I'm excited to help you learn about AI. What would you like to explore today?",
            "Hi there! I'm here to guide you through the fascinating world of Artificial Intelligence. What interests you most?",
            "Welcome! I'm your AI learning companion. Let's dive into some amazing AI concepts together!"
        ],
        whatIsAI: [
            "AI (Artificial Intelligence) is the simulation of human intelligence in machines. It includes learning, reasoning, and problem-solving capabilities.",
            "Think of AI as teaching computers to think and make decisions like humans do, but often much faster and with access to vast amounts of data.",
            "AI encompasses various technologies like machine learning, natural language processing, and computer vision that enable computers to perform tasks that typically require human intelligence."
        ],
        machineLearning: [
            "Machine Learning is a subset of AI where computers learn patterns from data without being explicitly programmed for every scenario.",
            "ML algorithms improve their performance on a specific task through experience, much like how humans learn from practice.",
            "There are three main types: supervised learning (learning from examples), unsupervised learning (finding hidden patterns), and reinforcement learning (learning through trial and error)."
        ],
        neuralNetworks: [
            "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information.",
            "These networks can recognize patterns, classify data, and make predictions by adjusting the strength of connections between neurons during training.",
            "Deep learning uses multi-layered neural networks to solve complex problems like image recognition and language translation."
        ],
        applications: [
            "AI is everywhere! From recommendation systems (Netflix, Spotify) to autonomous vehicles, voice assistants, medical diagnosis, and financial fraud detection.",
            "Popular AI applications include chatbots, image recognition, language translation, predictive analytics, and robotics.",
            "AI is transforming industries like healthcare (drug discovery), finance (algorithmic trading), education (personalized learning), and entertainment (game AI)."
        ],
        careers: [
            "AI offers exciting career paths: ML Engineer, Data Scientist, AI Researcher, Computer Vision Engineer, NLP Specialist, and AI Product Manager.",
            "To get started, learn programming (Python, R), statistics, mathematics, and gain hands-on experience with ML frameworks like TensorFlow or PyTorch.",
            "The field is rapidly growing with opportunities in tech companies, startups, research institutions, and virtually every industry adopting AI."
        ],
        ethics: [
            "AI ethics involves ensuring fairness, transparency, accountability, and avoiding bias in AI systems. It's crucial for responsible AI development.",
            "Key concerns include data privacy, algorithmic bias, job displacement, and the need for explainable AI decisions in critical applications.",
            "Organizations are developing ethical AI guidelines and governments are creating regulations to ensure AI benefits society while minimizing risks."
        ],
        default: [
            "That's a great question! AI is a vast field with many interesting aspects. Could you be more specific about what you'd like to learn?",
            "I'd love to help you explore that topic! Can you tell me more about what specific aspect interests you?",
            "Interesting! Let me know if you'd like to learn about machine learning, neural networks, AI applications, or any other specific area."
        ]
    };
    
    const message = userMessage.toLowerCase();
    
    if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
        return getRandomResponse(responses.greeting);
    } else if (message.includes('what is ai') || message.includes('artificial intelligence')) {
        return getRandomResponse(responses.whatIsAI);
    } else if (message.includes('machine learning') || message.includes('ml')) {
        return getRandomResponse(responses.machineLearning);
    } else if (message.includes('neural network') || message.includes('deep learning')) {
        return getRandomResponse(responses.neuralNetworks);
    } else if (message.includes('application') || message.includes('example') || message.includes('use case')) {
        return getRandomResponse(responses.applications);
    } else if (message.includes('career') || message.includes('job') || message.includes('work')) {
        return getRandomResponse(responses.careers);
    } else if (message.includes('ethic') || message.includes('bias') || message.includes('fair')) {
        return getRandomResponse(responses.ethics);
    } else {
        return getRandomResponse(responses.default);
    }
}

function getRandomResponse(responseArray) {
    return responseArray[Math.floor(Math.random() * responseArray.length)];
}

// Utility Functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="closeNotification(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            closeNotification(notification.querySelector('.notification-close'));
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getNotificationColor(type) {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#6366f1'
    };
    return colors[type] || '#6366f1';
}

function closeNotification(closeBtn) {
    const notification = closeBtn.closest('.notification');
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// Analytics and Tracking
function trackEvent(eventName, eventData = {}) {
    // Simple event tracking (replace with your analytics solution)
    console.log(`📊 Event: ${eventName}`, eventData);
    
    // Example: Send to analytics service
    // gtag('event', eventName, eventData);
    // analytics.track(eventName, eventData);
}

// Performance Monitoring
function measurePerformance() {
    // Measure page load time
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        trackEvent('page_load_time', { load_time_ms: loadTime });
    });
}

// Error Handling
window.addEventListener('error', function(error) {
    console.error('Global error:', error);
    trackEvent('javascript_error', {
        message: error.message,
        filename: error.filename,
        line: error.lineno
    });
});

// Initialize performance monitoring
measurePerformance();

// Course interaction functions
function startCourse(courseTitle) {
    showNotification(`Starting course: ${courseTitle}`, 'success');
    trackEvent('course_started', { course: courseTitle });
    
    // Here you would typically redirect to the course or show course content
    console.log(`Starting course: ${courseTitle}`);
}

// Add course click handlers
document.addEventListener('DOMContentLoaded', function() {
    const courseButtons = document.querySelectorAll('.course-card .btn');
    courseButtons.forEach((button, index) => {
        button.addEventListener('click', function() {
            const courseCard = this.closest('.course-card');
            const courseTitle = courseCard.querySelector('h3').textContent;
            startCourse(courseTitle);
        });
    });
});

// Smooth scrolling for all anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        opacity: 0.8;
        transition: opacity 0.3s ease;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
`;
document.head.appendChild(style);

// Export functions for global access
window.PromptPal = {
    startLearning,
    watchDemo,
    generatePrompt,
    explainImageGeneration,
    sendMessage,
    showNotification,
    trackEvent
};