// Infinite Scroll Implementation for Long Lists
class InfiniteScroll {
    constructor(options = {}) {
        this.container = options.container || '.infinite-scroll-container';
        this.itemSelector = options.itemSelector || '.scroll-item';
        this.loadingSelector = options.loadingSelector || '.infinite-scroll-loading';
        this.endpoint = options.endpoint || '';
        this.params = options.params || {};
        this.page = options.initialPage || 1;
        this.hasNextPage = true;
        this.isLoading = false;
        this.observer = null;
        this.loadingElement = null;

        this.init();
    }

    init() {
        this.container = typeof this.container === 'string'
            ? document.querySelector(this.container)
            : this.container;

        if (!this.container) {
            console.error('Infinite scroll container not found');
            return;
        }

        this.createLoadingElement();
        this.setupIntersectionObserver();
        this.bindEvents();
    }

    createLoadingElement() {
        this.loadingElement = document.createElement('div');
        this.loadingElement.className = 'infinite-scroll-loading';
        this.loadingElement.innerHTML = `
            <div class="infinite-scroll-spinner"></div>
            <p>Loading more...</p>
        `;

        // Hide initially
        this.loadingElement.style.display = 'none';
        this.container.appendChild(this.loadingElement);
    }

    setupIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '100px',
            threshold: 0.1
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasNextPage && !this.isLoading) {
                    this.loadMore();
                }
            });
        }, options);

        // Observe the loading element
        this.observer.observe(this.loadingElement);
    }

    bindEvents() {
        // Handle manual load more button if present
        const loadMoreBtn = this.container.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                if (!this.isLoading) {
                    this.loadMore();
                }
            });
        }

        // Handle refresh/reset
        const refreshBtn = this.container.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.reset();
            });
        }
    }

    async loadMore() {
        if (this.isLoading || !this.hasNextPage) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const data = await this.fetchData();
            this.handleResponse(data);
        } catch (error) {
            this.handleError(error);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    async fetchData() {
        const url = new URL(this.endpoint, window.location.origin);
        url.searchParams.set('page', this.page + 1);

        // Add additional params
        Object.entries(this.params).forEach(([key, value]) => {
            url.searchParams.set(key, value);
        });

        const response = await fetch(url.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    handleResponse(data) {
        if (data.items && data.items.length > 0) {
            this.appendItems(data.items);
            this.page++;

            // Check if there are more pages
            this.hasNextPage = data.has_next || data.next_page_url;

            // Update pagination info if present
            this.updatePaginationInfo(data);
        } else {
            this.hasNextPage = false;
            this.showNoMoreItems();
        }

        // Trigger custom event
        this.container.dispatchEvent(new CustomEvent('infiniteScrollLoaded', {
            detail: { data, page: this.page }
        }));
    }

    appendItems(items) {
        const fragment = document.createDocumentFragment();

        items.forEach(item => {
            const element = this.createItemElement(item);
            fragment.appendChild(element);
        });

        // Insert before loading element
        this.container.insertBefore(fragment, this.loadingElement);

        // Trigger animations for new items
        this.animateNewItems(items.length);
    }

    createItemElement(item) {
        // This should be overridden by subclasses for specific item types
        const element = document.createElement('div');
        element.className = 'scroll-item';
        element.innerHTML = `<div class="item-content">${JSON.stringify(item)}</div>`;
        return element;
    }

    animateNewItems(count) {
        const newItems = this.container.querySelectorAll('.scroll-item:nth-last-child(-n+' + count + ')');

        newItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';

            setTimeout(() => {
                item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    handleError(error) {
        console.error('Infinite scroll error:', error);

        // Show error message
        this.showError('Failed to load more items. Please try again.');

        // Trigger error event
        this.container.dispatchEvent(new CustomEvent('infiniteScrollError', {
            detail: { error }
        }));
    }

    showLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'flex';
        }
    }

    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'none';
        }
    }

    showNoMoreItems() {
        if (this.loadingElement) {
            this.loadingElement.innerHTML = `
                <div class="no-more-items">
                    <p>No more items to load</p>
                </div>
            `;
            this.loadingElement.style.display = 'block';
        }
    }

    showError(message) {
        if (this.loadingElement) {
            this.loadingElement.innerHTML = `
                <div class="infinite-scroll-error">
                    <p>${message}</p>
                    <button class="retry-btn">Retry</button>
                </div>
            `;
            this.loadingElement.style.display = 'block';

            // Add retry functionality
            const retryBtn = this.loadingElement.querySelector('.retry-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    this.loadMore();
                });
            }
        }
    }

    updatePaginationInfo(data) {
        const paginationInfo = this.container.querySelector('.pagination-info');
        if (paginationInfo && data.total_count) {
            const loadedCount = this.container.querySelectorAll('.scroll-item').length;
            paginationInfo.textContent = `Showing ${loadedCount} of ${data.total_count} items`;
        }
    }

    reset() {
        // Reset state
        this.page = 1;
        this.hasNextPage = true;
        this.isLoading = false;

        // Clear existing items
        const items = this.container.querySelectorAll('.scroll-item');
        items.forEach(item => item.remove());

        // Reset loading element
        this.loadingElement.innerHTML = `
            <div class="infinite-scroll-spinner"></div>
            <p>Loading more...</p>
        `;
        this.loadingElement.style.display = 'none';

        // Load first page
        this.loadMore();
    }

    updateParams(newParams) {
        this.params = { ...this.params, ...newParams };
        this.reset();
    }

    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }

        if (this.loadingElement && this.loadingElement.parentNode) {
            this.loadingElement.parentNode.removeChild(this.loadingElement);
        }
    }
}

// Specialized infinite scroll classes for different content types

class MessageInfiniteScroll extends InfiniteScroll {
    constructor(options = {}) {
        super({
            ...options,
            endpoint: options.endpoint || '/api/messages/',
            itemSelector: '.message-item'
        });
    }

    createItemElement(message) {
        const element = document.createElement('div');
        element.className = 'message-item scroll-item';
        element.setAttribute('data-message-id', message.id);

        element.innerHTML = `
            <div class="message-avatar">
                <img src="${message.sender.avatar || '/static/img/default-avatar.png'}"
                     alt="${message.sender.name}"
                     class="avatar-img">
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${message.sender.name}</span>
                    <span class="message-time">${this.formatTime(message.timestamp)}</span>
                </div>
                <div class="message-text">${this.escapeHtml(message.content)}</div>
                ${message.attachments ? this.renderAttachments(message.attachments) : ''}
            </div>
        `;

        return element;
    }

    renderAttachments(attachments) {
        return `
            <div class="message-attachments">
                ${attachments.map(attachment => `
                    <div class="attachment-item">
                        <span class="material-symbols-outlined">${this.getAttachmentIcon(attachment.type)}</span>
                        <a href="${attachment.url}" target="_blank">${attachment.name}</a>
                    </div>
                `).join('')}
            </div>
        `;
    }

    getAttachmentIcon(type) {
        const icons = {
            'image': 'image',
            'video': 'videocam',
            'audio': 'audiotrack',
            'document': 'description',
            'pdf': 'picture_as_pdf'
        };
        return icons[type] || 'attach_file';
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

class UserInfiniteScroll extends InfiniteScroll {
    constructor(options = {}) {
        super({
            ...options,
            endpoint: options.endpoint || '/api/users/',
            itemSelector: '.user-item'
        });
    }

    createItemElement(user) {
        const element = document.createElement('div');
        element.className = 'user-item scroll-item';
        element.setAttribute('data-user-id', user.id);

        element.innerHTML = `
            <div class="user-avatar">
                <img src="${user.avatar || '/static/img/default-avatar.png'}"
                     alt="${user.name}"
                     class="avatar-img">
            </div>
            <div class="user-info">
                <div class="user-name">${user.name}</div>
                <div class="user-role">${user.role}</div>
                <div class="user-status ${user.is_online ? 'online' : 'offline'}">
                    <span class="status-dot"></span>
                    ${user.is_online ? 'Online' : 'Offline'}
                </div>
            </div>
            <div class="user-actions">
                <button class="btn-primary send-message-btn" data-user-id="${user.id}">
                    <span class="material-symbols-outlined">chat</span>
                    Message
                </button>
            </div>
        `;

        // Add event listeners
        const messageBtn = element.querySelector('.send-message-btn');
        messageBtn.addEventListener('click', () => {
            this.startConversation(user.id);
        });

        return element;
    }

    startConversation(userId) {
        // Implement conversation starting logic
        console.log('Starting conversation with user:', userId);
        // This would typically open a chat modal or navigate to chat page
    }
}

class ResourceInfiniteScroll extends InfiniteScroll {
    constructor(options = {}) {
        super({
            ...options,
            endpoint: options.endpoint || '/api/resources/',
            itemSelector: '.resource-item'
        });
    }

    createItemElement(resource) {
        const element = document.createElement('div');
        element.className = 'resource-item scroll-item resource-card';
        element.setAttribute('data-resource-id', resource.id);

        element.innerHTML = `
            <div class="resource-header">
                <div class="resource-type-badge ${resource.type}">${resource.type}</div>
                <h3 class="resource-title">
                    <a href="/resources/${resource.id}/">${resource.title}</a>
                </h3>
            </div>
            <div class="resource-content">
                <p class="resource-description">${resource.description}</p>
                <div class="resource-meta">
                    <span class="resource-author">By ${resource.author}</span>
                    <span class="resource-date">${this.formatDate(resource.created_at)}</span>
                    <span class="resource-views">${resource.views} views</span>
                </div>
                <div class="resource-tags">
                    ${resource.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
            <div class="resource-actions">
                <a href="/resources/${resource.id}/" class="btn-secondary">Read More</a>
                <button class="btn-primary save-resource-btn" data-resource-id="${resource.id}">
                    <span class="material-symbols-outlined">bookmark</span>
                    Save
                </button>
            </div>
        `;

        // Add event listeners
        const saveBtn = element.querySelector('.save-resource-btn');
        saveBtn.addEventListener('click', () => {
            this.saveResource(resource.id);
        });

        return element;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    saveResource(resourceId) {
        // Implement save resource logic
        console.log('Saving resource:', resourceId);
        // This would typically make an API call to save the resource
    }
}

// Utility functions for initializing infinite scroll on different pages

function initializeMessageInfiniteScroll(container, endpoint) {
    return new MessageInfiniteScroll({
        container: container || '.messages-container',
        endpoint: endpoint || '/api/messages/'
    });
}

function initializeUserInfiniteScroll(container, endpoint) {
    return new UserInfiniteScroll({
        container: container || '.users-container',
        endpoint: endpoint || '/api/users/'
    });
}

function initializeResourceInfiniteScroll(container, endpoint) {
    return new ResourceInfiniteScroll({
        container: container || '.resources-container',
        endpoint: endpoint || '/api/resources/'
    });
}

// Auto-initialize based on page content
document.addEventListener('DOMContentLoaded', function() {
    // Initialize based on page content
    if (document.querySelector('.messages-container')) {
        window.messageInfiniteScroll = initializeMessageInfiniteScroll();
    }

    if (document.querySelector('.users-container')) {
        window.userInfiniteScroll = initializeUserInfiniteScroll();
    }

    if (document.querySelector('.resources-container')) {
        window.resourceInfiniteScroll = initializeResourceInfiniteScroll();
    }
});

// Export for global use
window.InfiniteScroll = InfiniteScroll;
window.MessageInfiniteScroll = MessageInfiniteScroll;
window.UserInfiniteScroll = UserInfiniteScroll;
window.ResourceInfiniteScroll = ResourceInfiniteScroll;
window.initializeMessageInfiniteScroll = initializeMessageInfiniteScroll;
window.initializeUserInfiniteScroll = initializeUserInfiniteScroll;
window.initializeResourceInfiniteScroll = initializeResourceInfiniteScroll;