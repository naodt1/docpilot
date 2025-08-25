// --- Backend URL ---
const FLASK_BACKEND_URL = 'http://127.0.0.1:5000'; // Local Flask server endpoint

// --- DOM Element References ---
// Main UI elements
const targetDirInput = document.getElementById('targetDirInput'); // Input field for selected directory
const browseTargetDirBtn = document.getElementById('browseTargetDir'); // Button to open folder dialog
const dirDescription = document.getElementById('dirDescription'); // Optional directory description display

// File Preview and Action Buttons
const filePreviewActionsSection = document.querySelector('.file-preview-actions'); // Container for preview and action buttons
const fileCountSpan = document.getElementById('fileCount'); // Displays number of files in selected directory
const fileListPreview = document.getElementById('fileListPreview'); // Shows list of files preview
const fileListStatus = document.getElementById('fileListStatus'); // Status messages for file listing
const refreshFilesBtn = document.getElementById('refreshFilesBtn'); // Refresh file listing button (disabled initially)

// Action buttons
const renameFilesCheckbox = document.getElementById('renameFilesCheckbox'); // Checkbox to enable file renaming
const organizeNowBtn = document.getElementById('organizeNowBtn'); // "Organize Now" button (disabled initially)
const openScheduleModalBtn = document.getElementById('openScheduleModal'); // Opens schedule modal (disabled initially)
const organizeStatus = document.getElementById('organizeStatus'); // Status messages for organization actions

// --- Modals ---
const openLogModalBtn = document.getElementById('openLogModal'); // Opens activity log modal
const logModal = document.getElementById('logModal'); // Activity log modal element
const closeLogModalBtn = document.getElementById('closeLogModal'); // Close button for log modal

const scheduleModal = document.getElementById('scheduleModal'); // Schedule task modal element
const closeScheduleModalBtn = document.getElementById('closeScheduleModal'); // Close button for schedule modal
const scheduledDirDisplay = document.getElementById('scheduledDirDisplay'); // Displays selected directory in schedule modal

// Schedule-specific elements inside modal
const scheduleTypeSelect = document.getElementById('scheduleType'); // Dropdown for schedule type
const scheduleTimeGroup = document.getElementById('scheduleTimeGroup'); // Time input container (shown/hidden)
const scheduleTimeInput = document.getElementById('scheduleTime'); // Input for schedule time
const scheduleRenameFilesCheckbox = document.getElementById('scheduleRenameFiles'); // Checkbox for renaming in schedule
const saveScheduleBtn = document.getElementById('saveScheduleBtn'); // Button to save scheduled task
const scheduleStatus = document.getElementById('scheduleStatus'); // Status messages in schedule modal

// Activity log elements
const activityLogList = document.getElementById('activityLogList'); // List of log entries in modal
const uiLogDisplay = document.getElementById('uiLogDisplay'); // Main UI log display (new addition)

// --- Global State ---
let currentDirectory = ''; // Currently selected directory path

// --- Helper Functions ---

/**
 * Display a status message in a given element
 * @param {HTMLElement} element - Target element
 * @param {string} message - Message to show
 * @param {string} type - 'info', 'success', 'error' (for styling)
 */
function displayStatus(element, message, type = 'info') {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
}

/**
 * Clears status messages from an element
 * @param {HTMLElement} element
 */
function clearStatus(element) {
    element.textContent = '';
    element.className = 'status-message';
    element.style.display = 'none';
}

/**
 * Add a log entry to both the modal and the main UI log
 * @param {string} message - Log message
 * @param {string} type - 'info', 'success', 'error'
 */
function addLogEntry(message, type = 'info') {
    const timestamp = new Date().toLocaleString('en-US', { hour12: false });

    // Modal log entry
    const li = document.createElement('li');
    li.className = `log-entry ${type}`;
    li.innerHTML = `<span>[${timestamp}]</span> ${message}`;
    activityLogList.prepend(li);
    if (activityLogList.children.length > 50) {
        activityLogList.removeChild(activityLogList.lastChild);
    }

    // UI log entry
    const p = document.createElement('p');
    p.className = `log-${type}`;
    p.textContent = `[${timestamp.split(' ')[1]}] ${message}`; // shorter timestamp for main UI
    uiLogDisplay.prepend(p);
    if (uiLogDisplay.children.length > 10) {
        uiLogDisplay.removeChild(uiLogDisplay.lastChild);
    }
}

/**
 * Toggle loading state for a button
 * @param {HTMLButtonElement} button
 * @param {boolean} isLoading
 * @param {string} originalText
 */
function toggleLoading(button, isLoading, originalText = '') {
    if (isLoading) {
        button.disabled = true;
        button.classList.add('loading');
        button.dataset.originalText = originalText || button.textContent;
        button.textContent = 'Processing...';
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        button.textContent = button.dataset.originalText || originalText;
        delete button.dataset.originalText;
    }
}

// --- Directory Picker & File Listing ---

/**
 * Opens folder dialog and lists files
 */
async function openDirectoryDialogAndList() {
    if (window.electronAPI) {
        try {
            const directoryPath = await window.electronAPI.openDirectoryDialog();
            if (directoryPath) {
                const normalizedPath = directoryPath.replace(/\\/g, '/');
                targetDirInput.value = normalizedPath;
                currentDirectory = normalizedPath;
                addLogEntry(`Directory selected: ${normalizedPath}`, 'info');
                await listFilesInDirectory(normalizedPath);
            }
        } catch (error) {
            console.error('Error opening directory dialog:', error);
            addLogEntry(`Failed to open directory dialog: ${error.message}`, 'error');
            alert(`Error opening directory dialog: ${error.message}`);
            // Disable buttons if directory selection fails
            organizeNowBtn.disabled = true;
            openScheduleModalBtn.disabled = true;
            refreshFilesBtn.disabled = true;
        }
    } else {
        console.warn('Electron API unavailable.');
        addLogEntry('Electron API not available. Functionality is limited.', 'error');
        organizeNowBtn.disabled = true;
        openScheduleModalBtn.disabled = true;
        refreshFilesBtn.disabled = true;
    }
}

/**
 * Fetches files from backend for the selected directory and displays preview
 * @param {string} directoryPath
 */
async function listFilesInDirectory(directoryPath) {
    fileListPreview.innerHTML = '';
    fileCountSpan.textContent = '0';
    clearStatus(fileListStatus);
    displayStatus(fileListStatus, 'Fetching files...', 'info');

    refreshFilesBtn.disabled = false;

    addLogEntry(`Attempting to list files in: ${directoryPath}`, 'info');

    try {
        const response = await fetch(`${FLASK_BACKEND_URL}/list_files`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory_path: directoryPath })
        });
        const result = await response.json();

        if (response.ok && result.status === 'success') {
            const files = result.files;
            fileCountSpan.textContent = files.length;

            if (files.length > 0) {
                const previewUl = document.createElement('ul');
                previewUl.className = 'preview-list';
                for (const file of files.slice(0, 7)) {
                    const li = document.createElement('li');
                    const fileName = await window.electronAPI.pathBasename(file);
                    li.innerHTML = `<i class="fas fa-file file-icon"></i> ${fileName}`;
                    previewUl.appendChild(li);
                }
                if (files.length > 7) {
                    const moreLi = document.createElement('li');
                    moreLi.textContent = `... and ${files.length - 7} more.`;
                    previewUl.appendChild(moreLi);
                }
                fileListPreview.appendChild(previewUl);
                clearStatus(fileListStatus);
                addLogEntry(`Found ${files.length} files in "${directoryPath}".`, 'success');
                organizeNowBtn.disabled = false;
                openScheduleModalBtn.disabled = false;
            } else {
                fileListPreview.innerHTML = '<p class="no-files-selected">No supported files found in this directory.</p>';
                displayStatus(fileListStatus, 'No supported files found.', 'info');
                addLogEntry(`No files found in "${directoryPath}".`, 'info');
                organizeNowBtn.disabled = true;
                openScheduleModalBtn.disabled = true;
            }
        } else {
            fileListPreview.innerHTML = '<p class="no-files-selected">Error listing files.</p>';
            displayStatus(fileListStatus, `Error: ${result.message || 'Unknown error listing files.'}`, 'error');
            addLogEntry(`Failed to list files: ${result.message || 'Unknown error.'}`, 'error');
            organizeNowBtn.disabled = true;
            openScheduleModalBtn.disabled = true;
        }
    } catch (error) {
        console.error('Network or Flask error listing files:', error);
        fileListPreview.innerHTML = '<p class="no-files-selected">Network error: Could not connect to backend.</p>';
        displayStatus(fileListStatus, `Network error: Could not connect to backend. Please ensure Flask server is running.`, 'error');
        addLogEntry(`Network error listing files: ${error.message}`, 'error');
        organizeNowBtn.disabled = true;
        openScheduleModalBtn.disabled = true;
    }
}

// --- Event Listeners ---

// Directory selection
browseTargetDirBtn.addEventListener('click', openDirectoryDialogAndList);

// Refresh file list
refreshFilesBtn.addEventListener('click', () => {
    if (currentDirectory) {
        listFilesInDirectory(currentDirectory);
    } else {
        displayStatus(fileListStatus, 'No directory selected to refresh.', 'info');
    }
});

// Organize Now
organizeNowBtn.addEventListener('click', async () => {
    clearStatus(organizeStatus);
    const sourceDirectory = targetDirInput.value;
    const renameFiles = renameFilesCheckbox.checked;

    if (!sourceDirectory) {
        displayStatus(organizeStatus, 'Please select a directory to organize.', 'error');
        return;
    }

    toggleLoading(organizeNowBtn, true, 'Organize Now');
    addLogEntry(`Starting immediate organization for: "${sourceDirectory}" (Rename: ${renameFiles ? 'Yes' : 'No'})`, 'info');

    try {
        const response = await fetch(`${FLASK_BACKEND_URL}/auto_organize_in_place`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_directory: sourceDirectory,
                rename_files: renameFiles
            })
        });
        const result = await response.json();

        if (response.ok && result.status === 'success') {
            displayStatus(organizeStatus, `Successfully organized ${result.processed_count} files. Encountered ${result.error_count} errors.`, 'success');
            addLogEntry(`Immediate organization complete: ${result.processed_count} files processed, ${result.error_count} errors.`, 'success');
            if (result.errors.length > 0) {
                result.errors.forEach(err => addLogEntry(`Error with "${err.file}": ${err.message}`, 'error'));
            }
            await listFilesInDirectory(currentDirectory);
        } else {
            displayStatus(organizeStatus, `Error: ${result.message || 'Unknown error occurred.'}`, 'error');
            addLogEntry(`Immediate organization failed: ${result.message || 'Unknown error.'}`, 'error');
        }
    } catch (error) {
        console.error('Network or Flask error during organization:', error);
        displayStatus(organizeStatus, `Network error: Could not connect to backend or invalid response. Check console.`, 'error');
        addLogEntry(`Network error during immediate organization: ${error.message}`, 'error');
    } finally {
        toggleLoading(organizeNowBtn, false, 'Organize Now');
    }
});

// --- Modals Logic ---
// Schedule and log modals opening, closing, and outside-click handling omitted for brevity

// --- Initial Setup / Version Info ---
if (window.versions) {
    document.getElementById('node-version').textContent = window.versions.node();
    document.getElementById('chrome-version').textContent = window.versions.chrome();
    document.getElementById('electron-version').textContent = window.versions.electron();
} else {
    console.warn('window.versions is not available. Version info will not be displayed.');
    const versionInfoElement = document.querySelector('.version-info');
    if (versionInfoElement) versionInfoElement.style.display = 'none';
}

// Initialize UI state when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    clearStatus(fileListStatus);
    clearStatus(organizeStatus);
    clearStatus(scheduleStatus);

    addLogEntry('FilePilot application started.', 'info');
});