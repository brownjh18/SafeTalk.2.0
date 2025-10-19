// Advanced Search and Filtering Capabilities
class SearchFilterSystem {
    constructor() {
        this.searchTimeout = null;
        this.currentFilters = {};
        this.searchHistory = [];
        this.init();
    }

    init() {
        this.initializeSearchInputs();
        this.initializeFilters();
        this.loadSearchHistory();
        this.bindKeyboardShortcuts();
    }

    initializeSearchInputs() {
        const searchInputs = document.querySelectorAll('.search-input, .global-search, #global-search');

        searchInputs.forEach(input => {
            // Debounced search
            input.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                const query = e.target.value.trim();

                this.searchTimeout = setTimeout(() => {
                    this.performSearch(query, e.target);
                }, 300);
            });

            // Search on Enter
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const query = e.target.value.trim();
                    this.performInstantSearch(query, e.target);
                }

                // Arrow keys for search suggestions
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    this.navigateSuggestions(e, e.target);
                }
            });

            // Clear search on Escape
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.clearSearch(input);
                }
            });

            // Show search history on focus
            input.addEventListener('focus', () => {
                if (input.value.trim() === '') {
                    this.showSearchHistory(input);
                }
            });

            // Hide suggestions on blur
            input.addEventListener('blur', () => {
                setTimeout(() => this.hideSuggestions(input), 200);
            });
        });
    }

    initializeFilters() {
        // Initialize filter dropdowns
        const filterSelects = document.querySelectorAll('.filter-select, .search-filter');

        filterSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                this.applyFilter(e.target.name, e.target.value);
            });
        });

        // Initialize filter buttons
        const filterButtons = document.querySelectorAll('.filter-btn');

        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                const filterType = button.dataset.filter;
                const filterValue = button.dataset.value;
                const isActive = button.classList.contains('active');

                if (isActive) {
                    this.removeFilter(filterType);
                    button.classList.remove('active');
                } else {
                    this.applyFilter(filterType, filterValue);
                    button.classList.add('active');
                }
            });
        });

        // Initialize date range filters
        this.initializeDateFilters();

        // Initialize range sliders
        this.initializeRangeFilters();
    }

    initializeDateFilters() {
        const dateInputs = document.querySelectorAll('.date-filter');

        dateInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const filterName = e.target.name;
                const value = e.target.value;

                if (filterName.includes('start')) {
                    this.currentFilters[`${filterName.replace('_start', '')}_range`] = {
                        ...this.currentFilters[`${filterName.replace('_start', '')}_range`],
                        start: value
                    };
                } else if (filterName.includes('end')) {
                    this.currentFilters[`${filterName.replace('_end', '')}_range`] = {
                        ...this.currentFilters[`${filterName.replace('_end', '')}_range`],
                        end: value
                    };
                }

                this.applyFilters();
            });
        });
    }

    initializeRangeFilters() {
        const rangeInputs = document.querySelectorAll('.range-filter');

        rangeInputs.forEach(input => {
            const display = document.getElementById(`${input.id}-display`);

            input.addEventListener('input', (e) => {
                if (display) {
                    display.textContent = e.target.value;
                }

                this.applyFilter(e.target.name, e.target.value);
            });
        });
    }

    performSearch(query, input) {
        if (query.length === 0) {
            this.clearSearchResults(input);
            return;
        }

        // Show loading state
        this.showSearchLoading(input);

        // Perform search based on context
        const context = this.getSearchContext(input);

        switch (context) {
            case 'global':
                this.performGlobalSearch(query, input);
                break;
            case 'users':
                this.performUserSearch(query, input);
                break;
            case 'messages':
                this.performMessageSearch(query, input);
                break;
            case 'resources':
                this.performResourceSearch(query, input);
                break;
            default:
                this.performGenericSearch(query, input);
        }

        // Save to search history
        this.saveToSearchHistory(query);
    }

    performInstantSearch(query, input) {
        clearTimeout(this.searchTimeout);
        this.performSearch(query, input);
    }

    getSearchContext(input) {
        const container = input.closest('[data-search-context]');
        return container ? container.dataset.searchContext : 'global';
    }

    async performGlobalSearch(query, input) {
        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
            const results = await response.json();

            this.displayGlobalSearchResults(results, input);
        } catch (error) {
            console.error('Search failed:', error);
            this.showSearchError('Search failed. Please try again.', input);
        }
    }

    async performUserSearch(query, input) {
        try {
            const response = await fetch(`/api/users/search/?q=${encodeURIComponent(query)}`);
            const users = await response.json();

            this.displayUserSearchResults(users, input);
        } catch (error) {
            console.error('User search failed:', error);
            this.showSearchError('User search failed.', input);
        }
    }

    async performMessageSearch(query, input) {
        try {
            const response = await fetch(`/api/messages/search/?q=${encodeURIComponent(query)}`);
            const messages = await response.json();

            this.displayMessageSearchResults(messages, input);
        } catch (error) {
            console.error('Message search failed:', error);
            this.showSearchError('Message search failed.', input);
        }
    }

    async performResourceSearch(query, input) {
        try {
            const response = await fetch(`/api/resources/search/?q=${encodeURIComponent(query)}`);
            const resources = await response.json();

            this.displayResourceSearchResults(resources, input);
        } catch (error) {
            console.error('Resource search failed:', error);
            this.showSearchError('Resource search failed.', input);
        }
    }

    performGenericSearch(query, input) {
        // Fallback for generic search
        const results = this.searchInDOM(query, input);
        this.displayGenericSearchResults(results, input);
    }

    searchInDOM(query, input) {
        const container = input.closest('.search-container') || document.body;
        const elements = container.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, td, th, .card-title, .card-text');

        const results = [];
        const queryLower = query.toLowerCase();

        elements.forEach(element => {
            const text = element.textContent.toLowerCase();
            if (text.includes(queryLower)) {
                results.push({
                    element: element,
                    text: element.textContent,
                    type: element.tagName.toLowerCase()
                });
            }
        });

        return results;
    }

    displayGlobalSearchResults(results, input) {
        const suggestions = this.getSuggestionsContainer(input);

        if (!results || results.length === 0) {
            suggestions.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }

        const html = results.map(result => `
            <a href="${result.url}" class="search-result-item">
                <div class="result-icon">
                    <span class="material-symbols-outlined">${this.getResultIcon(result.type)}</span>
                </div>
                <div class="result-content">
                    <div class="result-title">${this.highlightQuery(result.title, input.value)}</div>
                    <div class="result-subtitle">${result.subtitle || ''}</div>
                </div>
            </a>
        `).join('');

        suggestions.innerHTML = html;
        suggestions.classList.remove('hidden');
    }

    displayUserSearchResults(users, input) {
        const suggestions = this.getSuggestionsContainer(input);

        if (!users || users.length === 0) {
            suggestions.innerHTML = '<div class="no-results">No users found</div>';
            return;
        }

        const html = users.map(user => `
            <a href="/users/${user.id}/" class="search-result-item">
                <div class="result-icon">
                    <span class="material-symbols-outlined">person</span>
                </div>
                <div class="result-content">
                    <div class="result-title">${this.highlightQuery(user.name, input.value)}</div>
                    <div class="result-subtitle">${user.role}</div>
                </div>
            </a>
        `).join('');

        suggestions.innerHTML = html;
        suggestions.classList.remove('hidden');
    }

    displayMessageSearchResults(messages, input) {
        const container = input.closest('.search-container');
        const resultsContainer = container.querySelector('.search-results') || container;

        if (!messages || messages.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No messages found</div>';
            return;
        }

        const html = messages.map(message => `
            <div class="message-result">
                <div class="message-header">
                    <span class="message-author">${message.author}</span>
                    <span class="message-time">${this.formatTime(message.timestamp)}</span>
                </div>
                <div class="message-content">${this.highlightQuery(message.content, input.value)}</div>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    displayResourceSearchResults(resources, input) {
        const container = input.closest('.search-container');
        const resultsContainer = container.querySelector('.search-results') || container;

        if (!resources || resources.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No resources found</div>';
            return;
        }

        const html = resources.map(resource => `
            <div class="resource-result">
                <div class="resource-header">
                    <span class="resource-type">${resource.type}</span>
                    <span class="resource-category">${resource.category}</span>
                </div>
                <h4 class="resource-title">${this.highlightQuery(resource.title, input.value)}</h4>
                <p class="resource-description">${this.highlightQuery(resource.description, input.value)}</p>
                <a href="/resources/${resource.id}/" class="resource-link">View Resource</a>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    displayGenericSearchResults(results, input) {
        const container = input.closest('.search-container');
        const resultsContainer = container.querySelector('.search-results') || container;

        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }

        const html = results.map(result => `
            <div class="generic-result" data-element="${result.element.tagName}">
                <span class="result-type">${result.type}</span>
                <span class="result-text">${this.highlightQuery(result.text, input.value)}</span>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    highlightQuery(text, query) {
        if (!query) return text;

        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    getResultIcon(type) {
        const icons = {
            user: 'person',
            message: 'chat',
            resource: 'menu_book',
            appointment: 'calendar_today',
            page: 'web',
            default: 'search'
        };
        return icons[type] || icons.default;
    }

    getSuggestionsContainer(input) {
        let suggestions = input.parentNode.querySelector('.search-suggestions');

        if (!suggestions) {
            suggestions = document.createElement('div');
            suggestions.className = 'search-suggestions hidden';
            input.parentNode.appendChild(suggestions);
        }

        return suggestions;
    }

    showSearchLoading(input) {
        const suggestions = this.getSuggestionsContainer(input);
        suggestions.innerHTML = '<div class="search-loading">Searching...</div>';
        suggestions.classList.remove('hidden');
    }

    showSearchError(message, input) {
        const suggestions = this.getSuggestionsContainer(input);
        suggestions.innerHTML = `<div class="search-error">${message}</div>`;
        suggestions.classList.remove('hidden');
    }

    clearSearchResults(input) {
        const suggestions = this.getSuggestionsContainer(input);
        suggestions.classList.add('hidden');
    }

    clearSearch(input) {
        input.value = '';
        this.clearSearchResults(input);
        input.focus();
    }

    navigateSuggestions(e, input) {
        const suggestions = this.getSuggestionsContainer(input);
        const items = suggestions.querySelectorAll('.search-result-item, .search-suggestion-item');

        if (items.length === 0) return;

        let currentIndex = -1;
        items.forEach((item, index) => {
            if (item.classList.contains('highlighted')) {
                currentIndex = index;
                item.classList.remove('highlighted');
            }
        });

        if (e.key === 'ArrowDown') {
            currentIndex = Math.min(currentIndex + 1, items.length - 1);
        } else if (e.key === 'ArrowUp') {
            currentIndex = Math.max(currentIndex - 1, -1);
        }

        if (currentIndex >= 0) {
            items[currentIndex].classList.add('highlighted');
        }
    }

    hideSuggestions(input) {
        const suggestions = this.getSuggestionsContainer(input);
        suggestions.classList.add('hidden');
    }

    applyFilter(name, value) {
        if (value === '' || value === 'all') {
            delete this.currentFilters[name];
        } else {
            this.currentFilters[name] = value;
        }

        this.applyFilters();
    }

    removeFilter(name) {
        delete this.currentFilters[name];
        this.applyFilters();
    }

    applyFilters() {
        // Update URL with filters
        this.updateURLWithFilters();

        // Apply filters to current view
        this.filterCurrentView();

        // Update filter UI
        this.updateFilterUI();
    }

    updateURLWithFilters() {
        const url = new URL(window.location);

        // Clear existing filter params
        Array.from(url.searchParams.keys()).forEach(key => {
            if (key.startsWith('filter_')) {
                url.searchParams.delete(key);
            }
        });

        // Add current filters
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (typeof value === 'object') {
                // Handle range filters
                if (value.start) url.searchParams.set(`filter_${key}_start`, value.start);
                if (value.end) url.searchParams.set(`filter_${key}_end`, value.end);
            } else {
                url.searchParams.set(`filter_${key}`, value);
            }
        });

        // Update URL without reloading
        window.history.replaceState({}, '', url);
    }

    filterCurrentView() {
        const items = document.querySelectorAll('.filterable-item, .card, .list-item, tr[data-item]');

        items.forEach(item => {
            let visible = true;

            Object.entries(this.currentFilters).forEach(([filterName, filterValue]) => {
                const itemValue = item.dataset[filterName];

                if (itemValue) {
                    if (typeof filterValue === 'object') {
                        // Range filter
                        if (filterValue.start && itemValue < filterValue.start) visible = false;
                        if (filterValue.end && itemValue > filterValue.end) visible = false;
                    } else {
                        // Exact match filter
                        if (itemValue !== filterValue) visible = false;
                    }
                }
            });

            item.style.display = visible ? '' : 'none';
        });

        // Update results count
        this.updateResultsCount();
    }

    updateFilterUI() {
        // Update active filter indicators
        document.querySelectorAll('.filter-indicator').forEach(indicator => {
            indicator.remove();
        });

        Object.entries(this.currentFilters).forEach(([name, value]) => {
            const filterContainer = document.querySelector(`[data-filter-name="${name}"]`) ||
                                  document.querySelector('.active-filters');

            if (filterContainer) {
                const indicator = document.createElement('span');
                indicator.className = 'filter-indicator';
                indicator.innerHTML = `
                    <span class="filter-label">${name}: ${value}</span>
                    <button class="filter-remove" data-filter="${name}">&times;</button>
                `;

                filterContainer.appendChild(indicator);
            }
        });

        // Add event listeners to remove buttons
        document.querySelectorAll('.filter-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filterName = e.target.dataset.filter;
                this.removeFilter(filterName);
            });
        });
    }

    updateResultsCount() {
        const visibleItems = document.querySelectorAll('.filterable-item:not([style*="display: none"]), .card:not([style*="display: none"]), .list-item:not([style*="display: none"]), tr[data-item]:not([style*="display: none"])');
        const totalItems = document.querySelectorAll('.filterable-item, .card, .list-item, tr[data-item]').length;

        const countElement = document.querySelector('.results-count');
        if (countElement) {
            countElement.textContent = `Showing ${visibleItems.length} of ${totalItems} results`;
        }
    }

    saveToSearchHistory(query) {
        if (!query.trim()) return;

        // Remove if already exists
        this.searchHistory = this.searchHistory.filter(item => item !== query);

        // Add to beginning
        this.searchHistory.unshift(query);

        // Limit history size
        if (this.searchHistory.length > 10) {
            this.searchHistory = this.searchHistory.slice(0, 10);
        }

        // Save to localStorage
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
    }

    loadSearchHistory() {
        try {
            const history = localStorage.getItem('searchHistory');
            if (history) {
                this.searchHistory = JSON.parse(history);
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }

    showSearchHistory(input) {
        if (this.searchHistory.length === 0) return;

        const suggestions = this.getSuggestionsContainer(input);
        const html = `
            <div class="search-history-header">
                <span>Recent searches</span>
                <button class="clear-history-btn">Clear</button>
            </div>
            ${this.searchHistory.map(query => `
                <div class="search-history-item" data-query="${query}">
                    <span class="material-symbols-outlined">history</span>
                    <span>${query}</span>
                </div>
            `).join('')}
        `;

        suggestions.innerHTML = html;
        suggestions.classList.remove('hidden');

        // Add event listeners
        suggestions.querySelectorAll('.search-history-item').forEach(item => {
            item.addEventListener('click', () => {
                const query = item.dataset.query;
                input.value = query;
                this.performInstantSearch(query, input);
            });
        });

        suggestions.querySelector('.clear-history-btn')?.addEventListener('click', () => {
            this.clearSearchHistory();
            this.hideSuggestions(input);
        });
    }

    clearSearchHistory() {
        this.searchHistory = [];
        localStorage.removeItem('searchHistory');
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.global-search, #global-search, .search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Ctrl/Cmd + F for filter panel
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                this.toggleFilterPanel();
            }
        });
    }

    toggleFilterPanel() {
        const panel = document.querySelector('.filter-panel, .advanced-filters');
        if (panel) {
            panel.classList.toggle('show');
        }
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
}

// Initialize search and filter system
const searchFilterSystem = new SearchFilterSystem();

// Export for global use
window.SearchFilterSystem = SearchFilterSystem;
window.searchFilterSystem = searchFilterSystem;