// Advanced Notification System with Toast Messages and In-App Notifications
class NotificationSystem {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.maxNotifications = 5;
        this.init();
    }

    init() {
        // Create notification container
        this.createContainer();

        // Listen for theme changes to update styles
        window.addEventListener('themeChanged', () => {
            this.updateTheme();
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'n' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.showNotificationPanel();
            }
        });
    }

    createContainer() {
        // Remove existing container if it exists
        const existing = document.querySelector('.toast-container');
        if (existing) existing.remove();

        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    updateTheme() {
        // Update existing notifications for theme changes
        this.notifications.forEach(notification => {
            if (notification.element) {
                notification.element.classList.toggle('dark', document.body.classList.contains('dark'));
            }
        });
    }

    show(message, options = {}) {
        const defaults = {
            type: 'info',
            duration: 5000,
            position: 'top-right',
            title: '',
            description: '',
            actions: [],
            persistent: false,
            icon: null,
            sound: false
        };

        const config = { ...defaults, ...options };

        // Limit concurrent notifications
        if (this.notifications.length >= this.maxNotifications) {
            this.notifications[0].dismiss();
        }

        // Update container position
        this.updateContainerPosition(config.position);

        const notification = new ToastNotification(message, config, this);
        this.notifications.push(notification);

        notification.show();

        // Play sound if enabled
        if (config.sound) {
            this.playNotificationSound(config.type);
        }

        return notification;
    }

    updateContainerPosition(position) {
        this.container.className = 'toast-container';

        if (position.includes('left')) this.container.classList.add('left');
        if (position.includes('center')) this.container.classList.add('center');
        if (position.includes('bottom')) this.container.classList.add('bottom');
    }

    remove(notification) {
        const index = this.notifications.indexOf(notification);
        if (index > -1) {
            this.notifications.splice(index, 1);
        }
    }

    clearAll() {
        this.notifications.forEach(notification => notification.dismiss());
        this.notifications = [];
    }

    playNotificationSound(type) {
        // Create audio context for notification sounds
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            // Different frequencies for different notification types
            const frequencies = {
                success: 800,
                error: 400,
                warning: 600,
                info: 500
            };

            oscillator.frequency.setValueAtTime(frequencies[type] || 500, audioContext.currentTime);
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Silently fail if Web Audio API is not supported
            console.warn('Web Audio API not supported for notification sounds');
        }
    }

    // In-App Notification Panel
    showNotificationPanel() {
        let panel = document.querySelector('.notification-panel');
        if (!panel) {
            panel = this.createNotificationPanel();
        }

        panel.classList.add('show');

        // Load notifications (mock data for now)
        this.loadNotifications(panel);
    }

    createNotificationPanel() {
        const panel = document.createElement('div');
        panel.className = 'notification-panel';
        panel.innerHTML = `
            <div class="notification-header">
                <h3 class="notification-title">Notifications</h3>
                <button class="notification-close" aria-label="Close notifications">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="notification-list">
                <div class="notification-empty">
                    <p>No notifications yet</p>
                </div>
            </div>
        `;

        document.body.appendChild(panel);

        // Event listeners
        panel.querySelector('.notification-close').addEventListener('click', () => {
            panel.classList.remove('show');
        });

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel.classList.contains('show')) {
                panel.classList.remove('show');
            }
        });

        return panel;
    }

    async loadNotifications(panel) {
        const list = panel.querySelector('.notification-list');

        try {
            // Mock API call - replace with actual API endpoint
            const response = await fetch('/api/notifications/');
            const notifications = await response.json();

            if (notifications.length === 0) {
                list.innerHTML = '<div class="notification-empty"><p>No notifications yet</p></div>';
                return;
            }

            list.innerHTML = notifications.map(notification => `
                <div class="notification-item ${notification.unread ? 'unread' : ''}" data-id="${notification.id}">
                    <div class="notification-content">
                        <div class="notification-icon">
                            <span class="material-symbols-outlined">${this.getNotificationIcon(notification.type)}</span>
                        </div>
                        <div class="notification-text">
                            <h4>${notification.title}</h4>
                            <p>${notification.message}</p>
                            <small class="notification-time">${this.formatTime(notification.created_at)}</small>
                        </div>
                    </div>
                    ${notification.unread ? `
                        <div class="notification-actions">
                            <button class="notification-btn mark-read" data-id="${notification.id}">Mark as Read</button>
                        </div>
                    ` : ''}
                </div>
            `).join('');

            // Add event listeners
            list.querySelectorAll('.mark-read').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.dataset.id;
                    await this.markAsRead(id);
                    e.target.closest('.notification-item').classList.remove('unread');
                    e.target.remove();
                });
            });

        } catch (error) {
            console.error('Failed to load notifications:', error);
            list.innerHTML = '<div class="notification-empty"><p>Failed to load notifications</p></div>';
        }
    }

    getNotificationIcon(type) {
        const icons = {
            message: 'chat',
            appointment: 'calendar_today',
            achievement: 'emoji_events',
            system: 'info',
            reminder: 'schedule'
        };
        return icons[type] || 'notifications';
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;

        return date.toLocaleDateString();
    }

    async markAsRead(id) {
        try {
            await fetch(`/api/notifications/${id}/read/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
                }
            });
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }
}

class ToastNotification {
    constructor(message, config, manager) {
        this.message = message;
        this.config = config;
        this.manager = manager;
        this.element = null;
        this.timeout = null;
        this.progressBar = null;
    }

    show() {
        this.createElement();
        this.manager.container.appendChild(this.element);

        // Trigger animation
        requestAnimationFrame(() => {
            this.element.classList.add('show');
        });

        // Auto dismiss unless persistent
        if (!this.config.persistent && this.config.duration > 0) {
            this.timeout = setTimeout(() => {
                this.dismiss();
            }, this.config.duration);
        }

        // Add event listeners
        this.element.querySelector('.toast-close')?.addEventListener('click', () => {
            this.dismiss();
        });

        // Handle action buttons
        this.element.querySelectorAll('.toast-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                if (this.config.actions && this.config.actions[action]) {
                    this.config.actions[action]();
                }
                this.dismiss();
            });
        });

        // Pause timeout on hover
        this.element.addEventListener('mouseenter', () => {
            if (this.timeout) {
                clearTimeout(this.timeout);
                this.progressBar?.style.animationPlayState = 'paused';
            }
        });

        this.element.addEventListener('mouseleave', () => {
            if (!this.config.persistent && this.config.duration > 0) {
                this.timeout = setTimeout(() => {
                    this.dismiss();
                }, this.config.duration);
                this.progressBar?.style.animationPlayState = 'running';
            }
        });
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = `toast ${this.config.type}`;
        this.element.setAttribute('role', 'alert');
        this.element.setAttribute('aria-live', 'assertive');

        const icon = this.config.icon || this.getDefaultIcon();

        let actionsHTML = '';
        if (this.config.actions && Object.keys(this.config.actions).length > 0) {
            actionsHTML = `
                <div class="toast-actions">
                    ${Object.keys(this.config.actions).map(action => `
                        <button class="toast-action-btn" data-action="${action}">${action}</button>
                    `).join('')}
                </div>
            `;
        }

        this.element.innerHTML = `
            <div class="toast-icon">
                <span class="material-symbols-outlined">${icon}</span>
            </div>
            <div class="toast-content">
                <div class="toast-message">${this.config.title || this.message}</div>
                ${this.config.description ? `<div class="toast-description">${this.config.description}</div>` : ''}
                ${actionsHTML}
            </div>
            <button class="toast-close" aria-label="Close notification">
                <span class="material-symbols-outlined">close</span>
            </button>
            ${!this.config.persistent ? '<div class="toast-progress"><div class="toast-progress-fill"></div></div>' : ''}
        `;

        this.progressBar = this.element.querySelector('.toast-progress-fill');
    }

    getDefaultIcon() {
        const icons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };
        return icons[this.config.type] || 'notifications';
    }

    dismiss() {
        if (this.timeout) {
            clearTimeout(this.timeout);
        }

        this.element.classList.remove('show');
        this.element.classList.add('hide');

        setTimeout(() => {
            if (this.element && this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
            this.manager.remove(this);
        }, 300);
    }
}

// Global notification functions
const notificationSystem = new NotificationSystem();

function showNotification(message, options = {}) {
    return notificationSystem.show(message, options);
}

function showSuccess(message, options = {}) {
    return showNotification(message, { ...options, type: 'success' });
}

function showError(message, options = {}) {
    return showNotification(message, { ...options, type: 'error' });
}

function showWarning(message, options = {}) {
    return showNotification(message, { ...options, type: 'warning' });
}

function showInfo(message, options = {}) {
    return showNotification(message, { ...options, type: 'info' });
}

function clearAllNotifications() {
    notificationSystem.clearAll();
}

function showNotificationPanel() {
    notificationSystem.showNotificationPanel();
}

// Export for global use
window.NotificationSystem = NotificationSystem;
window.showNotification = showNotification;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.clearAllNotifications = clearAllNotifications;
window.showNotificationPanel = showNotificationPanel;