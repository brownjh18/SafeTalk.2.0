// WebRTC Video Calling Implementation
class WebRTCCallManager {
    constructor() {
        this.peerConnection = null;
        this.localStream = null;
        this.remoteStream = null;
        this.signalingSocket = null;
        this.callSessionId = null;
        this.isInitiator = false;
        this.callType = 'voice'; // 'voice' or 'video'

        // ICE servers configuration
        this.iceServers = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                // Add TURN servers for production
            ]
        };

        this.onCallStateChange = null;
        this.onRemoteStream = null;
        this.onLocalStream = null;
    }

    async initializeCall(callSessionId, callType = 'voice', isInitiator = false) {
        this.callSessionId = callSessionId;
        this.callType = callType;
        this.isInitiator = isInitiator;

        try {
            // Get user media
            await this.getUserMedia();

            // Create peer connection
            this.createPeerConnection();

            // Setup signaling
            this.setupSignaling();

            if (isInitiator) {
                await this.createOffer();
            }

            this.updateCallState('connecting');
        } catch (error) {
            console.error('Failed to initialize call:', error);
            this.updateCallState('failed');
            throw error;
        }
    }

    async getUserMedia() {
        const constraints = {
            audio: true,
            video: this.callType === 'video' ? {
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } : false
        };

        try {
            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
            if (this.onLocalStream) {
                this.onLocalStream(this.localStream);
            }
        } catch (error) {
            console.error('Error accessing media devices:', error);
            throw new Error('Could not access camera/microphone. Please check permissions.');
        }
    }

    createPeerConnection() {
        this.peerConnection = new RTCPeerConnection(this.iceServers);

        // Add local stream tracks to peer connection
        this.localStream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, this.localStream);
        });

        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            if (!this.remoteStream) {
                this.remoteStream = new MediaStream();
            }
            this.remoteStream.addTrack(event.track);

            if (this.onRemoteStream) {
                this.onRemoteStream(this.remoteStream);
            }
        };

        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignalingMessage('ice_candidate', {
                    candidate: event.candidate
                });
            }
        };

        // Handle connection state changes
        this.peerConnection.onconnectionstatechange = () => {
            console.log('Connection state:', this.peerConnection.connectionState);
            switch (this.peerConnection.connectionState) {
                case 'connected':
                    this.updateCallState('connected');
                    break;
                case 'disconnected':
                case 'failed':
                    this.updateCallState('disconnected');
                    break;
                case 'closed':
                    this.updateCallState('ended');
                    break;
            }
        };

        // Handle ICE connection state changes
        this.peerConnection.oniceconnectionstatechange = () => {
            console.log('ICE connection state:', this.peerConnection.iceConnectionState);
        };
    }

    setupSignaling() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/call/${this.callSessionId}/`;

        this.signalingSocket = new WebSocket(wsUrl);

        this.signalingSocket.onopen = () => {
            console.log('Signaling connection established');
        };

        this.signalingSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleSignalingMessage(data);
        };

        this.signalingSocket.onclose = () => {
            console.log('Signaling connection closed');
        };

        this.signalingSocket.onerror = (error) => {
            console.error('Signaling error:', error);
        };
    }

    async createOffer() {
        try {
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);

            this.sendSignalingMessage('offer', {
                sdp: offer.sdp,
                type: offer.type
            });
        } catch (error) {
            console.error('Error creating offer:', error);
            throw error;
        }
    }

    async createAnswer() {
        try {
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);

            this.sendSignalingMessage('answer', {
                sdp: answer.sdp,
                type: answer.type
            });
        } catch (error) {
            console.error('Error creating answer:', error);
            throw error;
        }
    }

    sendSignalingMessage(type, data) {
        if (this.signalingSocket && this.signalingSocket.readyState === WebSocket.OPEN) {
            this.signalingSocket.send(JSON.stringify({
                type: type,
                [type]: data
            }));
        }
    }

    async handleSignalingMessage(data) {
        try {
            switch (data.type) {
                case 'offer':
                    await this.handleOffer(data.offer);
                    break;
                case 'answer':
                    await this.handleAnswer(data.answer);
                    break;
                case 'ice_candidate':
                    await this.handleIceCandidate(data.candidate);
                    break;
                case 'hangup':
                    this.handleHangup();
                    break;
            }
        } catch (error) {
            console.error('Error handling signaling message:', error);
        }
    }

    async handleOffer(offer) {
        try {
            const remoteOffer = new RTCSessionDescription(offer);
            await this.peerConnection.setRemoteDescription(remoteOffer);
            await this.createAnswer();
        } catch (error) {
            console.error('Error handling offer:', error);
        }
    }

    async handleAnswer(answer) {
        try {
            const remoteAnswer = new RTCSessionDescription(answer);
            await this.peerConnection.setRemoteDescription(remoteAnswer);
        } catch (error) {
            console.error('Error handling answer:', error);
        }
    }

    async handleIceCandidate(candidate) {
        try {
            if (candidate) {
                await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            }
        } catch (error) {
            console.error('Error handling ICE candidate:', error);
        }
    }

    handleHangup() {
        this.endCall();
    }

    toggleAudio() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                return audioTrack.enabled;
            }
        }
        return false;
    }

    toggleVideo() {
        if (this.localStream) {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                return videoTrack.enabled;
            }
        }
        return false;
    }

    endCall() {
        // Send hangup signal
        this.sendSignalingMessage('hangup', {});

        // Close peer connection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        // Stop local media tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        // Close signaling socket
        if (this.signalingSocket) {
            this.signalingSocket.close();
            this.signalingSocket = null;
        }

        this.updateCallState('ended');
    }

    updateCallState(state) {
        if (this.onCallStateChange) {
            this.onCallStateChange(state);
        }
    }

    // Screen sharing functionality
    async startScreenShare() {
        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: false
            });

            // Replace video track with screen share
            const videoTrack = screenStream.getVideoTracks()[0];
            const sender = this.peerConnection.getSenders().find(s => s.track.kind === 'video');
            if (sender) {
                await sender.replaceTrack(videoTrack);
            }

            // Handle screen share stop
            videoTrack.onended = () => {
                this.stopScreenShare();
            };

            return true;
        } catch (error) {
            console.error('Error starting screen share:', error);
            return false;
        }
    }

    async stopScreenShare() {
        try {
            // Get back to camera video
            const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
            const videoTrack = cameraStream.getVideoTracks()[0];
            const sender = this.peerConnection.getSenders().find(s => s.track.kind === 'video');
            if (sender) {
                await sender.replaceTrack(videoTrack);
            }
        } catch (error) {
            console.error('Error stopping screen share:', error);
        }
    }
}

// Global call manager instance
let callManager = null;

function initializeWebRTC() {
    // Check for WebRTC support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('WebRTC is not supported in this browser');
        return false;
    }
    return true;
}

function createCallManager() {
    if (!callManager) {
        callManager = new WebRTCCallManager();
    }
    return callManager;
}

function getCallManager() {
    return callManager;
}

// Export for global use
window.WebRTCCallManager = WebRTCCallManager;
window.initializeWebRTC = initializeWebRTC;
window.createCallManager = createCallManager;
window.getCallManager = getCallManager;