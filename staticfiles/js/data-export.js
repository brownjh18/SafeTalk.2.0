// Data Export Functionality (CSV, PDF) for User Data
class DataExporter {
    constructor() {
        this.exportFormats = ['csv', 'pdf', 'json'];
        this.init();
    }

    init() {
        this.bindExportButtons();
        this.initializeExportModal();
    }

    bindExportButtons() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.export-btn, .export-data-btn')) {
                e.preventDefault();
                const format = e.target.dataset.format || 'csv';
                const dataType = e.target.dataset.type || 'current-view';
                this.showExportModal(format, dataType, e.target);
            }
        });
    }

    initializeExportModal() {
        // Create export modal if it doesn't exist
        if (!document.querySelector('.export-modal')) {
            const modal = document.createElement('div');
            modal.className = 'export-modal modal-overlay';
            modal.innerHTML = `
                <div class="modal-content export-modal-content">
                    <div class="modal-header">
                        <h3>Export Data</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="export-options">
                            <div class="export-format-selection">
                                <label>Export Format:</label>
                                <div class="format-buttons">
                                    <button class="format-btn active" data-format="csv">
                                        <span class="material-symbols-outlined">table_chart</span>
                                        CSV
                                    </button>
                                    <button class="format-btn" data-format="pdf">
                                        <span class="material-symbols-outlined">picture_as_pdf</span>
                                        PDF
                                    </button>
                                    <button class="format-btn" data-format="json">
                                        <span class="material-symbols-outlined">data_object</span>
                                        JSON
                                    </button>
                                </div>
                            </div>

                            <div class="export-range-selection">
                                <label>Export Range:</label>
                                <div class="range-buttons">
                                    <button class="range-btn active" data-range="current-view">
                                        <span class="material-symbols-outlined">visibility</span>
                                        Current View
                                    </button>
                                    <button class="range-btn" data-range="all-data">
                                        <span class="material-symbols-outlined">select_all</span>
                                        All Data
                                    </button>
                                    <button class="range-btn" data-range="date-range">
                                        <span class="material-symbols-outlined">date_range</span>
                                        Date Range
                                    </button>
                                </div>
                            </div>

                            <div class="date-range-options" style="display: none;">
                                <div class="form-group">
                                    <label for="export-start-date">Start Date:</label>
                                    <input type="date" id="export-start-date" class="form-control">
                                </div>
                                <div class="form-group">
                                    <label for="export-end-date">End Date:</label>
                                    <input type="date" id="export-end-date" class="form-control">
                                </div>
                            </div>

                            <div class="export-columns" style="display: none;">
                                <label>Columns to Export:</label>
                                <div class="columns-list">
                                    <!-- Dynamically populated -->
                                </div>
                            </div>
                        </div>

                        <div class="export-preview" style="display: none;">
                            <h4>Export Preview</h4>
                            <div class="preview-content">
                                <!-- Preview content will be shown here -->
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary cancel-export">Cancel</button>
                        <button class="btn-primary start-export">
                            <span class="material-symbols-outlined">download</span>
                            Export Data
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            this.bindModalEvents(modal);
        }
    }

    showExportModal(format, dataType, triggerElement) {
        const modal = document.querySelector('.export-modal');
        this.currentTrigger = triggerElement;
        this.selectedFormat = format;
        this.selectedDataType = dataType;

        // Update modal based on trigger element data
        this.updateModalForDataType(dataType);

        // Show modal
        modal.style.display = 'flex';
        modal.classList.add('show');

        // Focus management
        setTimeout(() => {
            modal.querySelector('.format-btn.active').focus();
        }, 100);
    }

    updateModalForDataType(dataType) {
        const modal = document.querySelector('.export-modal');
        const columnsSection = modal.querySelector('.export-columns');

        // Show/hide columns selection based on data type
        if (dataType === 'mood-history' || dataType === 'appointments' || dataType === 'messages') {
            this.populateColumnsForDataType(dataType);
            columnsSection.style.display = 'block';
        } else {
            columnsSection.style.display = 'none';
        }

        // Update range options
        const rangeButtons = modal.querySelectorAll('.range-btn');
        rangeButtons.forEach(btn => {
            if (btn.dataset.range === 'current-view') {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    populateColumnsForDataType(dataType) {
        const columnsList = document.querySelector('.columns-list');
        let columns = [];

        switch (dataType) {
            case 'mood-history':
                columns = [
                    { id: 'date', label: 'Date', checked: true },
                    { id: 'mood_level', label: 'Mood Level', checked: true },
                    { id: 'notes', label: 'Notes', checked: true },
                    { id: 'activities', label: 'Activities', checked: false },
                    { id: 'location', label: 'Location', checked: false }
                ];
                break;
            case 'appointments':
                columns = [
                    { id: 'date', label: 'Date', checked: true },
                    { id: 'time', label: 'Time', checked: true },
                    { id: 'counselor', label: 'Counselor', checked: true },
                    { id: 'type', label: 'Type', checked: true },
                    { id: 'status', label: 'Status', checked: true },
                    { id: 'notes', label: 'Notes', checked: false }
                ];
                break;
            case 'messages':
                columns = [
                    { id: 'timestamp', label: 'Timestamp', checked: true },
                    { id: 'sender', label: 'Sender', checked: true },
                    { id: 'recipient', label: 'Recipient', checked: true },
                    { id: 'content', label: 'Content', checked: true },
                    { id: 'type', label: 'Type', checked: false }
                ];
                break;
        }

        columnsList.innerHTML = columns.map(col => `
            <label class="column-checkbox">
                <input type="checkbox" value="${col.id}" ${col.checked ? 'checked' : ''}>
                <span class="checkmark"></span>
                ${col.label}
            </label>
        `).join('');
    }

    bindModalEvents(modal) {
        // Close modal
        const closeBtn = modal.querySelector('.modal-close');
        const cancelBtn = modal.querySelector('.cancel-export');

        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                this.hideExportModal();
            });
        });

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideExportModal();
            }
        });

        // Format selection
        modal.querySelectorAll('.format-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedFormat = btn.dataset.format;
            });
        });

        // Range selection
        modal.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedRange = btn.dataset.range;

                // Show/hide date range options
                const dateRangeOptions = modal.querySelector('.date-range-options');
                dateRangeOptions.style.display = this.selectedRange === 'date-range' ? 'block' : 'none';
            });
        });

        // Start export
        const startBtn = modal.querySelector('.start-export');
        startBtn.addEventListener('click', () => {
            this.startExport();
        });

        // Keyboard navigation
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideExportModal();
            }
        });
    }

    hideExportModal() {
        const modal = document.querySelector('.export-modal');
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }

    async startExport() {
        const modal = document.querySelector('.export-modal');
        const startBtn = modal.querySelector('.start-export');

        // Get export options
        const options = {
            format: this.selectedFormat,
            range: this.selectedRange,
            columns: this.getSelectedColumns(),
            dateRange: this.getDateRange()
        };

        // Show loading state
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="spinner"></span> Exporting...';

        try {
            const data = await this.gatherData(options);
            const blob = await this.generateExportFile(data, options.format, options.columns);

            this.downloadFile(blob, this.generateFileName(options));
            showNotification('Export completed successfully!', 'success');

            this.hideExportModal();
        } catch (error) {
            console.error('Export failed:', error);
            showNotification('Export failed. Please try again.', 'error');
        } finally {
            // Reset button
            startBtn.disabled = false;
            startBtn.innerHTML = `
                <span class="material-symbols-outlined">download</span>
                Export Data
            `;
        }
    }

    getSelectedColumns() {
        const checkboxes = document.querySelectorAll('.column-checkbox input:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    getDateRange() {
        if (this.selectedRange !== 'date-range') return null;

        const startDate = document.getElementById('export-start-date').value;
        const endDate = document.getElementById('export-end-date').value;

        return { start: startDate, end: endDate };
    }

    async gatherData(options) {
        let data = [];

        if (options.range === 'current-view') {
            // Export currently visible data
            data = this.gatherCurrentViewData();
        } else if (options.range === 'all-data') {
            // Fetch all data from API
            data = await this.fetchAllData(this.selectedDataType);
        } else if (options.range === 'date-range') {
            // Fetch data within date range
            data = await this.fetchDataByDateRange(this.selectedDataType, options.dateRange);
        }

        return data;
    }

    gatherCurrentViewData() {
        // Gather data from currently visible elements
        const items = document.querySelectorAll('.data-item, .list-item, tr[data-item]');
        return Array.from(items).map(item => {
            const data = {};
            // Extract data attributes or text content
            Object.keys(item.dataset).forEach(key => {
                data[key] = item.dataset[key];
            });
            return data;
        });
    }

    async fetchAllData(dataType) {
        try {
            const response = await fetch(`/api/export/${dataType}/`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch data:', error);
            throw error;
        }
    }

    async fetchDataByDateRange(dataType, dateRange) {
        try {
            const params = new URLSearchParams({
                start_date: dateRange.start,
                end_date: dateRange.end
            });
            const response = await fetch(`/api/export/${dataType}/?${params}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch data by date range:', error);
            throw error;
        }
    }

    async generateExportFile(data, format, columns) {
        switch (format) {
            case 'csv':
                return this.generateCSV(data, columns);
            case 'pdf':
                return await this.generatePDF(data, columns);
            case 'json':
                return this.generateJSON(data);
            default:
                throw new Error(`Unsupported format: ${format}`);
        }
    }

    generateCSV(data, columns) {
        if (!data || data.length === 0) {
            throw new Error('No data to export');
        }

        // Filter columns if specified
        let exportData = data;
        if (columns && columns.length > 0) {
            exportData = data.map(item => {
                const filtered = {};
                columns.forEach(col => {
                    if (item.hasOwnProperty(col)) {
                        filtered[col] = item[col];
                    }
                });
                return filtered;
            });
        }

        // Generate CSV content
        const headers = Object.keys(exportData[0]);
        const csvContent = [
            headers.join(','),
            ...exportData.map(row =>
                headers.map(header => {
                    const value = row[header] || '';
                    // Escape commas and quotes
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                }).join(',')
            )
        ].join('\n');

        return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    }

    async generatePDF(data, columns) {
        // For PDF generation, we'll use a simple HTML-to-PDF approach
        // In a real implementation, you might want to use a library like jsPDF or Puppeteer

        let html = `
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f5f5f5; font-weight: bold; }
                    h1 { color: #333; }
                    .export-info { margin-bottom: 20px; color: #666; }
                </style>
            </head>
            <body>
                <h1>Data Export</h1>
                <div class="export-info">
                    <p>Exported on: ${new Date().toLocaleString()}</p>
                    <p>Total records: ${data.length}</p>
                </div>
                <table>
        `;

        if (data.length > 0) {
            const headers = columns && columns.length > 0 ? columns : Object.keys(data[0]);

            html += '<thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '</tr></thead><tbody>';

            data.forEach(row => {
                html += '<tr>';
                headers.forEach(header => {
                    const value = row[header] || '';
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
        }

        html += '</body></html>';

        // Convert HTML to blob
        return new Blob([html], { type: 'text/html;charset=utf-8;' });
    }

    generateJSON(data) {
        const jsonContent = JSON.stringify(data, null, 2);
        return new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    }

    generateFileName(options) {
        const timestamp = new Date().toISOString().split('T')[0];
        const dataType = this.selectedDataType.replace('-', '_');
        const format = options.format.toUpperCase();

        return `safetalk_${dataType}_export_${timestamp}.${options.format}`;
    }

    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Utility functions for specific data types
function exportMoodHistory(options = {}) {
    const exporter = new DataExporter();
    exporter.selectedDataType = 'mood-history';
    return exporter.startExport();
}

function exportAppointments(options = {}) {
    const exporter = new DataExporter();
    exporter.selectedDataType = 'appointments';
    return exporter.startExport();
}

function exportMessages(options = {}) {
    const exporter = new DataExporter();
    exporter.selectedDataType = 'messages';
    return exporter.startExport();
}

function exportUserProfile(options = {}) {
    const exporter = new DataExporter();
    exporter.selectedDataType = 'user-profile';
    return exporter.startExport();
}

// Initialize data exporter
document.addEventListener('DOMContentLoaded', function() {
    window.dataExporter = new DataExporter();
});

// Export for global use
window.DataExporter = DataExporter;
window.exportMoodHistory = exportMoodHistory;
window.exportAppointments = exportAppointments;
window.exportMessages = exportMessages;
window.exportUserProfile = exportUserProfile;