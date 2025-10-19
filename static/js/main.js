// Main JavaScript file
console.log('SafeTalk loaded');

// Enhanced Dark Mode Toggle with System Preference Detection
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.querySelector('.theme-icon');
    const darkModeToggle = document.getElementById('darkModeToggle');

    // Function to detect system preference
    function getSystemTheme() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Function to set theme
    function setTheme(theme, savePreference = true) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.classList.toggle('dark', theme === 'dark');

        if (savePreference) {
            localStorage.setItem('theme', theme);
        }

        // Update icons
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }

        // Update toggle switch
        if (darkModeToggle) {
            darkModeToggle.checked = theme === 'dark';
        }

        // Dispatch custom event for theme changes
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    // Function to toggle theme
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    }

    // Initialize theme
    function initializeTheme() {
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = getSystemTheme();

        // Use saved theme if available, otherwise use system preference
        const initialTheme = savedTheme || systemTheme;
        setTheme(initialTheme, !!savedTheme);

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // Only auto-switch if no manual preference is saved
                if (!localStorage.getItem('theme')) {
                    setTheme(e.matches ? 'dark' : 'light', false);
                }
            });
        }
    }

    // Add click event to toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Add change event to toggle switch
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            setTheme(this.checked ? 'dark' : 'light');
        });
    }

    // Initialize theme on load
    initializeTheme();
});

// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidenav-main');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainContent = document.querySelector('.main-content');

    // Desktop sidebar toggle
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('minimized');

            // Save state to localStorage
            const isMinimized = sidebar.classList.contains('minimized');
            localStorage.setItem('sidebarMinimized', isMinimized);
        });
    }

    // Mobile sidebar functionality
    const mobileToggle = document.createElement('button');
    mobileToggle.className = 'mobile-sidebar-toggle d-md-none';
    mobileToggle.innerHTML = '☰';
    mobileToggle.setAttribute('aria-label', 'Toggle sidebar');
    mobileToggle.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 1051;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-size: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
    `;

    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay d-md-none';
    overlay.style.cssText = `
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1040;
    `;

    document.body.appendChild(mobileToggle);
    document.body.appendChild(overlay);

    mobileToggle.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
    });

    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
    });

    // Load saved sidebar state
    const savedState = localStorage.getItem('sidebarMinimized');
    if (savedState === 'true') {
        sidebar.classList.add('minimized');
    }

    // Close mobile sidebar when clicking a link
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            }
        });
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        }
    });
});

// Enhanced Accessibility Features with ARIA Labels, Keyboard Navigation, and Screen Reader Support
document.addEventListener('DOMContentLoaded', function() {
    const accessibilityToggle = document.getElementById('accessibility-toggle');
    const accessibilityPanel = document.getElementById('accessibility-panel');
    const closeAccessibilityPanel = document.getElementById('close-accessibility-panel');

    // Toggle accessibility panel with enhanced accessibility
    if (accessibilityToggle) {
        accessibilityToggle.addEventListener('click', function() {
            const isOpen = accessibilityPanel.style.display === 'flex';
            accessibilityPanel.style.display = isOpen ? 'none' : 'flex';
            this.setAttribute('aria-expanded', !isOpen);
            this.setAttribute('aria-label', isOpen ? 'Open accessibility settings' : 'Close accessibility settings');

            // Focus management
            if (!isOpen) {
                setTimeout(() => {
                    const firstFocusable = accessibilityPanel.querySelector('button, input, select, textarea');
                    if (firstFocusable) firstFocusable.focus();
                }, 100);
            }
        });

        // Keyboard support
        accessibilityToggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    // Close accessibility panel with keyboard support
    if (closeAccessibilityPanel) {
        closeAccessibilityPanel.addEventListener('click', function() {
            accessibilityPanel.style.display = 'none';
            accessibilityToggle.setAttribute('aria-expanded', 'false');
            accessibilityToggle.focus();
        });

        closeAccessibilityPanel.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    // Close panel when clicking outside or pressing Escape
    accessibilityPanel.addEventListener('click', function(e) {
        if (e.target === accessibilityPanel) {
            accessibilityPanel.style.display = 'none';
            accessibilityToggle.setAttribute('aria-expanded', 'false');
            accessibilityToggle.focus();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && accessibilityPanel.style.display === 'flex') {
            accessibilityPanel.style.display = 'none';
            accessibilityToggle.setAttribute('aria-expanded', 'false');
            accessibilityToggle.focus();
        }
    });

    // Trap focus within accessibility panel
    accessibilityPanel.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            const focusableElements = accessibilityPanel.querySelectorAll(
                'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
    });

    // High Contrast Mode functionality with announcements
    const contrastButtons = document.querySelectorAll('.contrast-btn');
    contrastButtons.forEach(button => {
        button.addEventListener('click', function() {
            const contrast = this.getAttribute('data-contrast');

            // Remove active class from all buttons
            contrastButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Apply contrast mode
            document.documentElement.setAttribute('data-contrast', contrast);
            localStorage.setItem('contrast', contrast);

            // Announce change to screen readers
            announceToScreenReader(`High contrast mode changed to ${contrast === 'normal' ? 'normal' : contrast.replace('-', ' ')}`);
        });

        // Keyboard support for contrast buttons
        button.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // Load saved contrast setting
    const savedContrast = localStorage.getItem('contrast') || 'normal';
    document.documentElement.setAttribute('data-contrast', savedContrast);
    const activeContrastBtn = document.querySelector(`[data-contrast="${savedContrast}"]`);
    if (activeContrastBtn) activeContrastBtn.classList.add('active');

    // Enhanced Font Size Adjustment with keyboard support
    const fontDecreaseBtn = document.getElementById('font-decrease');
    const fontIncreaseBtn = document.getElementById('font-increase');
    const fontSizeDisplay = document.getElementById('font-size-display');
    let currentFontSize = parseInt(localStorage.getItem('fontSize')) || 100;

    function updateFontSize() {
        document.documentElement.style.fontSize = `${currentFontSize}%`;
        if (fontSizeDisplay) {
            fontSizeDisplay.textContent = `${currentFontSize}%`;
            fontSizeDisplay.setAttribute('aria-label', `Current font size: ${currentFontSize} percent`);
        }
        localStorage.setItem('fontSize', currentFontSize);

        // Announce change
        announceToScreenReader(`Font size changed to ${currentFontSize} percent`);
    }

    updateFontSize();

    if (fontDecreaseBtn) {
        fontDecreaseBtn.addEventListener('click', function() {
            if (currentFontSize > 75) {
                currentFontSize -= 25;
                updateFontSize();
            }
        });

        fontDecreaseBtn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    if (fontIncreaseBtn) {
        fontIncreaseBtn.addEventListener('click', function() {
            if (currentFontSize < 200) {
                currentFontSize += 25;
                updateFontSize();
            }
        });

        fontIncreaseBtn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    // Enhanced Reduced Motion with better detection
    const reduceMotionCheckbox = document.getElementById('reduce-motion');
    const savedReducedMotion = localStorage.getItem('reducedMotion') === 'true' ||
                              (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

    if (reduceMotionCheckbox) {
        reduceMotionCheckbox.checked = savedReducedMotion;
        document.documentElement.setAttribute('data-reduced-motion', savedReducedMotion);

        reduceMotionCheckbox.addEventListener('change', function() {
            const isReduced = this.checked;
            document.documentElement.setAttribute('data-reduced-motion', isReduced);
            localStorage.setItem('reducedMotion', isReduced);

            // Announce change
            announceToScreenReader(`Motion ${isReduced ? 'reduced' : 'enabled'}`);
        });
    }

    // Enhanced Text-to-Speech with better voice selection
    const enableTTSC_checkbox = document.getElementById('enable-tts');
    const savedTTS = localStorage.getItem('enableTTS') === 'true';

    if (enableTTSC_checkbox) {
        enableTTSC_checkbox.checked = savedTTS;
        document.documentElement.setAttribute('data-tts-enabled', savedTTS);

        enableTTSC_checkbox.addEventListener('change', function() {
            const isEnabled = this.checked;
            document.documentElement.setAttribute('data-tts-enabled', isEnabled);
            localStorage.setItem('enableTTS', isEnabled);

            // Announce change
            announceToScreenReader(`Text-to-speech ${isEnabled ? 'enabled' : 'disabled'}`);
        });
    }

    // Enhanced Text-to-Speech functionality
    let speechSynthesis = window.speechSynthesis;
    let currentUtterance = null;
    let availableVoices = [];

    // Load voices when available
    if (speechSynthesis) {
        speechSynthesis.addEventListener('voiceschanged', function() {
            availableVoices = speechSynthesis.getVoices();
        });
        availableVoices = speechSynthesis.getVoices();
    }

    function speakText(text, options = {}) {
        if (!speechSynthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }

        // Stop any current speech
        if (currentUtterance) {
            speechSynthesis.cancel();
        }

        // Create new utterance
        currentUtterance = new SpeechSynthesisUtterance(text);

        // Enhanced voice selection
        let preferredVoice = null;
        if (availableVoices.length > 0) {
            // Try to find preferred voices in order
            preferredVoice = availableVoices.find(voice =>
                voice.lang.startsWith('en') && voice.name.includes('Female')
            ) || availableVoices.find(voice =>
                voice.lang.startsWith('en') && voice.name.includes('Male')
            ) || availableVoices.find(voice =>
                voice.lang.startsWith('en')
            ) || availableVoices[0];
        }

        if (preferredVoice) {
            currentUtterance.voice = preferredVoice;
        }

        // Set speech properties with options
        currentUtterance.rate = options.rate || 0.9;
        currentUtterance.pitch = options.pitch || 1;
        currentUtterance.volume = options.volume || 1;
        currentUtterance.lang = options.lang || 'en-US';

        // Add event listeners for better UX
        currentUtterance.onstart = () => {
            announceToScreenReader('Speech started');
        };

        currentUtterance.onend = () => {
            announceToScreenReader('Speech finished');
        };

        currentUtterance.onerror = (e) => {
            console.error('Speech synthesis error:', e);
            announceToScreenReader('Speech synthesis error occurred');
        };

        // Speak the text
        speechSynthesis.speak(currentUtterance);
    }

    // Enhanced read aloud functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('read-aloud-btn') || e.target.closest('.read-aloud-btn')) {
            const button = e.target.classList.contains('read-aloud-btn') ? e.target : e.target.closest('.read-aloud-btn');
            const text = button.getAttribute('data-text') || button.textContent.trim();
            const isTTSEnabled = document.documentElement.getAttribute('data-tts-enabled') === 'true';

            if (isTTSEnabled && text) {
                speakText(text);
                button.setAttribute('aria-label', 'Reading aloud... Click to stop');
            } else if (!isTTSEnabled) {
                announceToScreenReader('Text-to-speech is disabled. Please enable it in accessibility settings.');
            }
        }
    });

    // Stop speech when accessibility settings change
    if (enableTTSC_checkbox) {
        enableTTSC_checkbox.addEventListener('change', function() {
            if (!this.checked && currentUtterance) {
                speechSynthesis.cancel();
            }
        });
    }

    // Screen reader announcement utility
    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.style.width = '1px';
        announcement.style.height = '1px';
        announcement.style.overflow = 'hidden';

        document.body.appendChild(announcement);
        announcement.textContent = message;

        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // Enhanced keyboard navigation for the entire application
    function initializeKeyboardNavigation() {
        // Add skip links
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);

        // Enhanced focus management for interactive elements
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]');
        interactiveElements.forEach(element => {
            element.addEventListener('focus', function() {
                this.setAttribute('data-focused', 'true');
            });

            element.addEventListener('blur', function() {
                this.removeAttribute('data-focused');
            });
        });

        // Add ARIA labels where missing
        document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').forEach(button => {
            if (!button.textContent.trim() && !button.querySelector('i, span, .material-symbols-outlined')) {
                button.setAttribute('aria-label', 'Button');
            }
        });

        // Enhanced form accessibility
        document.querySelectorAll('input, select, textarea').forEach(field => {
            const label = document.querySelector(`label[for="${field.id}"]`);
            if (label && !field.getAttribute('aria-describedby') && !field.getAttribute('aria-label')) {
                field.setAttribute('aria-label', label.textContent.trim());
            }

            // Add error message associations
            const errorElement = field.parentNode.querySelector('.error, .field-errors');
            if (errorElement) {
                const errorId = `error-${field.id || Math.random().toString(36).substr(2, 9)}`;
                errorElement.id = errorId;
                field.setAttribute('aria-describedby', errorId);
            }
        });
    }

    // Initialize keyboard navigation
    initializeKeyboardNavigation();

    // Add screen reader support for dynamic content
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Add ARIA labels to newly added buttons
                        if (node.tagName === 'BUTTON' && !node.getAttribute('aria-label') && !node.textContent.trim()) {
                            node.setAttribute('aria-label', 'Button');
                        }

                        // Add focus management to new interactive elements
                        if (node.matches('button, a, input, select, textarea, [tabindex]')) {
                            node.addEventListener('focus', function() {
                                this.setAttribute('data-focused', 'true');
                            });
                            node.addEventListener('blur', function() {
                                this.removeAttribute('data-focused');
                            });
                        }
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Notification count update
document.addEventListener('DOMContentLoaded', function() {
    const notificationCount = document.getElementById('notification-count');

    function updateNotificationCount() {
        fetch('/chat/api/notifications/unread/count/')
            .then(response => response.json())
            .then(data => {
                const count = data.unread_count || 0;
                if (count > 0) {
                    notificationCount.textContent = count > 99 ? '99+' : count;
                    notificationCount.style.display = 'inline-block';
                } else {
                    notificationCount.style.display = 'none';
                }
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }

    // Update notification count every 30 seconds
    if (notificationCount) {
        updateNotificationCount();
        setInterval(updateNotificationCount, 30000);
    }

    // Profile dropdown functionality
    const profileTrigger = document.getElementById('profileTrigger');
    const profileDropdown = document.getElementById('profileDropdown');

    if (profileTrigger && profileDropdown) {
        profileTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!profileTrigger.contains(e.target) && !profileDropdown.contains(e.target)) {
                profileDropdown.classList.remove('show');
            }
        });

        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                profileDropdown.classList.remove('show');
            }
        });
    }

    // Animated Counters for Dashboard Stats
    function animateCounters() {
        const counterElements = document.querySelectorAll('[data-count]');

        counterElements.forEach(element => {
            const target = parseInt(element.getAttribute('data-count'));

            if (!element.classList.contains('animated')) {
                element.classList.add('animated');
                let current = 0;
                const increment = target / 50; // Adjust speed here
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    element.textContent = Math.floor(current);
                }, 30);
            }
        });
    }

    // Trigger counter animation when page loads
    if (document.querySelector('[data-count]')) {
        // Small delay to ensure DOM is ready
        setTimeout(animateCounters, 500);
    }

    // Add pulse animation for icons
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);

});