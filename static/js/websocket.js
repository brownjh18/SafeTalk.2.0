// WebSocket functionality for real-time messaging

class ChatWebSocket {
    constructor(sessionId, userId) {
        this.sessionId = sessionId;
        this.userId = userId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.messageQueue = [];
        this.typingTimeouts = new Map();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.sessionId}/`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.flushMessageQueue();
                this.showConnectionStatus('Connected', 'success');
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.socket.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.showConnectionStatus('Disconnected', 'warning');

                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.attemptReconnect();
                }
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showConnectionStatus('Connection Error', 'error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.showConnectionStatus('Connection Failed', 'error');
        }
    }

    attemptReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Client disconnecting');
        }
    }

    send(data) {
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, queuing message');
            this.messageQueue.push(data);
        }
    }

    flushMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.handleNewMessage(data.message);
                break;
            case 'notification':
                this.handleNewNotification(data.notification);
                break;
            case 'typing':
                this.handleTypingIndicator(data);
                break;
            case 'reaction':
                this.handleReaction(data);
                break;
            case 'read_status':
                this.handleReadStatusUpdate(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleNewMessage(message) {
        // Add message to chat interface
        this.addMessageToChat(message);

        // Play notification sound if enabled
        if (this.shouldPlaySound()) {
            this.playNotificationSound();
        }

        // Update unread count if message is not from current user
        if (message.sender_id !== this.userId) {
            this.updateUnreadCount();
        }
    }

    handleNewNotification(notification) {
        // Add notification to the UI
        this.addNotificationToUI(notification);

        // Play notification sound
        if (this.shouldPlaySound()) {
            this.playNotificationSound();
        }

        // Show visual indicator for new notification
        this.showNotificationIndicator();

        // Update unread count
        this.updateUnreadCount();
    }

    handleReadStatusUpdate(data) {
        // Update the read status of messages in the UI
        this.updateMessageReadStatus(data.message_id, data.user_id);

        // Update unread count
        this.updateUnreadCount();
    }

    handleTypingIndicator(data) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (!typingIndicator) return;

        if (data.is_typing && data.user !== this.userId) {
            // Get user display name
            const userDisplayName = data.user_display_name || data.user;
            typingIndicator.innerHTML = `
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span>${userDisplayName} is typing...</span>
            `;
            typingIndicator.style.display = 'flex';
        } else {
            typingIndicator.style.display = 'none';
        }
    }

    handleReaction(data) {
        // Update reaction counts in the UI
        this.updateReactionDisplay(data.message_id, data.reaction_type, data.user);
    }

    addMessageToChat(message) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        const messageElement = this.createMessageElement(message);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender_id === this.userId ? 'sent' : 'received'}`;
        messageDiv.dataset.messageId = message.id;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message.content;

        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        metaDiv.textContent = timestamp;

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);

        return messageDiv;
    }

    sendMessage(content) {
        if (!content.trim()) return;

        this.send({
            type: 'message',
            content: content.trim(),
            message_type: 'text'
        });
    }

    sendTyping(isTyping) {
        this.send({
            type: 'typing',
            is_typing: isTyping
        });
    }

    sendReaction(messageId, reactionType) {
        this.send({
            type: 'reaction',
            message_id: messageId,
            reaction_type: reactionType
        });
    }

    showConnectionStatus(status, type) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = `Connection: ${status}`;
            statusElement.className = `connection-status ${type}`;
        }
    }

    shouldPlaySound() {
        // Check user preferences for notification sounds
        return localStorage.getItem('notification_sound') !== 'false';
    }

    playNotificationSound() {
        // Create and play a subtle notification sound
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQdBzaO1fLOfCsFJHfH8N2QQAoUXrTp66hVFApGn+D