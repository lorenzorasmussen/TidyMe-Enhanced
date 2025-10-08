// TidyMe Web UI JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadActivityLog();
    loadAIInsights();
    checkDaemonStatus();
    loadSystemHealth();
    checkAutoMonitoringStatus();
    loadProcessingStatus();
    loadTaskQueue(); // Load task queue on page load

    // Initialize expandable buttons
    initializeExpandableButtons();

    // Auto-refresh task queue every 30 seconds
    setInterval(loadTaskQueue, 30000);
});

// Expandable Button Functionality
function initializeExpandableButtons() {
    const expandableButtons = document.querySelectorAll('.expandable-btn');

    expandableButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Don't trigger if clicking on a child element that should handle its own click
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'LABEL') {
                return;
            }

            e.preventDefault();
            toggleExpandableButton(this);
        });
    });
}

function toggleExpandableButton(button) {
    const expandableButton = button.closest('.expandable-button');
    const content = expandableButton.querySelector('.expandable-content');

    if (button.classList.contains('expanded')) {
        // Collapse
        button.classList.remove('expanded');
        content.classList.remove('expanded');
    } else {
        // Expand
        button.classList.add('expanded');
        content.classList.add('expanded');
    }
}

// Function to programmatically expand a button by index
function expandButtonByIndex(sectionClass, buttonIndex) {
    const section = document.querySelector(sectionClass);
    if (!section) return;

    const buttons = section.querySelectorAll('.expandable-btn');
    if (buttons[buttonIndex]) {
        toggleExpandableButton(buttons[buttonIndex]);
    }
}

// Function to collapse all expandable buttons in a section
function collapseAllButtons(sectionClass) {
    const section = document.querySelector(sectionClass);
    if (!section) return;

    const expandedButtons = section.querySelectorAll('.expandable-btn.expanded');
    expandedButtons.forEach(button => {
        toggleExpandableButton(button);
    });
}

// Function to expand all buttons in a section
function expandAllButtons(sectionClass) {
    const section = document.querySelector(sectionClass);
    if (!section) return;

    const buttons = section.querySelectorAll('.expandable-btn:not(.expanded)');
    buttons.forEach(button => {
        toggleExpandableButton(button);
    });
}

// Task Management Functions
async function loadTaskQueue() {
    try {
        const response = await fetch('/api/tasks/queue');
        const data = await response.json();

        if (data.success) {
            updateTaskQueueDisplay(data.queue);
        }
    } catch (error) {
        console.error('Error loading task queue:', error);
    }
}

function updateTaskQueueDisplay(queueData) {
    const queueContainer = document.getElementById('task-queue-display');
    if (!queueContainer) return;

    let html = '<h3>📋 Task Queue Status</h3>';

    if (queueData.queue && queueData.queue.length > 0) {
        html += '<div class="task-list">';
        queueData.queue.forEach(task => {
            const statusClass = getTaskStatusClass(task.status);
            const statusIcon = getTaskStatusIcon(task.status);

            html += `
                <div class="task-item ${statusClass}">
                    <div class="task-header">
                        <span class="task-name">${task.name}</span>
                        <span class="task-status">${statusIcon} ${task.status}</span>
                    </div>
                    <div class="task-details">
                        <small>ID: ${task.id}</small>
                        ${task.dependencies && task.dependencies.length > 0 ?
                            `<small>Depends on: ${task.dependencies.join(', ')}</small>` : ''}
                        ${task.error ? `<small class="error">Error: ${task.error}</small>` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += '<p class="empty-queue">No tasks in queue</p>';
    }

    // Add queue statistics
    html += `
        <div class="queue-stats">
            <div class="stat-item">
                <span class="stat-label">Queued:</span>
                <span class="stat-value">${queueData.total_queued || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Running:</span>
                <span class="stat-value">${queueData.total_running || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Completed:</span>
                <span class="stat-value">${queueData.total_completed || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Failed:</span>
                <span class="stat-value">${queueData.total_failed || 0}</span>
            </div>
        </div>
    `;

    queueContainer.innerHTML = html;
}

function getTaskStatusClass(status) {
    switch (status) {
        case 'completed': return 'task-completed';
        case 'running': return 'task-running';
        case 'failed': return 'task-failed';
        case 'queued': return 'task-queued';
        case 'cancelled': return 'task-cancelled';
        default: return 'task-unknown';
    }
}

function getTaskStatusIcon(status) {
    switch (status) {
        case 'completed': return '✅';
        case 'running': return '🔄';
        case 'failed': return '❌';
        case 'queued': return '⏳';
        case 'cancelled': return '🚫';
        default: return '❓';
    }
}

async function createMaintenanceChain() {
    try {
        const response = await fetch('/api/tasks/maintenance-chain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification('✅ Maintenance chain created successfully!', 'success');
            loadTaskQueue(); // Refresh the queue display
        } else {
            showNotification('❌ Failed to create maintenance chain', 'error');
        }
    } catch (error) {
        console.error('Error creating maintenance chain:', error);
        showNotification('❌ Network error creating maintenance chain', 'error');
    }
}

async function cancelTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification(`✅ Task ${taskId} cancelled successfully!`, 'success');
            loadTaskQueue(); // Refresh the queue display
        } else {
            showNotification('❌ Failed to cancel task', 'error');
        }
    } catch (error) {
        console.error('Error cancelling task:', error);
        showNotification('❌ Network error cancelling task', 'error');
    }
}

// Browser Automation Functions
async function startBrowserCollection() {
    const resultsContainer = document.getElementById('results-container');

    try {
        resultsContainer.innerHTML = '<div class="loading"></div> Starting browser collection...';

        const response = await fetch('/api/browser/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                platforms: ['perplexity', 'chatgpt', 'claude'], // Default platforms
                headless: true
            })
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: #28a745; font-weight: bold;">✅ Browser collection completed!</div>
                <div class="collection-results">
                    <h4>Collection Summary:</h4>
                    <ul>
                        ${Object.entries(result.results || {}).map(([platform, data]) =>
                            `<li><strong>${platform}:</strong> ${data.success ? '✅ Success' : '❌ Failed'}</li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        } else {
            resultsContainer.innerHTML = `
                <div style="color: #dc3545; font-weight: bold;">❌ Browser collection failed</div>
                <p>${result.error || 'Unknown error'}</p>
            `;
        }

    } catch (error) {
        resultsContainer.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">❌ Network error</div>
            <p>${error.message}</p>
        `;
    }
}

async function testBrowserAutomation() {
    const resultsContainer = document.getElementById('results-container');

    try {
        resultsContainer.innerHTML = '<div class="loading"></div> Testing browser automation...';

        const response = await fetch('/api/browser/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: #28a745; font-weight: bold;">✅ Browser automation test successful!</div>
                <div class="test-results">
                    <p><strong>Page Title:</strong> ${result.page_title || 'N/A'}</p>
                    <p><strong>Content Found:</strong> ${result.content_found ? 'Yes' : 'No'}</p>
                    <p><strong>Response Time:</strong> ${result.response_time || 'N/A'}ms</p>
                </div>
            `;
        } else {
            resultsContainer.innerHTML = `
                <div style="color: #dc3545; font-weight: bold;">❌ Browser automation test failed</div>
                <p>${result.error || 'Unknown error'}</p>
            `;
        }

    } catch (error) {
        resultsContainer.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">❌ Network error</div>
            <p>${error.message}</p>
        `;
    }
}

// Notification System
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="notification-close">&times;</button>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.main-tab-btn');
    tabButtons.forEach(button => button.classList.remove('active'));

    // Show selected tab content
    const selectedContent = document.getElementById(tabName + '-content');
    if (selectedContent) {
        selectedContent.classList.add('active');
    }

    // Add active class to selected tab button
    const selectedButton = document.getElementById(tabName + '-tab');
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-space').textContent = formatBytes(data.total_space_cleaned);
        document.getElementById('duplicates-count').textContent = data.duplicate_files_found;
        document.getElementById('recent-scans').textContent = data.recent_scans;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load AI insights
async function loadAIInsights() {
    try {
        const response = await fetch('/api/ai/insights');
        const data = await response.json();

        const insightsContainer = document.getElementById('ai-insights');

        let html = '<div class="insights-section">';
        html += '<h3>Current Insights</h3>';
        html += '<ul>';
        data.insights.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
        html += '</ul>';

        html += '<h3>Recommendations</h3>';
        html += '<ul>';
        data.suggestions.forEach(suggestion => {
            html += `<li>${suggestion}</li>`;
        });
        html += '</ul>';
        html += '</div>';

        insightsContainer.innerHTML = html;
    } catch (error) {
        console.error('Error loading AI insights:', error);
        document.getElementById('ai-insights').innerHTML = '<p>Error loading AI insights.</p>';
    }
}

// Load recent activity log
async function loadActivityLog() {
    try {
        const response = await fetch('/api/cleanup-log');
        const logs = await response.json();

        const logContainer = document.getElementById('activity-log');

        if (logs.length === 0) {
            logContainer.innerHTML = '<p>No recent activity found.</p>';
            return;
        }

        logContainer.innerHTML = logs.map(log => `
            <div class="activity-item">
                <div>
                    <span class="activity-action">${log.action_type}</span>
                    <span class="activity-time">${new Date(log.action_date).toLocaleString()}</span>
                </div>
                <div class="${log.success ? 'success' : 'error'}">
                    ${log.success ? '✓' : '✗'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading activity log:', error);
        document.getElementById('activity-log').innerHTML = '<p>Error loading activity log.</p>';
    }
}

// Run cleanup action
async function runCleanup(action) {
    const resultsContainer = document.getElementById('results-container');
    const button = event.target;

    // Add loading overlay to results container
    resultsContainer.innerHTML = `
        <div class="loading-overlay">
            <div class="loading-card">
                <div class="loading loading-lg"></div>
                <p>Starting cleanup operation...</p>
            </div>
        </div>
    `;

    // Disable button and show loading
    button.disabled = true;
    button.innerHTML = '<div class="loading"></div> Running...';

    // Reset other buttons
    document.querySelectorAll('.btn').forEach(btn => {
        if (btn !== button) {
            btn.disabled = true;
        }
    });

    try {
        const response = await fetch(`/api/cleanup/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: #10b981; font-weight: bold; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">✅</span>
                    Operation completed successfully!
                </div>
                <div style="margin-top: 15px; background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #10b981;">
                    <pre style="margin: 0; background: transparent; padding: 0; border: none; white-space: pre-wrap; font-family: inherit;">${result.output || 'No output'}</pre>
                </div>
            `;
        } else {
            resultsContainer.innerHTML = `
                <div style="color: #ef4444; font-weight: bold; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">❌</span>
                    Operation failed
                </div>
                <div style="margin-top: 15px; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #ef4444;">
                    <pre style="margin: 0; background: transparent; padding: 0; border: none; white-space: pre-wrap; font-family: inherit; color: #ef4444;">${result.error || 'Unknown error'}</pre>
                </div>
            `;
        }

        // Refresh stats and activity log
        setTimeout(() => {
            loadStats();
            loadActivityLog();
        }, 1000);

    } catch (error) {
        resultsContainer.innerHTML = `
            <div style="color: #ef4444; font-weight: bold; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">🌐</span>
                Network error
            </div>
            <div style="margin-top: 15px; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #ef4444;">
                <p style="margin: 0; color: #ef4444;">${error.message}</p>
            </div>
        `;
    } finally {
        // Re-enable buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.disabled = false;
            // Reset button text
            const actionText = btn.onclick.toString().match(/'([^']+)'/);
            if (actionText) {
                const actionMap = {
                    'scan': '🔍 Scan for Duplicates',
                    'clean-cache': '🧠 Clean Cache',
                    'clean-temp': '🗑️ Clean Temp Files',
                    'clean-dev': '💻 Clean Dev Files',
                    'clean-all': '🚀 Complete Cleanup'
                };
                btn.innerHTML = actionMap[actionText[1]] || btn.innerHTML;
            }
        });
    }
}

// Format bytes to human readable format
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Check daemon status
async function checkDaemonStatus() {
    try {
        const response = await fetch('/api/daemon/status');
        const data = await response.json();
        const daemonBtn = document.getElementById('daemon-btn');

        if (data.running) {
            daemonBtn.innerHTML = '⏹️ Stop Daemon';
            daemonBtn.className = 'btn btn-danger';
        } else {
            daemonBtn.innerHTML = '▶️ Start Daemon';
            daemonBtn.className = 'btn btn-success';
        }
    } catch (error) {
        console.error('Error checking daemon status:', error);
    }
}

// Toggle daemon
async function toggleDaemon() {
    const daemonBtn = document.getElementById('daemon-btn');
    const isRunning = daemonBtn.innerHTML.includes('Stop');

    try {
        const action = isRunning ? 'daemon-stop' : 'daemon-start';
        const response = await fetch(`/api/cleanup/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            // Update button state
            setTimeout(() => {
                checkDaemonStatus();
                loadActivityLog();
            }, 1000);
        } else {
            alert('Failed to ' + (isRunning ? 'stop' : 'start') + ' daemon: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Show configuration
async function showConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        document.getElementById('config-content').textContent = JSON.stringify(data, null, 2);
        document.getElementById('config-modal').style.display = 'block';
    } catch (error) {
        alert('Error loading configuration: ' + error.message);
    }
}

// Close modal
function closeModal() {
    document.getElementById('config-modal').style.display = 'none';
}

// Show report
async function showReport(type) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(type + '-tab').classList.add('active');

    const reportContent = document.getElementById('report-content');

    try {
        let response, data;

        switch(type) {
            case 'scans':
                response = await fetch('/api/scans');
                data = await response.json();
                displayScansReport(data);
                break;
            case 'duplicates':
                response = await fetch('/api/duplicates');
                data = await response.json();
                displayDuplicatesReport(data);
                break;
            case 'cleanup':
                response = await fetch('/api/cleanup-log');
                data = await response.json();
                displayCleanupReport(data);
                break;
            case 'ai':
                response = await fetch('/api/ai/analyze-patterns');
                data = await response.json();
                displayAIAnalysis(data);
                break;
        }
    } catch (error) {
        reportContent.innerHTML = '<p>Error loading report: ' + error.message + '</p>';
    }
}

// Display functions for different report types
function displayScansReport(scans) {
    const reportContent = document.getElementById('report-content');

    if (scans.length === 0) {
        reportContent.innerHTML = '<p>No scans found.</p>';
        return;
    }

    let html = '<table class="report-table">';
    html += '<thead><tr><th>Date</th><th>Type</th><th>Files Found</th><th>Size</th><th>Status</th></tr></thead>';
    html += '<tbody>';

    scans.forEach(scan => {
        const size = formatBytes(scan.total_size || 0);
        html += `<tr>
            <td>${new Date(scan.scan_date).toLocaleString()}</td>
            <td>${scan.scan_type}</td>
            <td>${scan.files_found}</td>
            <td>${size}</td>
            <td>${scan.status}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    reportContent.innerHTML = html;
}

function displayDuplicatesReport(duplicates) {
    const reportContent = document.getElementById('report-content');

    if (duplicates.length === 0) {
        reportContent.innerHTML = '<p>No duplicates found.</p>';
        return;
    }

    let html = '<table class="report-table">';
    html += '<thead><tr><th>Group</th><th>File Path</th><th>Size</th><th>Similarity</th></tr></thead>';
    html += '<tbody>';

    duplicates.forEach(dup => {
        const size = formatBytes(dup.file_size || 0);
        html += `<tr>
            <td>${dup.group_id}</td>
            <td>${dup.file_path}</td>
            <td>${size}</td>
            <td>${dup.similarity_score ? dup.similarity_score.toFixed(2) : 'N/A'}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    reportContent.innerHTML = html;
}

function displayCleanupReport(logs) {
    const reportContent = document.getElementById('report-content');

    if (logs.length === 0) {
        reportContent.innerHTML = '<p>No cleanup activity found.</p>';
        return;
    }

    let html = '<table class="report-table">';
    html += '<thead><tr><th>Date</th><th>Action</th><th>File</th><th>Size</th><th>Status</th></tr></thead>';
    html += '<tbody>';

    logs.forEach(log => {
        const size = formatBytes(log.file_size || 0);
        const status = log.success ? '✅ Success' : '❌ Failed';
        html += `<tr>
            <td>${new Date(log.action_date).toLocaleString()}</td>
            <td>${log.action_type}</td>
            <td>${log.file_path || 'N/A'}</td>
            <td>${size}</td>
            <td>${status}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    reportContent.innerHTML = html;
}

function displayAIAnalysis(data) {
    const reportContent = document.getElementById('report-content');

    let html = '<h3>Cleanup Patterns</h3>';
    if (data.cleanup_patterns) {
        html += '<table class="report-table">';
        html += '<thead><tr><th>Action Type</th><th>Count</th><th>Success Rate</th></tr></thead>';
        html += '<tbody>';

        Object.entries(data.cleanup_patterns).forEach(([action, stats]) => {
            const successRate = (stats.success_rate * 100).toFixed(1) + '%';
            html += `<tr>
                <td>${action}</td>
                <td>${stats.count}</td>
                <td>${successRate}</td>
            </tr>`;
        });

        html += '</tbody></table>';
    }

    html += '<h3>Duplicate Analysis</h3>';
    if (data.duplicate_analysis) {
        const dup = data.duplicate_analysis;
        html += `<p><strong>Total Duplicates:</strong> ${dup.total_duplicates}</p>`;
        html += `<p><strong>Unique Groups:</strong> ${dup.unique_groups}</p>`;
        html += `<p><strong>Total Wasted Space:</strong> ${formatBytes(dup.total_wasted_space)}</p>`;
    }

    reportContent.innerHTML = html;
}

// File Browser Functions
function showFileBrowser() {
    document.getElementById('file-browser-modal').style.display = 'block';
    loadDirectory();
}

function closeFileBrowserModal() {
    document.getElementById('file-browser-modal').style.display = 'none';
}

async function loadDirectory() {
    const pathInput = document.getElementById('current-path');
    const path = pathInput.value || '/Users';
    const fileList = document.getElementById('file-list');

    fileList.innerHTML = '<p>Loading files...</p>';

    try {
        const response = await fetch(`/api/files/browse?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (data.error) {
            fileList.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
            return;
        }

        pathInput.value = data.current_path;

        let html = '';
        data.items.forEach(item => {
            const icon = item.type === 'directory' ? '📁' : '📄';
            const size = item.type === 'file' ? formatBytes(item.size) : '';
            const onclick = item.type === 'directory'
                ? `navigateTo('${item.path}')`
                : `selectFile('${item.path}')`;

            html += `
                <div class="file-item" onclick="${onclick}">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${item.name}</span>
                    <span class="file-size">${size}</span>
                </div>
            `;
        });

        fileList.innerHTML = html;
    } catch (error) {
        fileList.innerHTML = `<p style="color: red;">Error loading directory: ${error.message}</p>`;
    }
}

function navigateTo(path) {
    document.getElementById('current-path').value = path;
    loadDirectory();
}

function goUp() {
    const pathInput = document.getElementById('current-path');
    const currentPath = pathInput.value;
    const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
    pathInput.value = parentPath;
    loadDirectory();
}

function selectFile(path) {
    // For now, just show an alert. Could be extended to add to exclude list, etc.
    alert(`Selected file: ${path}`);
}

// Exclude Manager Functions
function showExcludeManager() {
    document.getElementById('exclude-modal').style.display = 'block';
    loadExcludes();
}

function closeExcludeModal() {
    document.getElementById('exclude-modal').style.display = 'none';
}

async function loadExcludes() {
    const excludeList = document.getElementById('exclude-list');

    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        if (config.exclusions && config.exclusions.patterns) {
            let html = '';
            config.exclusions.patterns.forEach((pattern, index) => {
                html += `
                    <div class="exclude-item">
                        <span class="exclude-path">${pattern}</span>
                        <button onclick="removeExclude(${index})" class="remove-btn">Remove</button>
                    </div>
                `;
            });
            excludeList.innerHTML = html;
        } else {
            excludeList.innerHTML = '<p>No exclude patterns found.</p>';
        }
    } catch (error) {
        excludeList.innerHTML = `<p style="color: red;">Error loading excludes: ${error.message}</p>`;
    }
}

function addExclude() {
    const newExclude = document.getElementById('new-exclude').value.trim();
    if (!newExclude) {
        alert('Please enter a path to exclude.');
        return;
    }

    // Add to the list visually (will be saved when user clicks Save Changes)
    const excludeList = document.getElementById('exclude-list');
    const newItem = document.createElement('div');
    newItem.className = 'exclude-item';
    newItem.innerHTML = `
        <span class="exclude-path">${newExclude}</span>
        <button onclick="removeExcludeItem(this)" class="remove-btn">Remove</button>
    `;
    excludeList.appendChild(newItem);

    document.getElementById('new-exclude').value = '';
}

function removeExclude(index) {
    // This would need to be implemented with proper backend support
    alert('Remove functionality requires backend implementation');
}

function removeExcludeItem(button) {
    button.parentElement.remove();
}

async function saveExcludes() {
    // This would need backend implementation to actually save changes
    alert('Save functionality requires backend implementation');
}

// AI Chat Functions
function showAIChat() {
    document.getElementById('ai-chat-modal').style.display = 'block';
}

function closeChatModal() {
    document.getElementById('ai-chat-modal').style.display = 'none';
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

// This function is replaced by the Ollama version below

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'AI'}:</strong> ${message}`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modals = ['config-modal', 'file-browser-modal', 'exclude-modal', 'ai-chat-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// System Health Functions
async function loadSystemHealth() {
    try {
        const response = await fetch('/api/health/system');
        const data = await response.json();

        // Update health status
        const healthElement = document.getElementById('system-health');
        healthElement.textContent = data.overall_status;
        healthElement.className = `health-${data.overall_status.toLowerCase()}`;

        // Update memory usage
        const memoryElement = document.getElementById('memory-usage');
        memoryElement.textContent = `${data.memory_usage.used_percent}%`;

        // Color code memory usage
        if (data.memory_usage.used_percent > 80) {
            memoryElement.className = 'health-critical';
        } else if (data.memory_usage.used_percent > 60) {
            memoryElement.className = 'health-warning';
        } else {
            memoryElement.className = 'health-good';
        }

    } catch (error) {
        console.error('Error loading system health:', error);
        document.getElementById('system-health').textContent = 'Error';
        document.getElementById('memory-usage').textContent = 'Error';
    }
}

// Health Check Function
async function runHealthCheck() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Running comprehensive health check...';

    try {
        const response = await fetch('/api/health/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            let html = '<h3>🏥 Health Check Results</h3>';
            html += '<div class="health-results">';

            result.checks.forEach(check => {
                const statusClass = check.status === 'good' ? 'health-good' :
                                  check.status === 'warning' ? 'health-warning' : 'health-critical';
                html += `
                    <div class="health-item">
                        <span class="health-label">${check.name}:</span>
                        <span class="health-value ${statusClass}">${check.status}</span>
                        <span class="health-detail">${check.details}</span>
                    </div>
                `;
            });

            html += '</div>';
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Health check failed: ${result.error}</div>`;
        }

        // Refresh health data
        setTimeout(() => {
            loadSystemHealth();
            loadStats();
        }, 1000);

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

// Memory Optimization Function
async function optimizeMemory() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Optimizing system memory...';

    try {
        const response = await fetch('/api/health/optimize-memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: green; font-weight: bold;">✓ Memory optimization completed!</div>
                <p>Freed: ${formatBytes(result.memory_freed)} of memory</p>
                <p>Cache cleared: ${formatBytes(result.cache_cleared)}</p>
            `;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Memory optimization failed: ${result.error}</div>`;
        }

        // Refresh health data
        setTimeout(() => {
            loadSystemHealth();
            loadStats();
        }, 1000);

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

// Auto Monitoring Functions
async function checkAutoMonitoringStatus() {
    try {
        const response = await fetch('/api/monitoring/status');
        const data = await response.json();

        const monitorBtn = document.getElementById('auto-monitor-btn');
        const statusDiv = document.getElementById('monitoring-status');

        if (data.active) {
            monitorBtn.innerHTML = '⏸️ Stop Auto-Monitoring';
            monitorBtn.className = 'btn btn-danger';
            statusDiv.innerHTML = '<div class="monitoring-active">Auto-monitoring is active and running in the background.</div>';
        } else {
            monitorBtn.innerHTML = '▶️ Start Auto-Monitoring';
            monitorBtn.className = 'btn btn-success';
            statusDiv.innerHTML = '<div class="monitoring-inactive">Auto-monitoring is currently disabled.</div>';
        }
    } catch (error) {
        console.error('Error checking monitoring status:', error);
    }
}

async function toggleAutoMonitoring() {
    const monitorBtn = document.getElementById('auto-monitor-btn');
    const isActive = monitorBtn.innerHTML.includes('Stop');

    try {
        const action = isActive ? 'stop' : 'start';
        const response = await fetch(`/api/monitoring/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            setTimeout(() => {
                checkAutoMonitoringStatus();
                loadActivityLog();
            }, 1000);
        } else {
            alert(`Failed to ${action} auto-monitoring: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Log Analysis Function
async function analyzeLogs() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Analyzing system logs...';

    try {
        const response = await fetch('/api/health/analyze-logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            let html = '<h3>📋 Log Analysis Results</h3>';
            html += '<div class="log-analysis">';

            if (result.large_logs && result.large_logs.length > 0) {
                html += '<h4>Large Log Files Found:</h4>';
                html += '<table class="report-table">';
                html += '<thead><tr><th>File</th><th>Size</th><th>Action</th></tr></thead>';
                html += '<tbody>';

                result.large_logs.forEach(log => {
                    html += `
                        <tr>
                            <td>${log.path}</td>
                            <td>${formatBytes(log.size)}</td>
                            <td><button onclick="cleanupLog('${log.path}')" class="btn btn-sm btn-warning">Clean</button></td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            }

            if (result.error_patterns && result.error_patterns.length > 0) {
                html += '<h4>Error Patterns Detected:</h4>';
                html += '<ul>';
                result.error_patterns.forEach(pattern => {
                    html += `<li><strong>${pattern.type}:</strong> ${pattern.count} occurrences</li>`;
                });
                html += '</ul>';
            }

            html += '</div>';
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Log analysis failed: ${result.error}</div>`;
        }

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

// Smart Cache Cleanup Function
async function smartCacheCleanup() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Running smart cache cleanup...';

    try {
        const response = await fetch('/api/health/smart-cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: green; font-weight: bold;">✓ Smart cache cleanup completed!</div>
                <p>Cache files analyzed: ${result.files_analyzed}</p>
                <p>Space freed: ${formatBytes(result.space_freed)}</p>
                <p>Oldest files prioritized: ${result.oldest_first ? 'Yes' : 'No'}</p>
            `;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Smart cache cleanup failed: ${result.error}</div>`;
        }

        // Refresh stats
        setTimeout(() => {
            loadStats();
            loadSystemHealth();
        }, 1000);

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

// Cleanup individual log file
async function cleanupLog(logPath) {
    if (!confirm(`Are you sure you want to clean up this log file?\n${logPath}`)) {
        return;
    }

    try {
        const response = await fetch('/api/health/cleanup-log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ log_path: logPath })
        });

        const result = await response.json();

        if (result.success) {
            alert(`Log file cleaned up! Freed ${formatBytes(result.space_freed)} of space.`);
            analyzeLogs(); // Refresh the analysis
        } else {
            alert(`Failed to cleanup log: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Document Processing Functions
async function loadProcessingStatus() {
    try {
        const response = await fetch('/api/processing/status');
        const data = await response.json();

        updateProcessingUI(data);
    } catch (error) {
        console.error('Error loading processing status:', error);
    }
}

function updateProcessingUI(data) {
    // Update statistics
    document.getElementById('queue-count').textContent = data.queue_count || 0;
    document.getElementById('processed-count').textContent = data.processed_count || 0;
    document.getElementById('time-estimate').textContent = data.time_estimate || '--:--';
    document.getElementById('processing-speed').textContent = `${data.processing_speed || 0} files/min`;

    // Update progress bar
    const progressPercent = data.total_files > 0 ? (data.processed_count / data.total_files) * 100 : 0;
    document.getElementById('progress-fill').style.width = `${progressPercent}%`;
    document.getElementById('progress-text').textContent = `${Math.round(progressPercent)}% Complete`;

    // Update status indicator
    const statusDiv = document.getElementById('processing-status');
    const statusIndicator = statusDiv.querySelector('.status-indicator');
    const statusText = statusDiv.querySelector('span:last-child');

    statusDiv.className = `processing-status status-${data.status || 'idle'}`;

    switch(data.status) {
        case 'active':
            statusIndicator.textContent = '🟢';
            statusText.textContent = 'Background processing: Active';
            break;
        case 'paused':
            statusIndicator.textContent = '🟡';
            statusText.textContent = 'Background processing: Paused';
            break;
        case 'error':
            statusIndicator.textContent = '🔴';
            statusText.textContent = 'Background processing: Error';
            break;
        default:
            statusIndicator.textContent = '⚪';
            statusText.textContent = 'Background processing: Idle';
    }

    // Update process button
    const processBtn = document.getElementById('process-btn');
    if (data.status === 'active') {
        processBtn.innerHTML = '⏸️ Pause Processing';
        processBtn.className = 'btn btn-warning';
    } else {
        processBtn.innerHTML = '▶️ Start Processing';
        processBtn.className = 'btn btn-primary';
    }
}

async function startDocumentProcessing() {
    const processBtn = document.getElementById('process-btn');
    const isActive = processBtn.innerHTML.includes('Pause');

    try {
        const action = isActive ? 'pause' : 'start';
        const response = await fetch(`/api/processing/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            setTimeout(() => {
                loadProcessingStatus();
                loadActivityLog();
            }, 1000);
        } else {
            alert(`Failed to ${action} processing: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function viewProcessingQueue() {
    try {
        const response = await fetch('/api/processing/queue');
        const data = await response.json();

        const queueList = document.getElementById('queue-list');

        if (!data.queue || data.queue.length === 0) {
            queueList.innerHTML = '<p class="empty-queue">Queue is empty</p>';
            return;
        }

        let html = '';
        data.queue.forEach((item, index) => {
            const statusClass = `status-${item.status || 'pending'}`;
            html += `
                <div class="queue-item ${item.status || 'pending'}">
                    <span class="queue-file-name">${item.filename}</span>
                    <span class="queue-file-status ${statusClass}">${item.status || 'pending'}</span>
                </div>
            `;
        });

        queueList.innerHTML = html;
    } catch (error) {
        document.getElementById('queue-list').innerHTML = `<p style="color: red;">Error loading queue: ${error.message}</p>`;
    }
}

async function clearProcessingQueue() {
    if (!confirm('Are you sure you want to clear the processing queue? This will stop all current processing.')) {
        return;
    }

    try {
        const response = await fetch('/api/processing/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('Processing queue cleared successfully.');
            loadProcessingStatus();
            viewProcessingQueue();
        } else {
            alert(`Failed to clear queue: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function analyzeDocuments() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Analyzing documents for cleanup opportunities...';

    try {
        const response = await fetch('/api/processing/analyze-documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            let html = '<h3>📄 Document Analysis Results</h3>';
            html += '<div class="document-analysis">';

            if (result.document_types && result.document_types.length > 0) {
                html += '<h4>Document Types Found:</h4>';
                html += '<table class="report-table">';
                html += '<thead><tr><th>Type</th><th>Count</th><th>Total Size</th></tr></thead>';
                html += '<tbody>';

                result.document_types.forEach(type => {
                    html += `
                        <tr>
                            <td>${type.extension}</td>
                            <td>${type.count}</td>
                            <td>${formatBytes(type.total_size)}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            }

            if (result.cleanup_suggestions && result.cleanup_suggestions.length > 0) {
                html += '<h4>Cleanup Suggestions:</h4>';
                html += '<ul>';
                result.cleanup_suggestions.forEach(suggestion => {
                    html += `<li>${suggestion}</li>`;
                });
                html += '</ul>';
            }

            html += '</div>';
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Document analysis failed: ${result.error}</div>`;
        }

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

async function filterArtifacts() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Filtering and categorizing artifacts...';

    try {
        const response = await fetch('/api/processing/filter-artifacts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            let html = '<h3>🔍 Artifact Filtering Results</h3>';
            html += '<div class="artifact-filtering">';

            if (result.categories) {
                Object.entries(result.categories).forEach(([category, items]) => {
                    if (items.length > 0) {
                        html += `<h4>${category} (${items.length} items):</h4>`;
                        html += '<ul>';
                        items.slice(0, 10).forEach(item => {  // Show first 10 items
                            html += `<li>${item.filename} (${formatBytes(item.size)})</li>`;
                        });
                        if (items.length > 10) {
                            html += `<li>... and ${items.length - 10} more items</li>`;
                        }
                        html += '</ul>';
                    }
                });
            }

            html += '</div>';
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Artifact filtering failed: ${result.error}</div>`;
        }

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

// Server Management Functions
async function startServer() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Starting TidyMe server...';

    try {
        const response = await fetch('/api/server/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: green; font-weight: bold;">✓ Server started successfully!</div>
                <p>Status: ${result.status}</p>
                <p>Message: ${result.message}</p>
            `;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">Server start failed: ${result.error}</div>`;
        }

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
    }
}

async function checkServerStatus() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Checking server status...';

    try {
        const response = await fetch('/api/server/status');
        const result = await response.json();

        let html = '<h3>📊 Server Status</h3>';
        html += '<div class="server-status">';

        if (result.status === 'running') {
            html += '<div style="color: green; font-weight: bold;">✓ Server is running</div>';
        } else {
            html += '<div style="color: red; font-weight: bold;">✗ Server status: ' + result.status + '</div>';
        }

        html += `<p><strong>Version:</strong> ${result.version}</p>`;
        html += `<p><strong>Uptime:</strong> ${result.uptime}</p>`;
        html += `<p><strong>Memory Usage:</strong> ${formatBytes(result.memory_usage || 0)}</p>`;

        html += '</div>';
        resultsContainer.innerHTML = html;

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error checking server status: ${error.message}</div>`;
    }
}

// Vault Management Functions
function showVault() {
    document.getElementById('vault-modal').style.display = 'block';
    loadVaultItems();
    loadVaultCategories();
}

function closeVaultModal() {
    document.getElementById('vault-modal').style.display = 'none';
}

async function loadVaultItems() {
    try {
        const response = await fetch('/api/vault/items');
        const data = await response.json();

        if (data.success) {
            displayVaultItems(data.items);
        } else {
            document.getElementById('vault-items').innerHTML = '<p>Error loading vault items.</p>';
        }
    } catch (error) {
        document.getElementById('vault-items').innerHTML = `<p>Error: ${error.message}</p>`;
    }
}

function displayVaultItems(items) {
    const container = document.getElementById('vault-items');

    if (items.length === 0) {
        container.innerHTML = '<p>No items in vault. Click "Add Item" to get started.</p>';
        return;
    }

    let html = '<div class="vault-items-grid">';
    items.forEach(item => {
        const expiresSoon = item.expires_at && new Date(item.expires_at) < new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
        const expired = item.expires_at && new Date(item.expires_at) < new Date();

        let statusClass = '';
        let statusText = '';

        if (expired) {
            statusClass = 'vault-expired';
            statusText = ' (Expired)';
        } else if (expiresSoon) {
            statusClass = 'vault-warning';
            statusText = ' (Expires Soon)';
        }

        html += `
            <div class="vault-item ${statusClass}" onclick="viewVaultItem('${item.key}')">
                <div class="vault-item-header">
                    <h4>${item.key}</h4>
                    <span class="vault-category">${item.category}</span>
                </div>
                <div class="vault-item-meta">
                    <span>Tags: ${item.tags.join(', ') || 'None'}</span>
                    ${statusText}
                </div>
                <div class="vault-item-actions">
                    <button onclick="event.stopPropagation(); viewVaultItem('${item.key}')" class="btn btn-sm btn-info">👁️ View</button>
                    <button onclick="event.stopPropagation(); deleteVaultItem('${item.key}')" class="btn btn-sm btn-danger">🗑️ Delete</button>
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

async function loadVaultCategories() {
    try {
        const response = await fetch('/api/vault/categories');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('vault-category-filter');
            select.innerHTML = '<option value="">All Categories</option>';

            data.categories.forEach(category => {
                select.innerHTML += `<option value="${category}">${category}</option>`;
            });
        }
    } catch (error) {
        console.error('Error loading vault categories:', error);
    }
}

function showAddItemForm() {
    document.getElementById('add-item-form').style.display = 'block';
    document.getElementById('vault-items').style.display = 'none';
    document.getElementById('vault-stats').style.display = 'none';
}

function hideAddItemForm() {
    document.getElementById('add-item-form').style.display = 'none';
    document.getElementById('vault-items').style.display = 'block';
}

async function addVaultItem(event) {
    event.preventDefault();

    const key = document.getElementById('item-key').value;
    const value = document.getElementById('item-value').value;
    const category = document.getElementById('item-category').value;
    const tags = document.getElementById('item-tags').value.split(',').map(tag => tag.trim()).filter(tag => tag);
    const expiresDays = document.getElementById('item-expires').value;

    try {
        const response = await fetch('/api/vault/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: key,
                value: value,
                category: category,
                tags: tags,
                expires_days: expiresDays ? parseInt(expiresDays) : null
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('Item added successfully!');
            hideAddItemForm();
            loadVaultItems();
            loadVaultCategories();

            // Clear form
            document.getElementById('item-key').value = '';
            document.getElementById('item-value').value = '';
            document.getElementById('item-tags').value = '';
            document.getElementById('item-expires').value = '';
        } else {
            alert('Error adding item: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function viewVaultItem(key) {
    try {
        const response = await fetch(`/api/vault/items/${key}`);
        const data = await response.json();

        if (data.success) {
            const value = typeof data.value === 'object' ? JSON.stringify(data.value, null, 2) : data.value;

            const details = `
Key: ${data.key}
Category: ${data.category}
Tags: ${data.tags.join(', ') || 'None'}
Created: ${new Date(data.created_at).toLocaleString()}
${data.expires_at ? `Expires: ${new Date(data.expires_at).toLocaleString()}` : ''}

Value:
${value}
            `;

            alert(details);
        } else {
            alert('Error retrieving item: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteVaultItem(key) {
    if (!confirm(`Are you sure you want to delete the vault item "${key}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/vault/items/${key}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('Item deleted successfully!');
            loadVaultItems();
        } else {
            alert('Error deleting item: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function searchVault() {
    const query = document.getElementById('vault-search').value.toLowerCase();
    const items = document.querySelectorAll('.vault-item');

    items.forEach(item => {
        const key = item.querySelector('h4').textContent.toLowerCase();
        const category = item.querySelector('.vault-category').textContent.toLowerCase();
        const tags = item.querySelector('.vault-item-meta span').textContent.toLowerCase();

        if (key.includes(query) || category.includes(query) || tags.includes(query)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function filterVaultByCategory() {
    const category = document.getElementById('vault-category-filter').value;
    const items = document.querySelectorAll('.vault-item');

    items.forEach(item => {
        const itemCategory = item.querySelector('.vault-category').textContent;

        if (!category || itemCategory === category) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

async function showVaultStats() {
    document.getElementById('vault-stats').style.display = 'block';
    document.getElementById('vault-items').style.display = 'none';
    document.getElementById('add-item-form').style.display = 'none';

    try {
        const response = await fetch('/api/vault/stats');
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            const html = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <strong>Total Items:</strong> ${stats.total_items}
                    </div>
                    <div class="stat-item">
                        <strong>Expired Items:</strong> ${stats.expired_items}
                    </div>
                    <div class="stat-item">
                        <strong>Expiring Soon:</strong> ${stats.expiring_soon}
                    </div>
                </div>
                <h4>Items by Category:</h4>
                <ul>
                    ${Object.entries(stats.categories).map(([cat, count]) =>
                        `<li>${cat}: ${count} items</li>`
                    ).join('')}
                </ul>
            `;

            document.getElementById('stats-content').innerHTML = html;
        } else {
            document.getElementById('stats-content').innerHTML = '<p>Error loading statistics.</p>';
        }
    } catch (error) {
        document.getElementById('stats-content').innerHTML = `<p>Error: ${error.message}</p>`;
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modals = ['config-modal', 'file-browser-modal', 'exclude-modal', 'ai-chat-modal', 'vault-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// AI Chat Functions
function showAIChat() {
    document.getElementById('ai-chat-modal').style.display = 'block';
}

function closeChatModal() {
    document.getElementById('ai-chat-modal').style.display = 'none';
}

// Store pending message IDs for status checking
let pendingMessages = new Set();

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const model = document.getElementById('chat-model').value;

    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    input.value = '';

    // Show typing indicator
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message';
    typingDiv.innerHTML = '<strong>AI:</strong> <em>Thinking...</em>';
    typingDiv.id = 'typing-indicator';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/ollama/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                model: model,
                queue: true  // Enable queuing
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            if (result.queued) {
                // Message was queued
                addMessageToChat('ai', `📋 ${result.message} (Position: ${result.queue_position})`);
                pendingMessages.add(result.message_id);

                // Start checking status for this message
                checkMessageStatus(result.message_id);
            } else if (result.response) {
                // Message processed immediately
                // Remove typing indicator
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                addMessageToChat('ai', result.response);
            }
        } else {
            // Remove typing indicator
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            const errorMsg = result.error || 'Unknown error occurred';
            addMessageToChat('ai', `❌ Error: ${errorMsg}`);
        }
    } catch (error) {
        // Remove typing indicator
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        addMessageToChat('ai', `🌐 Network error: ${error.message}`);
    }
}

async function checkMessageStatus(messageId) {
    if (!pendingMessages.has(messageId)) return;

    try {
        const response = await fetch(`/api/ollama/chat/status/${messageId}`);
        const result = await response.json();

        if (result.success) {
            if (result.status === 'queued') {
                // Still in queue, check again in 2 seconds
                setTimeout(() => checkMessageStatus(messageId), 2000);
            } else if (result.response) {
                // Message completed
                pendingMessages.delete(messageId);

                // Remove typing indicator if it exists
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                addMessageToChat('ai', result.response);
            }
        } else if (result.error) {
            // Error occurred
            pendingMessages.delete(messageId);

            // Remove typing indicator if it exists
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }

            addMessageToChat('ai', `❌ Error: ${result.error}`);
        }
    } catch (error) {
        // Network error, try again in 3 seconds
        setTimeout(() => checkMessageStatus(messageId), 3000);
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function addMessageToChat(sender, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
        <strong>${sender === 'ai' ? 'AI' : 'You'}:</strong>
        <span class="message-time">${timestamp}</span><br>
        ${message.replace(/\n/g, '<br>')}
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Query Processing Functions
function handleQueryKeyPress(event) {
    if (event.key === 'Enter') {
        processQuery();
    }
}

async function processQuery() {
    const input = document.getElementById('query-input');
    const query = input.value.trim().toLowerCase();

    if (!query) return;

    input.value = '';

    // Show processing indicator
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Processing your request...';

    try {
        // Parse the query and determine action
        const action = parseQuery(query);

        if (action.type === 'orchestrate') {
            await orchestrateAction(action);
        } else if (action.type === 'cleanup' || action.type === 'scan' || action.type === 'report') {
            await runCleanup(action.command);
        } else if (action.type === 'chat') {
            // Open chat modal and send the query
            showAIChat();
            setTimeout(() => {
                document.getElementById('chat-input').value = query;
                sendChatMessage();
            }, 500);
        } else {
            // Default to AI chat for unrecognized queries
            showAIChat();
            setTimeout(() => {
                document.getElementById('chat-input').value = query;
                sendChatMessage();
            }, 500);
        }

    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">Error processing query: ${error.message}</div>`;
    }
}

function parseQuery(query) {
    // Enhanced query parsing with patterns and orchestration
    const patterns = [
        // Multi-step operations
        {
            pattern: /(clean|cleanup).*all|complete.*clean/i,
            action: { type: 'orchestrate', command: 'maintenance-chain' }
        },
        {
            pattern: /(scan|find).*duplicate/i,
            action: { type: 'orchestrate', command: 'scan-cleanup-chain' }
        },
        {
            pattern: /(optimize|speed.*up|performance)/i,
            action: { type: 'orchestrate', command: 'optimization-chain' }
        },

        // Single operations
        {
            pattern: /(clean|remove).*temp/i,
            action: { type: 'cleanup', command: 'clean-temp' }
        },
        {
            pattern: /(clean|clear).*cache/i,
            action: { type: 'cleanup', command: 'clean-cache' }
        },
        {
            pattern: /(scan|find).*duplicate/i,
            action: { type: 'scan', command: 'scan' }
        },
        {
            pattern: /(clean|remove).*dev/i,
            action: { type: 'cleanup', command: 'clean-dev' }
        },

        // Reports and status
        {
            pattern: /(report|status|summary|overview)/i,
            action: { type: 'report', command: 'report' }
        },
        {
            pattern: /(health|check|diagnos)/i,
            action: { type: 'report', command: 'health' }
        },

        // AI interactions
        {
            pattern: /(chat|talk|ask|help|question)/i,
            action: { type: 'chat', command: 'chat' }
        }
    ];

    // Check patterns
    for (const { pattern, action } of patterns) {
        if (pattern.test(query)) {
            return action;
        }
    }

    // Default to chat for unrecognized queries
    return { type: 'chat', command: 'chat' };
}

async function orchestrateAction(action) {
    const resultsContainer = document.getElementById('results-container');

    switch (action.command) {
        case 'maintenance-chain':
            resultsContainer.innerHTML = '<div class="loading"></div> Starting complete maintenance chain...';
            await createMaintenanceChain();
            break;

        case 'scan-cleanup-chain':
            resultsContainer.innerHTML = '<div class="loading"></div> Starting scan and cleanup chain...';
            await runCleanup('scan');
            setTimeout(() => runCleanup('clean-all'), 2000);
            break;

        case 'optimization-chain':
            resultsContainer.innerHTML = '<div class="loading"></div> Starting optimization chain...';
            await runCleanup('clean-cache');
            setTimeout(() => runCleanup('clean-temp'), 2000);
            setTimeout(() => runCleanup('clean-dev'), 4000);
            break;

        default:
            await runCleanup(action.command);
    }
}

// Consent Management Functions
function showConsentModal() {
    document.getElementById('consent-modal').style.display = 'block';
}

function closeConsentModal() {
    document.getElementById('consent-modal').style.display = 'none';
}

async function submitConsent(event) {
    event.preventDefault();

    const checkbox = document.getElementById('consent-checkbox');
    if (!checkbox.checked) {
        alert('Please check the consent box to continue.');
        return;
    }

    try {
        const response = await fetch('/api/consent/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            closeConsentModal();
            alert('Thank you for your consent! TidyMe is now ready to use.');
            // Refresh the page to show all features
            location.reload();
        } else {
            alert('Error recording consent: ' + result.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

async function declineConsent() {
    if (confirm('Are you sure you want to decline? TidyMe will not function without consent.')) {
        closeConsentModal();
        alert('Consent declined. Some features may be limited.');
    }
}

// Browser Session Management Functions
async function closeBrowserInstances() {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"></div> Closing browser instances...';

    try {
        const response = await fetch('/api/browser/close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            resultsContainer.innerHTML = `
                <div style="color: green; font-weight: bold;">✅ Browser instances closed successfully</div>
                <p>${result.message}</p>
                <p>Cookies preserved: ${result.cookies_preserved ? 'Yes' : 'No'}</p>
                ${result.sessions_closed ? `<p>Sessions logged: ${result.sessions_closed.length}</p>` : ''}
            `;
        } else {
            resultsContainer.innerHTML = `<div style="color: red;">❌ Failed to close browser instances: ${result.error}</div>`;
        }
    } catch (error) {
        resultsContainer.innerHTML = `<div style="color: red;">❌ Network error: ${error.message}</div>`;
    }
}

async function showBrowserSessions() {
    try {
        const response = await fetch('/api/browser/sessions/active');
        const result = await response.json();

        if (result.success) {
            let html = '<h3>Active Browser Sessions</h3>';
            if (result.sessions.length > 0) {
                html += '<table class="report-table">';
                html += '<thead><tr><th>Session ID</th><th>Browser</th><th>Start Time</th><th>Tabs</th><th>Status</th></tr></thead>';
                html += '<tbody>';

                result.sessions.forEach(session => {
                    html += `
                        <tr>
                            <td>${session.session_id}</td>
                            <td>${session.browser_type}</td>
                            <td>${new Date(session.start_time).toLocaleString()}</td>
                            <td>${session.tabs_count || 0}</td>
                            <td>${session.status}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
            } else {
                html += '<p>No active browser sessions found.</p>';
            }

            document.getElementById('results-container').innerHTML = html;
        } else {
            document.getElementById('results-container').innerHTML = `<div style="color: red;">Error: ${result.error}</div>`;
        }
    } catch (error) {
        document.getElementById('results-container').innerHTML = `<div style="color: red;">Network error: ${error.message}</div>`;
    }
}

// Check consent status on page load
async function checkConsentStatus() {
    try {
        const response = await fetch('/api/consent/status');
        const result = await response.json();

        if (result.success && !result.consent.has_consent) {
            // Show consent modal if no consent given
            setTimeout(() => {
                showConsentModal();
            }, 1000);
        }
    } catch (error) {
        console.error('Error checking consent status:', error);
    }
}

// Auto-refresh data every 30 seconds
setInterval(() => {
    loadStats();
    loadAIInsights();
    checkDaemonStatus();
    loadSystemHealth();
    loadProcessingStatus();
    updateChatQueueStatus();
}, 30000);

// Update chat queue status every 5 seconds
setInterval(() => {
    updateChatQueueStatus();
}, 5000);

// AI Chat Functions
async function showAIChat() {
    document.getElementById('ai-chat-modal').style.display = 'block';
    await loadAvailableModels();
    await updateChatQueueStatus();
}

function closeChatModal() {
    document.getElementById('ai-chat-modal').style.display = 'none';
}

async function loadAvailableModels() {
    try {
        const response = await fetch('/api/ollama/models');
        const data = await response.json();

        if (data.success && data.models.length > 0) {
            const modelSelector = document.getElementById('chat-model');
            modelSelector.innerHTML = '';

            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `${model.name} (${model.size})`;
                modelSelector.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading available models:', error);
        // Keep default models if loading fails
    }
}

async function updateChatQueueStatus() {
    try {
        const response = await fetch('/api/ollama/chat/queue');
        const data = await response.json();

        if (data.success) {
            const queueStatus = document.getElementById('chat-queue-status');
            if (queueStatus) {
                if (data.processing_active || data.queue_length > 0) {
                    queueStatus.innerHTML = `
                        <div class="queue-status">
                            ${data.processing_active ? '🔄 Processing' : '⏳ Waiting'}
                            ${data.queue_length > 0 ? ` | Queue: ${data.queue_length}` : ''}
                        </div>
                    `;
                    queueStatus.style.display = 'block';
                } else {
                    queueStatus.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Error updating chat queue status:', error);
    }
}

// Check consent on page load
document.addEventListener('DOMContentLoaded', function() {
    checkConsentStatus();
});

// Tab Switching Functionality
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.main-tab-btn');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab content
    const selectedContent = document.getElementById(tabName + '-content');
    if (selectedContent) {
        selectedContent.classList.add('active');
    }

    // Add active class to selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Save tab preference to localStorage
    saveUserPreference('activeTab', tabName);
}

// AI Tab Functions
async function sendAIMessage() {
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    const model = document.getElementById('ai-model-selector').value;

    if (!message) return;

    // Add user message to chat
    addAIMessageToChat('user', message);
    input.value = '';

    // Show typing indicator
    const chatMessages = document.getElementById('ai-chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message';
    typingDiv.innerHTML = '<strong>AI:</strong> <em>Thinking...</em>';
    typingDiv.id = 'ai-typing-indicator';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });

        const result = await response.json();

        // Remove typing indicator
        const typingIndicator = document.getElementById('ai-typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        if (result.success !== false) {
            addAIMessageToChat('ai', result.response || result.message || 'Sorry, I encountered an error.');
        } else {
            addAIMessageToChat('ai', `❌ Error: ${result.error || 'Unknown error'}`);
        }

    } catch (error) {
        // Remove typing indicator
        const typingIndicator = document.getElementById('ai-typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        addAIMessageToChat('ai', `❌ Network error: ${error.message}`);
    }
}

function handleAIChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendAIMessage();
    }
}

function addAIMessageToChat(sender, message) {
    const chatMessages = document.getElementById('ai-chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
        <strong>${sender === 'ai' ? 'AI' : 'You'}:</strong>
        <span class="message-time">${timestamp}</span><br>
        ${message.replace(/\n/g, '<br>')}
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearAIChat() {
    const chatMessages = document.getElementById('ai-chat-messages');
    // Keep only the initial welcome message
    const welcomeMessage = chatMessages.querySelector('.ai-message');
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }
}

// AI Feature Functions
async function getAIAnalysis() {
    const insightsPanel = document.getElementById('ai-insights-panel');
    insightsPanel.innerHTML = '<div class="loading"></div> Analyzing system...';

    try {
        const response = await fetch('/api/ai/insights');
        const result = await response.json();

        if (result.success !== false) {
            let html = '<h4>🧠 System Analysis Results</h4>';
            html += '<div class="ai-analysis-results">';

            if (result.insights) {
                html += '<div class="insights-section">';
                html += '<h5>Key Insights:</h5>';
                html += '<ul>';
                result.insights.forEach(insight => {
                    html += `<li>${insight}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }

            if (result.suggestions) {
                html += '<div class="suggestions-section">';
                html += '<h5>Recommendations:</h5>';
                html += '<ul>';
                result.suggestions.forEach(suggestion => {
                    html += `<li>${suggestion}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }

            html += '</div>';
            insightsPanel.innerHTML = html;
        } else {
            insightsPanel.innerHTML = `<div style="color: red;">❌ Analysis failed: ${result.error || 'Unknown error'}</div>`;
        }

    } catch (error) {
        insightsPanel.innerHTML = `<div style="color: red;">❌ Network error: ${error.message}</div>`;
    }
}

async function getCleanupPredictions() {
    const insightsPanel = document.getElementById('ai-insights-panel');
    insightsPanel.innerHTML = '<div class="loading"></div> Generating predictions...';

    try {
        const response = await fetch('/api/ai/predictions?days=7');
        const result = await response.json();

        if (result.success !== false) {
            let html = '<h4>🔮 Cleanup Predictions (Next 7 Days)</h4>';
            html += '<div class="predictions-results">';

            if (result.predictions && result.predictions.length > 0) {
                html += '<ul>';
                result.predictions.forEach(prediction => {
                    html += `<li><strong>${prediction.date}:</strong> ${prediction.description}</li>`;
                });
                html += '</ul>';
            } else {
                html += '<p>No specific predictions available. Your system appears to be well-maintained!</p>';
            }

            html += '</div>';
            insightsPanel.innerHTML = html;
        } else {
            insightsPanel.innerHTML = `<div style="color: red;">❌ Prediction failed: ${result.error || 'Unknown error'}</div>`;
        }

    } catch (error) {
        insightsPanel.innerHTML = `<div style="color: red;">❌ Network error: ${error.message}</div>`;
    }
}

async function analyzePatterns() {
    const insightsPanel = document.getElementById('ai-insights-panel');
    insightsPanel.innerHTML = '<div class="loading"></div> Analyzing patterns...';

    try {
        const response = await fetch('/api/ai/analyze-patterns');
        const result = await response.json();

        if (result.success !== false) {
            let html = '<h4>📈 Pattern Analysis</h4>';
            html += '<div class="patterns-results">';

            if (result.cleanup_patterns) {
                html += '<div class="pattern-section">';
                html += '<h5>Cleanup Patterns:</h5>';
                html += '<ul>';
                result.cleanup_patterns.forEach(pattern => {
                    html += `<li><strong>${pattern.type}:</strong> ${pattern.description}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }

            if (result.duplicate_analysis) {
                html += '<div class="pattern-section">';
                html += '<h5>Duplicate Analysis:</h5>';
                html += '<ul>';
                result.duplicate_analysis.forEach(analysis => {
                    html += `<li><strong>${analysis.category}:</strong> ${analysis.insights}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }

            html += '</div>';
            insightsPanel.innerHTML = html;
        } else {
            insightsPanel.innerHTML = `<div style="color: red;">❌ Pattern analysis failed: ${result.error || 'Unknown error'}</div>`;
        }

    } catch (error) {
        insightsPanel.innerHTML = `<div style="color: red;">❌ Network error: ${error.message}</div>`;
    }
}

function getOptimizationTips() {
    const insightsPanel = document.getElementById('ai-insights-panel');

    const tips = [
        "🧹 Run regular cache cleanup to free up disk space",
        "📁 Organize files by type and date for better management",
        "🔍 Use duplicate detection to identify and remove redundant files",
        "🗂️ Consider archiving old projects instead of deleting them",
        "⚡ Monitor system performance and clean temp files regularly",
        "🔒 Use secure deletion for sensitive files when needed",
        "📊 Review cleanup logs to understand usage patterns",
        "🤖 Enable automated maintenance for consistent performance"
    ];

    let html = '<h4>💡 Optimization Tips</h4>';
    html += '<div class="tips-results">';
    html += '<ul>';
    tips.forEach(tip => {
        html += `<li>${tip}</li>`;
    });
    html += '</ul>';
    html += '</div>';

    insightsPanel.innerHTML = html;
}

// LocalStorage Functions for Remembering User Choices
function saveUserPreference(key, value) {
    try {
        localStorage.setItem(`tidyme_${key}`, JSON.stringify(value));
    } catch (error) {
        console.warn('Failed to save user preference:', error);
    }
}

function loadUserPreference(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(`tidyme_${key}`);
        return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.warn('Failed to load user preference:', error);
        return defaultValue;
    }
}

function saveExpandableButtonStates() {
    const expandedButtons = {};
    const buttons = document.querySelectorAll('.expandable-btn.expanded');

    buttons.forEach(button => {
        const section = button.closest('.action-buttons, .system-buttons, .monitoring-buttons, .processing-buttons');
        if (section) {
            const sectionId = section.id || section.className;
            const buttonIndex = Array.from(section.querySelectorAll('.expandable-btn')).indexOf(button);
            if (!expandedButtons[sectionId]) {
                expandedButtons[sectionId] = [];
            }
            expandedButtons[sectionId].push(buttonIndex);
        }
    });

    saveUserPreference('expandedButtons', expandedButtons);
}

function loadExpandableButtonStates() {
    const expandedButtons = loadUserPreference('expandedButtons', {});

    Object.entries(expandedButtons).forEach(([sectionId, buttonIndices]) => {
        const section = document.getElementById(sectionId) || document.querySelector(`.${sectionId}`);
        if (section) {
            buttonIndices.forEach(index => {
                const buttons = section.querySelectorAll('.expandable-btn');
                if (buttons[index]) {
                    setTimeout(() => {
                        toggleExpandableButton(buttons[index]);
                    }, 100); // Small delay to ensure DOM is ready
                }
            });
        }
    });
}

function saveCheckboxStates() {
    const checkboxStates = {};
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        if (checkbox.id) {
            checkboxStates[checkbox.id] = checkbox.checked;
        }
    });

    saveUserPreference('checkboxStates', checkboxStates);
}

function loadCheckboxStates() {
    const checkboxStates = loadUserPreference('checkboxStates', {});

    Object.entries(checkboxStates).forEach(([checkboxId, checked]) => {
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.checked = checked;
        }
    });
}

function saveSelectStates() {
    const selectStates = {};
    const selects = document.querySelectorAll('select');

    selects.forEach(select => {
        if (select.id) {
            selectStates[select.id] = select.value;
        }
    });

    saveUserPreference('selectStates', selectStates);
}

function loadSelectStates() {
    const selectStates = loadUserPreference('selectStates', {});

    Object.entries(selectStates).forEach(([selectId, value]) => {
        const select = document.getElementById(selectId);
        if (select) {
            select.value = value;
        }
    });
}

function saveInputStates() {
    const inputStates = {};
    const numberInputs = document.querySelectorAll('input[type="number"]');

    numberInputs.forEach(input => {
        if (input.id) {
            inputStates[input.id] = input.value;
        }
    });

    saveUserPreference('inputStates', inputStates);
}

function loadInputStates() {
    const inputStates = loadUserPreference('inputStates', {});

    Object.entries(inputStates).forEach(([inputId, value]) => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = value;
        }
    });
}

// Initialize user preferences on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load active tab
    const activeTab = loadUserPreference('activeTab', 'cleanup');
    switchTab(activeTab);

    // Load user preferences after a short delay to ensure DOM is ready
    setTimeout(() => {
        loadExpandableButtonStates();
        loadCheckboxStates();
        loadSelectStates();
        loadInputStates();
    }, 500);

    // Save preferences when user interacts with elements
    document.addEventListener('change', function(event) {
        if (event.target.type === 'checkbox' || event.target.type === 'number' || event.target.tagName === 'SELECT') {
            saveCheckboxStates();
            saveSelectStates();
            saveInputStates();
        }
    });

    // Save expandable button states when they change
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target.classList.contains('expandable-btn')) {
                    saveExpandableButtonStates();
                }
            }
        });
    });

    // Observe expandable buttons for class changes
    document.querySelectorAll('.expandable-btn').forEach(button => {
        observer.observe(button, { attributes: true });
    });
});