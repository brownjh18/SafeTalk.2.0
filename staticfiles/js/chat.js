// Modern Chat JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat features
    initializeChat();
    initializeUserSearch();
    initializeReactions();
    initializeEmojiPicker();
    initializeContextMenu();
    initializeMessageInput();
    initializeReportBlock();
    initializeRealTimeUpdates();

    function initializeChat() {
        // Auto-scroll to bottom on page load
        scrollToBottom();

        // Handle window resize for mobile
        window.addEventListener('resize', function() {
            scrollToBottom();
        });
    }

    function initializeUserSearch() {
        const searchInput = document.getElementById('user-search');
        const searchResults = document.getElementById('search-results');

        if (searchInput && searchResults) {
            let timeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(timeout);
                const query = this.value.trim();

                if (query.length < 2) {
                    searchResults.innerHTML = '';
                    return;
                }

                timeout = setTimeout(() => {
                    fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            searchResults.innerHTML = '';
                            data.results.forEach(user => {
                                const userDiv = document.createElement('div');
                                userDiv.className = 'search-result-item';
                                userDiv.innerHTML = `
                                    <span>${user.username} (${user.role})</span>
                                    <a href="/chat/start-chat/${user.id}/" class="start-chat-btn">Start Chat</a>
                                `;
                                searchResults.appendChild(userDiv);
                            });
                        })
                        .catch(error => console.error('Error:', error));
                }, 300);
            });
        }
    }

    function initializeReactions() {
        document.addEventListener('click', function(e) {
            // Handle reaction button clicks
            if (e.target.classList.contains('reaction-btn') || e.target.closest('.reaction-btn')) {
                const btn = e.target.classList.contains('reaction-btn') ? e.target : e.target.closest('.reaction-btn');
                const messageDiv = btn.closest('.message-bubble');
                const messageId = messageDiv.dataset.messageId;
                const reactionType = btn.dataset.reactionType;
                toggleReaction(messageId, reactionType);
            }

            // Handle reaction picker toggle
            if (e.target.classList.contains('reaction-trigger-btn') || e.target.closest('.reaction-trigger-btn')) {
                const btn = e.target.classList.contains('reaction-trigger-btn') ? e.target : e.target.closest('.reaction-trigger-btn');
                const messageBubble = btn.closest('.message-bubble');
                let picker = messageBubble.parentElement.querySelector('.reaction-picker');

                // Create picker if it doesn't exist
                if (!picker) {
                    picker = document.createElement('div');
                    picker.className = 'reaction-picker';
                    picker.innerHTML = `
                        <button class="reaction-option" data-reaction-type="thumbs_up" title="Thumbs Up">👍</button>
                        <button class="reaction-option" data-reaction-type="heart" title="Heart">❤️</button>
                        <button class="reaction-option" data-reaction-type="smiley" title="Smiley">😊</button>
                        <button class="reaction-option" data-reaction-type="laugh" title="Laugh">😂</button>
                        <button class="reaction-option" data-reaction-type="sad" title="Sad">😢</button>
                        <button class="reaction-option" data-reaction-type="angry" title="Angry">😠</button>
                    `;
                    messageBubble.parentElement.appendChild(picker);
                }

                hideAllPickers();
                picker.style.display = picker.style.display === 'none' ? 'flex' : 'none';
            }

            // Handle reaction option selection
            if (e.target.classList.contains('reaction-option')) {
                const messageDiv = e.target.closest('.message-bubble');
                const messageId = messageDiv.dataset.messageId;
                const reactionType = e.target.dataset.reactionType;
                const picker = e.target.closest('.reaction-picker');
                picker.style.display = 'none';
                toggleReaction(messageId, reactionType);
            }
        });

        // Hide pickers when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.reaction-picker') && !e.target.closest('.add-reaction-btn')) {
                hideAllPickers();
            }
        });
    }

    function initializeEmojiPicker() {
        const emojiBtn = document.querySelector('.emoji-btn');
        const emojiPicker = document.getElementById('emoji-picker');
        const messageInput = document.getElementById('message-input');

        if (emojiBtn && emojiPicker && messageInput) {
            emojiBtn.addEventListener('click', function(e) {
                e.preventDefault();
                emojiPicker.style.display = emojiPicker.style.display === 'none' ? 'block' : 'none';
            });

            // Handle emoji selection
            emojiPicker.addEventListener('click', function(e) {
                if (e.target.classList.contains('emoji-option')) {
                    const emoji = e.target.dataset.emoji;
                    const cursorPos = messageInput.selectionStart;
                    const textBefore = messageInput.value.substring(0, cursorPos);
                    const textAfter = messageInput.value.substring(cursorPos);
                    messageInput.value = textBefore + emoji + textAfter;
                    messageInput.focus();
                    messageInput.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
                    emojiPicker.style.display = 'none';
                }
            });

            // Hide emoji picker when clicking outside
            document.addEventListener('click', function(e) {
                if (!emojiBtn.contains(e.target) && !emojiPicker.contains(e.target)) {
                    emojiPicker.style.display = 'none';
                }
            });
        }
    }

    function initializeContextMenu() {
        let currentMessage = null;

        document.addEventListener('contextmenu', function(e) {
            const messageBubble = e.target.closest('.message-bubble');
            if (messageBubble) {
                e.preventDefault();
                currentMessage = messageBubble;
                showContextMenu(e.pageX, e.pageY, messageBubble);
            }
        });

        document.addEventListener('click', function(e) {
            const contextMenu = document.getElementById('message-context-menu');
            if (contextMenu && !contextMenu.contains(e.target)) {
                contextMenu.style.display = 'none';
            }
        });

        // Handle context menu actions
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('context-menu-item')) {
                const action = e.target.dataset.action;
                if (currentMessage) {
                    handleContextMenuAction(action, currentMessage);
                }
                document.getElementById('message-context-menu').style.display = 'none';
            }
        });
    }

    function initializeMessageInput() {
        const messageForm = document.getElementById('message-form');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');

        if (messageForm && messageInput) {
            // Handle form submission
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                sendMessage();
            });

            // Handle Enter key (send message)
            messageInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            // Handle input for typing indicator (placeholder for now)
            let typingTimeout;
            messageInput.addEventListener('input', function() {
                // Show typing indicator
                clearTimeout(typingTimeout);
                // In a real implementation, this would send typing status via WebSocket

                typingTimeout = setTimeout(() => {
                    // Hide typing indicator
                }, 1000);
            });

            // Auto-resize textarea (if we change to textarea later)
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });
        }
    }

    function initializeReportBlock() {
        // Report user functionality
        const reportBtn = document.getElementById('report-user-btn');
        if (reportBtn) {
            reportBtn.addEventListener('click', function() {
                const userId = this.dataset.userId;
                if (confirm('Are you sure you want to report this user?')) {
                    reportUser(userId);
                }
            });
        }

        // Block user functionality
        const blockBtn = document.getElementById('block-user-btn');
        if (blockBtn) {
            blockBtn.addEventListener('click', function() {
                const userId = this.dataset.userId;
                if (confirm('Are you sure you want to block this user? You will no longer see their messages.')) {
                    blockUser(userId);
                }
            });
        }

        // Report message functionality
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('report-message-btn')) {
                const messageId = e.target.dataset.messageId;
                const userId = e.target.dataset.userId;
                if (confirm('Are you sure you want to report this message?')) {
                    reportMessage(messageId, userId);
                }
            }
        });
    }

    // Utility Functions
    function scrollToBottom() {
        const messagesContainer = document.getElementById('session-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function hideAllPickers() {
        document.querySelectorAll('.reaction-picker, .emoji-picker').forEach(picker => {
            picker.style.display = 'none';
        });
    }

    function toggleReaction(messageId, reactionType) {
        const formData = new FormData();
        formData.append('reaction_type', reactionType);

        fetch(`/chat/toggle-reaction/${messageId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateReactions(messageId, data.reaction_counts, data.user_reaction);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function updateReactions(messageId, reactionCounts, userReaction) {
        const messageDiv = document.querySelector(`.message-bubble[data-message-id="${messageId}"]`);
        const reactionsDiv = messageDiv.parentElement.querySelector('.message-reactions');

        if (!reactionsDiv) return;

        // Clear existing reaction buttons
        const existingBtns = reactionsDiv.querySelectorAll('.reaction-btn');
        existingBtns.forEach(btn => btn.remove());

        // Add updated reaction buttons
        for (const [type, count] of Object.entries(reactionCounts)) {
            const emoji = getEmojiForType(type);
            const btn = document.createElement('button');
            btn.className = 'reaction-btn';
            btn.dataset.reactionType = type;
            btn.innerHTML = `${emoji}${count > 1 ? ` <span class="reaction-count">${count}</span>` : ''}`;
            if (userReaction === type) {
                btn.classList.add('user-reacted');
            }
            reactionsDiv.appendChild(btn);
        }
    }

    function getEmojiForType(type) {
        const emojis = {
            'thumbs_up': '👍',
            'heart': '❤️',
            'smiley': '😊',
            'laugh': '😂',
            'sad': '😢',
            'angry': '😠'
        };
        return emojis[type] || type;
    }

    function sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();

        if (!message) return;

        // Disable send button to prevent double submission
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) sendBtn.disabled = true;

        // Send via AJAX for real-time updates
        const formData = new FormData();
        formData.append('content', message);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Check if there's a file attachment
        const fileInput = document.getElementById('file-input');
        if (fileInput && fileInput.files[0]) {
            formData.append('attachment', fileInput.files[0]);
        }

        fetch(window.location.href, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                // Clear input
                messageInput.value = '';
                if (fileInput) fileInput.value = '';

                // Hide file preview if exists
                const filePreview = document.getElementById('file-preview');
                if (filePreview) filePreview.style.display = 'none';

                // Reset message input requirements
                messageInput.required = true;
                messageInput.placeholder = "Type a message...";

                // Scroll to bottom
                scrollToBottom();

                // In a real-time implementation, the new message would be added via WebSocket
                // For now, we'll reload the page to show the new message
                setTimeout(() => location.reload(), 500);
            } else {
                throw new Error('Failed to send message');
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            showToast('Failed to send message. Please try again.');
        })
        .finally(() => {
            // Re-enable send button
            if (sendBtn) sendBtn.disabled = false;
        });
    }

    function showContextMenu(x, y, messageBubble) {
        const contextMenu = document.getElementById('message-context-menu');
        if (!contextMenu) return;

        contextMenu.style.left = x + 'px';
        contextMenu.style.top = y + 'px';
        contextMenu.style.display = 'block';
    }

    function handleContextMenuAction(action, messageBubble) {
        const messageId = messageBubble.dataset.messageId;
        const messageContent = messageBubble.querySelector('.message-content').textContent;

        switch (action) {
            case 'reply':
                // Focus input and add reply indicator
                const input = document.getElementById('message-input');
                input.focus();
                input.placeholder = `Replying to: ${messageContent.substring(0, 50)}...`;
                break;
            case 'forward':
                // Copy message to clipboard for forwarding
                navigator.clipboard.writeText(messageContent).then(() => {
                    showToast('Message copied to clipboard');
                });
                break;
            case 'copy':
                // Copy message text
                navigator.clipboard.writeText(messageContent).then(() => {
                    showToast('Message text copied');
                });
                break;
            case 'react':
                // Show reaction picker
                const picker = messageBubble.parentElement.querySelector('.reaction-picker');
                if (picker) {
                    hideAllPickers();
                    picker.style.display = 'flex';
                }
                break;
        }
    }

    function showToast(message) {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        document.body.appendChild(toast);

        setTimeout(() => toast.style.opacity = '1', 100);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    function reportUser(userId) {
        const formData = new FormData();
        formData.append('reason', 'harassment'); // Default reason, could be made configurable

        fetch(`/chat/report-user/${userId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('User reported successfully');
            } else {
                showToast('Error reporting user: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error reporting user');
        });
    }

    function blockUser(userId) {
        const formData = new FormData();

        fetch(`/chat/block-user/${userId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('User blocked successfully');
                // Redirect back to messages
                setTimeout(() => window.location.href = '/chat/messages/', 1000);
            } else {
                showToast('Error blocking user: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error blocking user');
        });
    }

    function reportMessage(messageId, userId) {
        const formData = new FormData();
        formData.append('reason', 'inappropriate');
        formData.append('message_id', messageId);

        fetch(`/chat/report-user/${userId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Message reported successfully');
            } else {
                showToast('Error reporting message: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error reporting message');
        });
    }

    // Text-to-speech functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('read-aloud-btn')) {
            const text = e.target.dataset.text;
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                speechSynthesis.speak(utterance);
            } else {
                showToast('Text-to-speech not supported in this browser');
            }
        }
    });

    // File attachment functionality
    initializeFileUpload();

    function initializeFileUpload() {
        const attachmentBtn = document.getElementById('attachment-btn');
        const fileInput = document.getElementById('file-input');
        const filePreview = document.getElementById('file-preview');
        const filePreviewName = document.getElementById('file-preview-name');
        const removeFileBtn = document.getElementById('remove-file-btn');
        const messageInput = document.getElementById('message-input');

        if (attachmentBtn && fileInput) {
            attachmentBtn.addEventListener('click', function() {
                fileInput.click();
            });

            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    // Validate file size (10MB limit)
                    if (file.size > 10 * 1024 * 1024) {
                        showToast('File size must be less than 10MB');
                        fileInput.value = '';
                        return;
                    }

                    // Show file preview
                    filePreviewName.textContent = file.name;
                    filePreview.style.display = 'block';

                    // Make message input optional when file is attached
                    messageInput.required = false;
                    messageInput.placeholder = "Add a caption (optional)...";
                }
            });

            removeFileBtn.addEventListener('click', function() {
                fileInput.value = '';
                filePreview.style.display = 'none';
                messageInput.required = true;
                messageInput.placeholder = "Type a message...";
            });
        }
    }

    // Call functionality
    initializeCallFeatures();

    function initializeCallFeatures() {
        // Initialize video call UI
        window.videoCallUI = initializeVideoCallUI();

        const voiceCallBtn = document.getElementById('voice-call-btn');
        const videoCallBtn = document.getElementById('video-call-btn');

        if (voiceCallBtn) {
            voiceCallBtn.addEventListener('click', function() {
                initiateCall('voice');
            });
        }

        if (videoCallBtn) {
            videoCallBtn.addEventListener('click', function() {
                initiateCall('video');
            });
        }

        // Handle call acceptance/decline
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('accept-call') || e.target.closest('.accept-call')) {
                const btn = e.target.classList.contains('accept-call') ? e.target : e.target.closest('.accept-call');
                const callId = btn.dataset.callId;
                acceptCall(callId);
            }

            if (e.target.classList.contains('decline-call') || e.target.closest('.decline-call')) {
                const btn = e.target.classList.contains('decline-call') ? e.target : e.target.closest('.decline-call');
                const callId = btn.dataset.callId;
                declineCall(callId);
            }
        });

        // Listen for incoming call notifications
        if (window.WebSocket && window.notificationSocket) {
            // Handle incoming calls via WebSocket notifications
            const originalOnMessage = window.notificationSocket.onmessage;
            window.notificationSocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'notification' && data.notification.notification_type === 'call') {
                    // Show incoming call UI
                    window.videoCallUI.showIncomingCall({
                        call_session_id: data.notification.related_id,
                        call_type: data.notification.call_type,
                        caller: data.notification.caller
                    });
                }
                // Call original handler
                if (originalOnMessage) {
                    originalOnMessage.call(this, event);
                }
            };
        }
    }

    function initiateCall(callType) {
        // Get current session ID from URL
        const urlParts = window.location.pathname.split('/');
        const sessionId = urlParts[urlParts.length - 2]; // Assuming URL format: /chat/session/<session_id>/

        if (!sessionId) {
            showToast('Unable to determine chat session');
            return;
        }

        // Initiate call via API
        fetch(`/chat/initiate-call/${sessionId}/`, {
            method: 'POST',
            body: new FormData(), // Empty form data
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Start the call with WebRTC
                window.videoCallUI.startCall(data.call_session_id, callType, true);
                showToast(`${callType.charAt(0).toUpperCase() + callType.slice(1)} call initiated`);
            } else {
                showToast('Failed to initiate call');
            }
        })
        .catch(error => {
            console.error('Error initiating call:', error);
            showToast('Failed to initiate call');
        });
    }

    function acceptCall(callId) {
        // Accept call via API
        fetch(`/chat/accept-call/${callId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Get call details and start WebRTC
                // For now, assume voice call - in production, get from API response
                window.videoCallUI.startCall(callId, 'voice', false);
            } else {
                showToast('Failed to accept call');
            }
        })
        .catch(error => {
            console.error('Error accepting call:', error);
            showToast('Failed to accept call');
        });
    }

    function declineCall(callId) {
        // Decline call via API
        fetch(`/chat/decline-call/${callId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Call declined');
                // Reload to update UI
                setTimeout(() => location.reload(), 1000);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    // Image modal functionality
    function openImageModal(src) {
        let modal = document.getElementById('image-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'image-modal';
            modal.className = 'image-modal';
            modal.innerHTML = `
                <button class="image-modal-close">&times;</button>
                <img src="" alt="Full size image">
            `;
            document.body.appendChild(modal);

            modal.querySelector('.image-modal-close').addEventListener('click', function() {
                modal.style.display = 'none';
            });

            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }

        modal.querySelector('img').src = src;
        modal.style.display = 'flex';
    }

    // Make openImageModal globally available
    window.openImageModal = openImageModal;

    // Call interface functions
    function showCallInterface(status) {
        let callInterface = document.getElementById('call-interface');
        if (!callInterface) {
            callInterface = document.createElement('div');
            callInterface.id = 'call-interface';
            callInterface.className = 'call-interface';
            callInterface.innerHTML = `
                <div class="call-header">
                    <div class="call-user">Call in progress...</div>
                    <div class="call-status-text">${status}</div>
                </div>
                <div class="call-controls">
                    <button class="call-btn-large call-end" onclick="endCall()">
                        <i class="fas fa-phone-slash"></i>
                    </button>
                </div>
            `;
            document.body.appendChild(callInterface);
        }

        callInterface.style.display = 'flex';
    }

    function endCall() {
        const callInterface = document.getElementById('call-interface');
        if (callInterface) {
            callInterface.style.display = 'none';
        }
        showToast('Call ended');
    }

    // Make endCall globally available
    window.endCall = endCall;

    // Enhanced message input handling
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');

    if (messageInput && sendBtn) {
        // Auto-resize textarea (if we change to textarea later)
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        // Send on Ctrl+Enter
        messageInput.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Real-time updates functionality
    function initializeRealTimeUpdates() {
        // Poll for new messages every 5 seconds
        setInterval(() => {
            checkForNewMessages();
            updateOnlineStatus();
        }, 5000);

        // Check for new messages immediately
        checkForNewMessages();
    }

    function checkForNewMessages() {
        // Get the current session ID from URL or data attribute
        const sessionMessages = document.getElementById('session-messages');
        if (!sessionMessages) return;

        const lastMessageId = getLastMessageId();

        fetch(`${window.location.pathname}?last_id=${lastMessageId}&ajax=1`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.new_messages && data.new_messages.length > 0) {
                appendNewMessages(data.new_messages);
                scrollToBottom();
                showNewMessageIndicator(data.new_messages.length);
            }
        })
        .catch(error => console.log('Real-time check failed:', error));
    }

    function getLastMessageId() {
        const messages = document.querySelectorAll('.message-bubble[data-message-id]');
        if (messages.length === 0) return 0;

        const lastMessage = messages[messages.length - 1];
        return parseInt(lastMessage.dataset.messageId) || 0;
    }

    function appendNewMessages(messages) {
        const messagesContainer = document.getElementById('session-messages');
        if (!messagesContainer) return;

        messages.forEach(message => {
            const messageElement = createMessageElement(message);
            messagesContainer.appendChild(messageElement);
        });
    }

    function createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-wrapper';
        messageDiv.dataset.messageId = message.id;

        const isOwnMessage = message.sender_id === parseInt(document.body.dataset.userId);

        messageDiv.innerHTML = `
            <div class="message-bubble ${isOwnMessage ? 'own-message' : ''}" data-message-id="${message.id}">
                <div class="message-header">
                    <span class="message-sender">${message.sender}</span>
                    <span class="message-time">${message.timestamp}</span>
                </div>
                <div class="message-content">${message.content}</div>
                <div class="message-actions">
                    <button class="reaction-trigger-btn" title="Add reaction">😊</button>
                    <button class="reply-btn" title="Reply">↩️</button>
                </div>
                <div class="message-reactions"></div>
            </div>
        `;

        return messageDiv;
    }

    function showNewMessageIndicator(count) {
        // Remove existing indicator
        const existingIndicator = document.querySelector('.new-messages-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Create new indicator
        const indicator = document.createElement('div');
        indicator.className = 'new-messages-indicator';
        indicator.textContent = `${count} new message${count > 1 ? 's' : ''}`;
        indicator.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #007bff;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            z-index: 1000;
            cursor: pointer;
            animation: slideIn 0.3s ease-out;
        `;

        indicator.addEventListener('click', () => {
            scrollToBottom();
            indicator.remove();
        });

        document.body.appendChild(indicator);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (indicator.parentElement) {
                indicator.remove();
            }
        }, 5000);
    }

    function updateOnlineStatus() {
        // Update online status indicators
        const onlineIndicators = document.querySelectorAll('.online-status');
        onlineIndicators.forEach(indicator => {
            const userId = indicator.dataset.userId;
            if (userId) {
                // In a real implementation, this would check actual online status
                // For now, we'll simulate random online/offline status
                const isOnline = Math.random() > 0.3; // 70% chance of being online
                indicator.className = `online-status ${isOnline ? 'online' : 'offline'}`;
                indicator.title = isOnline ? 'Online' : 'Offline';
            }
        });
    }

    // Add CSS for new message indicator animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .new-messages-indicator:hover {
            background: #0056b3;
        }

        .online-status.online {
            color: #28a745;
        }

        .online-status.offline {
            color: #6c757d;
        }

        .message-wrapper {
            margin-bottom: 10px;
        }

        .message-bubble.own-message {
            background: #007bff;
            color: white;
            margin-left: auto;
            margin-right: 0;
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 5px;
            opacity: 0.8;
        }

        .message-actions {
            display: none;
            margin-top: 5px;
        }

        .message-bubble:hover .message-actions {
            display: flex;
            gap: 5px;
        }

        .reaction-trigger-btn, .reply-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            opacity: 0.7;
        }

        .reaction-trigger-btn:hover, .reply-btn:hover {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
});