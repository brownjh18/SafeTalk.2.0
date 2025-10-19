// Video Call UI Components and Management
class VideoCallUI {
    constructor() {
        this.callContainer = null;
        this.incomingCallModal = null;
        this.permissionsModal = null;
        this.callManager = null;
        this.currentCallSessionId = null;
        this.callTimer = null;
        this.callStartTime = null;
        this.isMinimized = false;

        this.initializeUI();
        this.bindEvents();
    }

    initializeUI() {
        // Create main call container
        this.callContainer = document.createElement('div');
        this.callContainer.className = 'video-call-container';
        this.callContainer.style.display = 'none';
        this.callContainer.innerHTML = `
            <div class="video-call-header">
                <div class="call-info">
                    <h3 class="call-user-name" id="call-user-name">Connecting...</h3>
                    <p class="call-status" id="call-status">Initializing call</p>
                    <p class="call-timer" id="call-timer" style="display: none;">00:00:00</p>
                </div>
                <button class="call-btn minimize-btn" onclick="videoCallUI.minimizeCall()">
                    <i class="fas fa-minus"></i>
                </button>
            </div>

            <div class="video-call-main">
                <div class="video-container">
                    <div class="remote-video-container">
                        <video id="remote-video" class="remote-video" autoplay playsinline></video>
                        <div class="no-remote-video" id="no-remote-video">
                            <div class="call-loading">
                                <div class="call-spinner"></div>
                                <p>Connecting to call...</p>
                            </div>
                        </div>
                    </div>

                    <div class="local-video-container">
                        <video id="local-video" class="local-video" autoplay playsinline muted></video>
                    </div>
                </div>

                <div class="call-controls">
                    <button class="call-btn mic-btn" id="mic-btn" onclick="videoCallUI.toggleMic()">
                        <i class="fas fa-microphone"></i>
                    </button>
                    <button class="call-btn video-btn" id="video-btn" onclick="videoCallUI.toggleVideo()">
                        <i class="fas fa-video"></i>
                    </button>
                    <button class="call-btn screen-btn" id="screen-btn" onclick="videoCallUI.toggleScreenShare()">
                        <i class="fas fa-desktop"></i>
                    </button>
                    <button class="call-btn end-call-btn" onclick="videoCallUI.endCall()">
                        <i class="fas fa-phone-slash"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(this.callContainer);

        // Create incoming call modal
        this.incomingCallModal = document.createElement('div');
        this.incomingCallModal.className = 'incoming-call-modal';
        this.incomingCallModal.style.display = 'none';
        this.incomingCallModal.innerHTML = `
            <div class="incoming-call-content">
                <div class="incoming-call-icon" id="incoming-call-icon">
                    <i class="fas fa-phone"></i>
                </div>
                <h2 class="incoming-call-title" id="incoming-call-title">Incoming Call</h2>
                <p class="incoming-call-subtitle" id="incoming-call-subtitle">from User</p>
                <div class="incoming-call-actions">
                    <button class="incoming-call-btn decline" onclick="videoCallUI.declineCall()">
                        <i class="fas fa-phone-slash"></i> Decline
                    </button>
                    <button class="incoming-call-btn accept" onclick="videoCallUI.acceptCall()">
                        <i class="fas fa-phone"></i> Accept
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(this.incomingCallModal);

        // Create permissions modal
        this.permissionsModal = document.createElement('div');
        this.permissionsModal.className = 'permissions-modal';
        this.permissionsModal.style.display = 'none';
        this.permissionsModal.innerHTML = `
            <div class="permissions-content">
                <h2 class="permissions-title">Camera & Microphone Access</h2>
                <p class="permissions-message">
                    This app needs access to your camera and microphone to make video calls.
                    Your privacy is important to us - media access is only used during calls.
                </p>
                <ul class="permissions-list">
                    <li><i class="fas fa-check-circle"></i> Camera access for video calls</li>
                    <li><i class="fas fa-check-circle"></i> Microphone access for audio calls</li>
                    <li><i class="fas fa-check-circle"></i> Secure peer-to-peer connection</li>
                    <li><i class="fas fa-check-circle"></i> No data stored on our servers</li>
                </ul>
                <div class="permissions-actions">
                    <button class="permissions-btn deny" onclick="videoCallUI.denyPermissions()">
                        Deny
                    </button>
                    <button class="permissions-btn allow" onclick="videoCallUI.requestPermissions()">
                        Allow Access
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(this.permissionsModal);
    }

    bindEvents() {
        // Handle incoming call notifications
        if (window.WebSocket) {
            // This will be handled by the notification system
            document.addEventListener('incomingCall', (event) => {
                this.showIncomingCall(event.detail);
            });
        }
    }

    async startCall(sessionId, callType = 'voice', isInitiator = false) {
        try {
            // Check permissions first
            const hasPermissions = await this.checkPermissions();
            if (!hasPermissions) {
                this.showPermissionsModal();
                return;
            }

            // Create call manager
            this.callManager = createCallManager();

            // Set up event handlers
            this.callManager.onCallStateChange = (state) => this.onCallStateChange(state);
            this.callManager.onLocalStream = (stream) => this.onLocalStream(stream);
            this.callManager.onRemoteStream = (stream) => this.onRemoteStream(stream);

            // Initialize the call
            await this.callManager.initializeCall(sessionId, callType, isInitiator);
            this.currentCallSessionId = sessionId;

        } catch (error) {
            console.error('Failed to start call:', error);
            this.showError('Failed to start call', error.message);
        }
    }

    async acceptIncomingCall(callSessionId, callType) {
        try {
            // Accept the call via API
            const response = await fetch(`/chat/accept-call/${callSessionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Start the call
                await this.startCall(callSessionId, callType, false);
                this.hideIncomingCall();
            } else {
                throw new Error('Failed to accept call');
            }
        } catch (error) {
            console.error('Failed to accept call:', error);
            this.showError('Failed to accept call', error.message);
        }
    }

    async declineCall() {
        if (this.currentCallSessionId) {
            try {
                await fetch(`/chat/decline-call/${this.currentCallSessionId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });
            } catch (error) {
                console.error('Failed to decline call:', error);
            }
        }
        this.hideIncomingCall();
    }

    endCall() {
        if (this.callManager) {
            this.callManager.endCall();
            this.callManager = null;
        }
        this.hideCallInterface();
        this.currentCallSessionId = null;
        this.stopTimer();
    }

    minimizeCall() {
        this.isMinimized = !this.isMinimized;
        if (this.isMinimized) {
            this.callContainer.style.transform = 'translateY(calc(100% - 60px))';
            this.callContainer.style.height = '60px';
        } else {
            this.callContainer.style.transform = 'translateY(0)';
            this.callContainer.style.height = '100%';
        }
    }

    toggleMic() {
        if (this.callManager) {
            const enabled = this.callManager.toggleAudio();
            const micBtn = document.getElementById('mic-btn');
            const icon = micBtn.querySelector('i');

            if (enabled) {
                micBtn.classList.remove('muted');
                icon.className = 'fas fa-microphone';
            } else {
                micBtn.classList.add('muted');
                icon.className = 'fas fa-microphone-slash';
            }
        }
    }

    toggleVideo() {
        if (this.callManager) {
            const enabled = this.callManager.toggleVideo();
            const videoBtn = document.getElementById('video-btn');
            const icon = videoBtn.querySelector('i');

            if (enabled) {
                videoBtn.classList.remove('disabled');
                icon.className = 'fas fa-video';
            } else {
                videoBtn.classList.add('disabled');
                icon.className = 'fas fa-video-slash';
            }
        }
    }

    async toggleScreenShare() {
        if (this.callManager) {
            const screenBtn = document.getElementById('screen-btn');
            const icon = screenBtn.querySelector('i');

            if (screenBtn.classList.contains('active')) {
                // Stop screen sharing
                await this.callManager.stopScreenShare();
                screenBtn.classList.remove('active');
                icon.className = 'fas fa-desktop';
            } else {
                // Start screen sharing
                const success = await this.callManager.startScreenShare();
                if (success) {
                    screenBtn.classList.add('active');
                    icon.className = 'fas fa-stop';
                }
            }
        }
    }

    showIncomingCall(callData) {
        const icon = document.getElementById('incoming-call-icon');
        const title = document.getElementById('incoming-call-title');
        const subtitle = document.getElementById('incoming-call-subtitle');

        if (callData.call_type === 'video') {
            icon.innerHTML = '<i class="fas fa-video"></i>';
            icon.classList.add('video');
            icon.classList.remove('voice');
        } else {
            icon.innerHTML = '<i class="fas fa-phone"></i>';
            icon.classList.add('voice');
            icon.classList.remove('video');
        }

        title.textContent = `Incoming ${callData.call_type.charAt(0).toUpperCase() + callData.call_type.slice(1)} Call`;
        subtitle.textContent = `from ${callData.caller}`;

        this.currentCallSessionId = callData.call_session_id;
        this.incomingCallModal.style.display = 'flex';
    }

    hideIncomingCall() {
        this.incomingCallModal.style.display = 'none';
        this.currentCallSessionId = null;
    }

    acceptCall() {
        if (this.currentCallSessionId) {
            const callData = this.getCurrentCallData();
            this.acceptIncomingCall(this.currentCallSessionId, callData.call_type);
        }
    }

    showCallInterface() {
        this.callContainer.style.display = 'flex';
        this.isMinimized = false;
    }

    hideCallInterface() {
        this.callContainer.style.display = 'none';
        this.stopTimer();
    }

    showPermissionsModal() {
        this.permissionsModal.style.display = 'flex';
    }

    hidePermissionsModal() {
        this.permissionsModal.style.display = 'none';
    }

    async requestPermissions() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: true
            });
            // Stop the test stream
            stream.getTracks().forEach(track => track.stop());
            this.hidePermissionsModal();
            // Now proceed with the call
            this.showToast('Permissions granted! You can now make calls.');
        } catch (error) {
            console.error('Permissions denied:', error);
            this.showError('Permissions Required', 'Camera and microphone access are required for calls.');
        }
    }

    denyPermissions() {
        this.hidePermissionsModal();
        this.showToast('Call cancelled - permissions required for video calls.');
    }

    async checkPermissions() {
        try {
            const result = await navigator.permissions.query({ name: 'camera' });
            const micResult = await navigator.permissions.query({ name: 'microphone' });
            return result.state === 'granted' && micResult.state === 'granted';
        } catch (error) {
            // Fallback for browsers that don't support permissions API
            return true; // Assume granted and handle errors during getUserMedia
        }
    }

    onCallStateChange(state) {
        const statusEl = document.getElementById('call-status');
        const timerEl = document.getElementById('call-timer');
        const noRemoteVideo = document.getElementById('no-remote-video');

        switch (state) {
            case 'connecting':
                statusEl.textContent = 'Connecting...';
                noRemoteVideo.style.display = 'flex';
                break;
            case 'ringing':
                statusEl.textContent = 'Ringing...';
                break;
            case 'connected':
                statusEl.textContent = 'Connected';
                timerEl.style.display = 'block';
                noRemoteVideo.style.display = 'none';
                this.startTimer();
                this.showCallInterface();
                break;
            case 'ended':
                statusEl.textContent = 'Call ended';
                this.endCall();
                break;
            case 'failed':
                statusEl.textContent = 'Call failed';
                this.showError('Call Failed', 'Unable to establish connection');
                break;
        }
    }

    onLocalStream(stream) {
        const localVideo = document.getElementById('local-video');
        if (localVideo) {
            localVideo.srcObject = stream;
        }
    }

    onRemoteStream(stream) {
        const remoteVideo = document.getElementById('remote-video');
        const noRemoteVideo = document.getElementById('no-remote-video');

        if (remoteVideo) {
            remoteVideo.srcObject = stream;
            noRemoteVideo.style.display = 'none';
        }
    }

    startTimer() {
        this.callStartTime = new Date();
        this.callTimer = setInterval(() => {
            const elapsed = Math.floor((new Date() - this.callStartTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;

            const timerEl = document.getElementById('call-timer');
            if (timerEl) {
                timerEl.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    stopTimer() {
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
    }

    showError(title, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'call-error';
        errorDiv.innerHTML = `
            <h3 class="call-error-title">${title}</h3>
            <p class="call-error-message">${message}</p>
            <button class="call-error-retry" onclick="this.parentElement.remove()">OK</button>
        `;

        // Position in center of screen
        errorDiv.style.position = 'fixed';
        errorDiv.style.top = '50%';
        errorDiv.style.left = '50%';
        errorDiv.style.transform = 'translate(-50%, -50%)';
        errorDiv.style.zIndex = '10003';

        document.body.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    showToast(message) {
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

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    getCurrentCallData() {
        // This should be set when showing incoming call
        return {
            call_session_id: this.currentCallSessionId,
            call_type: 'voice' // Default, should be passed in
        };
    }
}

// Global instance
let videoCallUI = null;

function initializeVideoCallUI() {
    if (!videoCallUI) {
        videoCallUI = new VideoCallUI();
    }
    return videoCallUI;
}

function getVideoCallUI() {
    return videoCallUI;
}

// Export for global use
window.VideoCallUI = VideoCallUI;
window.initializeVideoCallUI = initializeVideoCallUI;
window.getVideoCallUI = getVideoCallUI;
window.videoCallUI = null; // Will be set after initialization