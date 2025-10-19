// Drag and Drop Functionality for File Uploads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop for all file upload areas
    initializeDragDrop();

    function initializeDragDrop() {
        const dropZones = document.querySelectorAll('.drag-drop-zone');

        dropZones.forEach(zone => {
            const input = zone.querySelector('input[type="file"]');
            const preview = zone.querySelector('.file-preview');
            const uploadText = zone.querySelector('.upload-text');

            if (!input) return;

            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });

            // Highlight drop zone when item is dragged over it
            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, unhighlight, false);
            });

            // Handle dropped files
            zone.addEventListener('drop', handleDrop, false);

            // Handle file selection via click
            zone.addEventListener('click', () => input.click());
            input.addEventListener('change', (e) => handleFiles(e.target.files));

            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                handleFiles(files);
            }

            function handleFiles(files) {
                if (files.length === 0) return;

                // Validate file types and sizes
                const validFiles = Array.from(files).filter(file => {
                    const maxSize = 10 * 1024 * 1024; // 10MB
                    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain'];

                    if (file.size > maxSize) {
                        showNotification(`File "${file.name}" is too large. Maximum size is 10MB.`, 'error');
                        return false;
                    }

                    if (!allowedTypes.includes(file.type)) {
                        showNotification(`File type "${file.type}" is not allowed.`, 'error');
                        return false;
                    }

                    return true;
                });

                if (validFiles.length === 0) return;

                // Process valid files
                validFiles.forEach(file => {
                    if (file.type.startsWith('image/')) {
                        handleImageFile(file, zone);
                    } else {
                        handleDocumentFile(file, zone);
                    }
                });

                // Update input
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                input.files = dt.files;
            }

            function handleImageFile(file, zone) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    updatePreview(zone, {
                        type: 'image',
                        src: e.target.result,
                        name: file.name,
                        size: formatFileSize(file.size)
                    });
                };
                reader.readAsDataURL(file);
            }

            function handleDocumentFile(file, zone) {
                updatePreview(zone, {
                    type: 'document',
                    name: file.name,
                    size: formatFileSize(file.size),
                    icon: getFileIcon(file.type)
                });
            }
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        e.currentTarget.classList.add('drag-over');
    }

    function unhighlight(e) {
        e.currentTarget.classList.remove('drag-over');
    }

    function updatePreview(zone, fileData) {
        const preview = zone.querySelector('.file-preview');
        const uploadText = zone.querySelector('.upload-text');

        if (!preview) return;

        let previewHTML = '';

        if (fileData.type === 'image') {
            previewHTML = `
                <div class="file-preview-content">
                    <img src="${fileData.src}" alt="${fileData.name}" class="file-preview-image">
                    <div class="file-preview-info">
                        <div class="file-preview-name">${fileData.name}</div>
                        <div class="file-preview-size">${fileData.size}</div>
                    </div>
                    <button type="button" class="file-remove-btn" aria-label="Remove file">&times;</button>
                </div>
            `;
        } else {
            previewHTML = `
                <div class="file-preview-content">
                    <div class="file-preview-icon">${fileData.icon}</div>
                    <div class="file-preview-info">
                        <div class="file-preview-name">${fileData.name}</div>
                        <div class="file-preview-size">${fileData.size}</div>
                    </div>
                    <button type="button" class="file-remove-btn" aria-label="Remove file">&times;</button>
                </div>
            `;
        }

        preview.innerHTML = previewHTML;
        preview.style.display = 'block';

        if (uploadText) {
            uploadText.style.display = 'none';
        }

        // Add remove functionality
        const removeBtn = preview.querySelector('.file-remove-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                clearPreview(zone);
            });
        }

        // Announce to screen readers
        announceToScreenReader(`File "${fileData.name}" uploaded successfully`);
    }

    function clearPreview(zone) {
        const preview = zone.querySelector('.file-preview');
        const uploadText = zone.querySelector('.upload-text');
        const input = zone.querySelector('input[type="file"]');

        if (preview) {
            preview.innerHTML = '';
            preview.style.display = 'none';
        }

        if (uploadText) {
            uploadText.style.display = 'block';
        }

        if (input) {
            input.value = '';
        }

        announceToScreenReader('File removed');
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function getFileIcon(mimeType) {
        const iconMap = {
            'application/pdf': '📄',
            'text/plain': '📝',
            'application/msword': '📄',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📄',
            'default': '📎'
        };

        return iconMap[mimeType] || iconMap.default;
    }

    function showNotification(message, type = 'info') {
        // Use existing notification system or create a simple one
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-xl shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            'bg-blue-500'
        } text-white`;

        notification.innerHTML = `
            <div class="flex items-center">
                <span class="material-symbols-outlined mr-2">${
                    type === 'success' ? 'check_circle' :
                    type === 'error' ? 'error' :
                    'info'
                }</span>
                ${message}
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

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

    // Multiple file upload support
    function initializeMultipleUpload() {
        const multiUploadZones = document.querySelectorAll('.multi-file-upload');

        multiUploadZones.forEach(zone => {
            const input = zone.querySelector('input[type="file"][multiple]');
            const fileList = zone.querySelector('.file-list');

            if (!input || !fileList) return;

            input.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                updateFileList(zone, files);
            });

            // Drag and drop for multiple files
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.add('drag-over'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.remove('drag-over'), false);
            });

            zone.addEventListener('drop', (e) => {
                const files = Array.from(e.dataTransfer.files);
                updateFileList(zone, files);

                // Update input
                const dt = new DataTransfer();
                files.forEach(file => dt.items.add(file));
                input.files = dt.files;
            });
        });
    }

    function updateFileList(zone, files) {
        const fileList = zone.querySelector('.file-list');
        if (!fileList) return;

        fileList.innerHTML = '';

        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-item-content">
                    <span class="file-item-icon">${getFileIcon(file.type)}</span>
                    <div class="file-item-info">
                        <div class="file-item-name">${file.name}</div>
                        <div class="file-item-size">${formatFileSize(file.size)}</div>
                    </div>
                    <button type="button" class="file-item-remove" data-index="${index}" aria-label="Remove ${file.name}">&times;</button>
                </div>
            `;

            fileList.appendChild(fileItem);
        });

        // Add remove functionality
        fileList.querySelectorAll('.file-item-remove').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const newFiles = files.filter((_, i) => i !== index);
                updateFileList(zone, newFiles);

                // Update input
                const input = zone.querySelector('input[type="file"]');
                const dt = new DataTransfer();
                newFiles.forEach(file => dt.items.add(file));
                input.files = dt.files;
            });
        });
    }

    // Initialize multiple file upload
    initializeMultipleUpload();
});