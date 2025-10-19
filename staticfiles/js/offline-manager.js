/**
 * Offline Manager for SafeTalk
 * Handles offline data storage, synchronization, and offline functionality
 */

class OfflineManager {
    constructor() {
        this.dbName = 'SafeTalkOffline';
        this.dbVersion = 1;
        this.db = null;
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;

        this.init();
        this.bindEvents();
    }

    async init() {
        try {
            this.db = await this.openDB();
            console.log('Offline database initialized');

            // Load cached data on startup
            await this.loadCachedData();

            // Attempt sync if online
            if (this.isOnline) {
                this.syncData();
            }
        } catch (error) {
            console.error('Failed to initialize offline database:', error);
        }
    }

    bindEvents() {
        // Online/offline event listeners
        window.addEventListener('online', () => {
            console.log('Connection restored');
            this.isOnline = true;
            this.syncData();
            this.showOnlineNotification();
        });

        window.addEventListener('offline', () => {
            console.log('Connection lost');
            this.isOnline = false;
            this.showOfflineNotification();
        });

        // Page visibility change (for background sync)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                this.syncData();
            }
        });

        // Before unload, attempt final sync
        window.addEventListener('beforeunload', () => {
            if (this.isOnline && !this.syncInProgress) {
                // Use sendBeacon for reliable data sending
                this.sendPendingData();
            }
        });
    }

    async openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores for different data types
                if (!db.objectStoreNames.contains('mood_entries')) {
                    const moodStore = db.createObjectStore('mood_entries', { keyPath: 'id' });
                    moodStore.createIndex('date', 'date', { unique: false });
                    moodStore.createIndex('synced', 'synced', { unique: false });
                }

                if (!db.objectStoreNames.contains('messages')) {
                    const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
                    messageStore.createIndex('session_id', 'session_id', { unique: false });
                    messageStore.createIndex('timestamp', 'timestamp', { unique: false });
                    messageStore.createIndex('synced', 'synced', { unique: false });
                }

                if (!db.objectStoreNames.contains('appointments')) {
                    const appointmentStore = db.createObjectStore('appointments', { keyPath: 'id' });
                    appointmentStore.createIndex('date', 'scheduled_date', { unique: false });
                    appointmentStore.createIndex('synced', 'synced', { unique: false });
                }

                if (!db.objectStoreNames.contains('pending_actions')) {
                    db.createObjectStore('pending_actions', { keyPath: 'id', autoIncrement: true });
                }
            };
        });
    }

    async storeData(storeName, data) {
        if (!this.db) return;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);

            // Add metadata
            const dataWithMeta = {
                ...data,
                synced: false,
                created_at: new Date().toISOString(),
                device_id: this.getDeviceId()
            };

            const request = store.put(dataWithMeta);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getData(storeName, key = null) {
        if (!this.db) return null;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);

            let request;
            if (key) {
                request = store.get(key);
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUnsyncedData(storeName) {
        if (!this.db) return [];

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index('synced');
            const request = index.getAll(false); // Get all where synced = false

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async markSynced(storeName, ids) {
        if (!this.db) return;

        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);

        ids.forEach(id => {
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const data = getRequest.result;
                if (data) {
                    data.synced = true;
                    data.synced_at = new Date().toISOString();
                    store.put(data);
                }
            };
        });
    }

    async logMood(mood, note = '') {
        const moodEntry = {
            id: `mood_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            mood: mood,
            note: note,
            date: new Date().toISOString().split('T')[0], // YYYY-MM-DD format
            data_type: 'mood_entries'
        };

        try {
            await this.storeData('mood_entries', moodEntry);

            // Try to sync immediately if online
            if (this.isOnline) {
                await this.syncMoodEntry(moodEntry);
            }

            // Update UI
            this.updateMoodUI(moodEntry);

            return moodEntry;
        } catch (error) {
            console.error('Failed to log mood offline:', error);
            throw error;
        }
    }

    async sendMessage(sessionId, content, messageType = 'text') {
        const message = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            session_id: sessionId,
            content: content,
            message_type: messageType,
            timestamp: new Date().toISOString(),
            data_type: 'messages'
        };

        try {
            await this.storeData('messages', message);

            // Try to sync immediately if online
            if (this.isOnline) {
                await this.syncMessage(message);
            }

            return message;
        } catch (error) {
            console.error('Failed to send message offline:', error);
            throw error;
        }
    }

    async syncData() {
        if (!this.isOnline || this.syncInProgress) return;

        this.syncInProgress = true;
        console.log('Starting data synchronization...');

        try {
            // Sync mood entries
            const unsyncedMoods = await this.getUnsyncedData('mood_entries');
            if (unsyncedMoods.length > 0) {
                await this.syncMoodEntries(unsyncedMoods);
            }

            // Sync messages
            const unsyncedMessages = await this.getUnsyncedData('messages');
            if (unsyncedMessages.length > 0) {
                await this.syncMessages(unsyncedMessages);
            }

            // Sync appointments
            const unsyncedAppointments = await this.getUnsyncedData('appointments');
            if (unsyncedAppointments.length > 0) {
                await this.syncAppointments(unsyncedAppointments);
            }

            console.log('Data synchronization completed');
            this.showSyncSuccessNotification();

        } catch (error) {
            console.error('Data synchronization failed:', error);
            this.showSyncErrorNotification();
        } finally {
            this.syncInProgress = false;
        }
    }

    async syncMoodEntries(moodEntries) {
        const response = await fetch('/accounts/api/sync-offline-data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(moodEntries)
        });

        if (response.ok) {
            const result = await response.json();
            await this.markSynced('mood_entries', moodEntries.map(m => m.id));
            console.log(`Synced ${result.synced_count} mood entries`);
        } else {
            throw new Error('Failed to sync mood entries');
        }
    }

    async syncMessages(messages) {
        // For messages, we might need to sync with chat WebSocket or API
        // This is a simplified version
        const response = await fetch('/chat/api/sync-messages/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(messages)
        });

        if (response.ok) {
            await this.markSynced('messages', messages.map(m => m.id));
        }
    }

    async syncAppointments(appointments) {
        const response = await fetch('/accounts/api/sync-appointments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(appointments)
        });

        if (response.ok) {
            await this.markSynced('appointments', appointments.map(a => a.id));
        }
    }

    async loadCachedData() {
        try {
            // Load recent mood entries
            const moodEntries = await this.getData('mood_entries');
            if (moodEntries) {
                this.displayCachedMoodEntries(moodEntries.slice(-10)); // Last 10 entries
            }

            // Load recent messages
            const messages = await this.getData('messages');
            if (messages) {
                this.displayCachedMessages(messages.slice(-20)); // Last 20 messages
            }

        } catch (error) {
            console.error('Failed to load cached data:', error);
        }
    }

    displayCachedMoodEntries(entries) {
        const container = document.getElementById('mood-history-container');
        if (!container) return;

        entries.forEach(entry => {
            const entryElement = document.createElement('div');
            entryElement.className = `mood-entry ${entry.synced ? 'synced' : 'pending'}`;
            entryElement.innerHTML = `
                <div class="mood-date">${entry.date}</div>
                <div class="mood-emoji">${this.getMoodEmoji(entry.mood)}</div>
                <div class="mood-note">${entry.note || ''}</div>
                ${!entry.synced ? '<div class="sync-status">Pending sync</div>' : ''}
            `;
            container.appendChild(entryElement);
        });
    }

    displayCachedMessages(messages) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${message.synced ? 'synced' : 'pending'}`;
            messageElement.innerHTML = `
                <div class="message-content">${message.content}</div>
                <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
                ${!message.synced ? '<div class="sync-status">Pending sync</div>' : ''}
            `;
            container.appendChild(messageElement);
        });
    }

    updateMoodUI(moodEntry) {
        // Update mood tracking UI
        const moodDisplay = document.getElementById('current-mood-display');
        if (moodDisplay) {
            moodDisplay.innerHTML = `
                <div class="mood-emoji">${this.getMoodEmoji(moodEntry.mood)}</div>
                <div class="mood-status">${moodEntry.synced ? 'Synced' : 'Saved offline'}</div>
            `;
        }

        // Add to recent moods list
        const recentMoods = document.getElementById('recent-moods');
        if (recentMoods) {
            const moodItem = document.createElement('div');
            moodItem.className = 'recent-mood-item';
            moodItem.innerHTML = `
                <span class="mood-emoji">${this.getMoodEmoji(moodEntry.mood)}</span>
                <span class="mood-date">${moodEntry.date}</span>
            `;
            recentMoods.insertBefore(moodItem, recentMoods.firstChild);
        }
    }

    getMoodEmoji(mood) {
        const moodEmojis = {
            'happy': '😊',
            'sad': '😢',
            'anxious': '😰',
            'calm': '😌',
            'angry': '😠',
            'excited': '🤩'
        };
        return moodEmojis[mood] || '😐';
    }

    getDeviceId() {
        let deviceId = localStorage.getItem('safetalk_device_id');
        if (!deviceId) {
            deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('safetalk_device_id', deviceId);
        }
        return deviceId;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    sendPendingData() {
        // Use sendBeacon for reliable delivery of pending data
        if ('sendBeacon' in navigator) {
            const unsyncedData = {
                mood_entries: [],
                messages: [],
                appointments: []
            };

            // Collect unsynced data (simplified)
            navigator.sendBeacon('/accounts/api/sync-offline-data/', JSON.stringify(unsyncedData));
        }
    }

    showOnlineNotification() {
        this.showNotification('Connection restored! Syncing data...', 'success');
    }

    showOfflineNotification() {
        this.showNotification('You are offline. Changes will be saved locally.', 'warning');
    }

    showSyncSuccessNotification() {
        this.showNotification('Data synchronized successfully!', 'success');
    }

    showSyncErrorNotification() {
        this.showNotification('Sync failed. Will retry when online.', 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add to page
        const container = document.getElementById('notifications-container') || document.body;
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Service Worker integration for background sync
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/sw.js')
                .then(registration => {
                    console.log('Service Worker registered for offline functionality');

                    // Register background sync
                    if ('sync' in registration) {
                        registration.sync.register('background-sync');
                    }
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }

    // Cache management
    async clearOldCache() {
        const cacheKeys = await caches.keys();
        const currentCache = 'safetalk-v1';

        cacheKeys.forEach(key => {
            if (key !== currentCache) {
                caches.delete(key);
            }
        });
    }

    // Storage quota management
    async checkStorageQuota() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            const usedMB = (estimate.usage / (1024 * 1024)).toFixed(2);
            const quotaMB = (estimate.quota / (1024 * 1024)).toFixed(2);

            console.log(`Storage used: ${usedMB}MB of ${quotaMB}MB`);

            // Warn if using more than 80% of quota
            if (estimate.usage > estimate.quota * 0.8) {
                this.showNotification('Storage space running low. Consider clearing old data.', 'warning');
            }
        }
    }

    // Export data for backup
    async exportData() {
        const data = {
            mood_entries: await this.getData('mood_entries'),
            messages: await this.getData('messages'),
            appointments: await this.getData('appointments'),
            export_date: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `safetalk_backup_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Import data from backup
    async importData(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const data = JSON.parse(event.target.result);

                    // Import each data type
                    if (data.mood_entries) {
                        for (const entry of data.mood_entries) {
                            await this.storeData('mood_entries', entry);
                        }
                    }

                    if (data.messages) {
                        for (const message of data.messages) {
                            await this.storeData('messages', message);
                        }
                    }

                    if (data.appointments) {
                        for (const appointment of data.appointments) {
                            await this.storeData('appointments', appointment);
                        }
                    }

                    resolve();
                } catch (error) {
                    reject(error);
                }
            };
            reader.readAsText(file);
        });
    }
}

// Initialize offline manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager = new OfflineManager();

    // Register service worker for advanced offline features
    if ('serviceWorker' in navigator) {
        window.offlineManager.registerServiceWorker();
    }
});

// Global functions for easy access
window.logMoodOffline = (mood, note) => window.offlineManager?.logMood(mood, note);
window.sendMessageOffline = (sessionId, content) => window.offlineManager?.sendMessage(sessionId, content);
window.syncOfflineData = () => window.offlineManager?.syncData();
window.exportOfflineData = () => window.offlineManager?.exportData();
window.checkStorageQuota = () => window.offlineManager?.checkStorageQuota();