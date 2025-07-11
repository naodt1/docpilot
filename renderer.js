
const FLASK_BACKEND_URL = 'http://127.0.0.1:5000'; 

// --- DOM Element References ---
// Main UI elements
const targetDirInput = document.getElementById('targetDirInput');
const browseTargetDirBtn = document.getElementById('browseTargetDir');
const dirDescription = document.getElementById('dirDescription');

// File Preview and Action Buttons container (now always visible)
const filePreviewActionsSection = document.querySelector('.file-preview-actions'); // Still reference for clarity, but no more display toggling
const fileCountSpan = document.getElementById('fileCount');
const fileListPreview = document.getElementById('fileListPreview');
const fileListStatus = document.getElementById('fileListStatus');
const refreshFilesBtn = document.getElementById('refreshFilesBtn'); // Now disabled by default in HTML

// Actions for the selected directory
const renameFilesCheckbox = document.getElementById('renameFilesCheckbox');
const organizeNowBtn = document.getElementById('organizeNowBtn'); // Now disabled by default in HTML
const openScheduleModalBtn = document.getElementById('openScheduleModal'); // Now here, disabled by default in HTML
const organizeStatus = document.getElementById('organizeStatus');

// Modals
const openLogModalBtn = document.getElementById('openLogModal');
const logModal = document.getElementById('logModal');
const closeLogModalBtn = document.getElementById('closeLogModal');

const scheduleModal = document.getElementById('scheduleModal');
const closeScheduleModalBtn = document.getElementById('closeScheduleModal');
const scheduledDirDisplay = document.getElementById('scheduledDirDisplay'); // To show scheduled directory in modal

// Schedule specific elements (inside modal)
const scheduleTypeSelect = document.getElementById('scheduleType');
const scheduleTimeGroup = document.getElementById('scheduleTimeGroup');
const scheduleTimeInput = document.getElementById('scheduleTime');
const scheduleRenameFilesCheckbox = document.getElementById('scheduleRenameFiles');
const saveScheduleBtn = document.getElementById('saveScheduleBtn');
const scheduleStatus = document.getElementById('scheduleStatus');

// Activity Log specific elements (inside modal)
const activityLogList = document.getElementById('activityLogList');

// --- Global State ---
let currentDirectory = ''; // Stores the single selected directory path

// --- Helper Functions ---
function displayStatus(element, message, type = 'info') {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
}

function clearStatus(element) {
    element.textContent = '';
    element.className = 'status-message'; // Reset classes
    element.style.display = 'none';
}

function addLogEntry(message, type = 'info') {
    const li = document.createElement('li');
    const timestamp = new Date().toLocaleString('en-US', { hour12: false });
    li.className = `log-entry ${type}`;
    li.innerHTML = `<span>[${timestamp}]</span> ${message}`;
    activityLogList.prepend(li); // Add to the top of the log
    // Optional: Keep log list from getting too long
    if (activityLogList.children.length > 50) {
        activityLogList.removeChild(activityLogList.lastChild);
    }
}

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

// --- Directory Picker & File Listing Functionality ---
async function openDirectoryDialogAndList() {
    if (window.electronAPI) { // Check if Electron API is available (from preload.js)
        try {
            const directoryPath = await window.electronAPI.openDirectoryDialog();
            if (directoryPath) {

                const normalizedPath = directoryPath.replace(/\\/g, '/'); 
                // -------------------------------------------------------------------

                targetDirInput.value = normalizedPath; // Update input field
                console.log(`Selected directory: ${normalizedPath}`);
                currentDirectory = normalizedPath;     // Update global state variable
                addLogEntry(`Directory selected: ${normalizedPath}`, 'info');
                await listFilesInDirectory(normalizedPath); // Pass the normalized path to the listing function
            }
        } catch (error) {
            console.error('Error opening directory dialog:', error);
            addLogEntry(`Failed to open directory dialog: ${error.message}`, 'error');
            alert(`Error opening directory dialog: ${error.message}`);
            // Disable buttons if directory selection failed
            organizeNowBtn.disabled = true;
            openScheduleModalBtn.disabled = true;
            refreshFilesBtn.disabled = true;
        }
    } else {
        // ... (rest of the non-electron handling) ...
        console.warn('window.electronAPI is not available. Running in a standard browser might limit functionality.');
        // For local browser testing on Windows without Electron, you might manually set a path here
        // and ensure it uses forward slashes or double backslashes:
        // const testPath = "C:/Users/YourUser/Downloads"; // Example with forward slashes
        // const testPath = "C:\\\\Users\\\\YourUser\\\\Downloads"; // Example with double backslashes
        // targetDirInput.value = testPath;
        // currentDirectory = testPath;
        // listFilesInDirectory(currentDirectory);
        organizeNowBtn.disabled = true;
        openScheduleModalBtn.disabled = true;
        refreshFilesBtn.disabled = true;
    }
}

async function listFilesInDirectory(directoryPath) {
    fileListPreview.innerHTML = ''; // Clear existing lists
    fileCountSpan.textContent = '0';
    clearStatus(fileListStatus);
    displayStatus(fileListStatus, 'Fetching files...', 'info');
    
    // Always enable refresh button when a directory is chosen
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
for (const file of files.slice(0, 7)) { // Use a for...of loop for async/await
                    const li = document.createElement('li');
                    
                    // --- FIX IS HERE ---
                    const fileName = await window.electronAPI.pathBasename(file); // AWAIT the promise
                    // --- END FIX ---

                    li.innerHTML = `<i class="fas fa-file file-icon"></i> ${fileName}`; // Use the resolved file name
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
                // Enable action buttons if files found
                organizeNowBtn.disabled = false;
                openScheduleModalBtn.disabled = false;
            } else {
                fileListPreview.innerHTML = '<p class="no-files-selected">No supported files found in this directory.</p>';
                displayStatus(fileListStatus, 'No supported files found.', 'info');
                addLogEntry(`No files found in "${directoryPath}".`, 'info');
                // Disable action buttons if no files
                organizeNowBtn.disabled = true;
                openScheduleModalBtn.disabled = true;
            }
        } else {
            fileListPreview.innerHTML = '<p class="no-files-selected">Error listing files.</p>';
            displayStatus(fileListStatus, `Error: ${result.message || 'Unknown error listing files.'}`, 'error');
            addLogEntry(`Failed to list files: ${result.message || 'Unknown error.'}`, 'error');
            // Disable buttons on error
            organizeNowBtn.disabled = true;
            openScheduleModalBtn.disabled = true;
        }
    } catch (error) {
        console.error('Network or Flask error listing files:', error);
        fileListPreview.innerHTML = '<p class="no-files-selected">Network error: Could not connect to backend.</p>';
        displayStatus(fileListStatus, `Network error: Could not connect to backend. Please ensure Flask server is running.`, 'error');
        addLogEntry(`Network error listing files: ${error.message}`, 'error');
        // Disable buttons on network error
        organizeNowBtn.disabled = true;
        openScheduleModalBtn.disabled = true;
    }
}


// --- Event Listeners ---

// Browse directory button
browseTargetDirBtn.addEventListener('click', openDirectoryDialogAndList);

// Refresh files button (for the current directory)
refreshFilesBtn.addEventListener('click', () => {
    if (currentDirectory) {
        listFilesInDirectory(currentDirectory);
    } else {
        displayStatus(fileListStatus, 'No directory selected to refresh.', 'info');
    }
});

// Organize Now Button
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
            // Refresh file list after organization to show changes
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

// Open Schedule Modal
openScheduleModalBtn.addEventListener('click', () => {
    if (!currentDirectory) {
        displayStatus(organizeStatus, 'Please select a directory first to schedule an organization.', 'info');
        return;
    }
    scheduledDirDisplay.textContent = currentDirectory; // Display the currently selected directory
    scheduleModal.style.display = 'flex'; // Use flex to center the modal
    addLogEntry('Opened Schedule Tasks modal.', 'info');
});

// Close Schedule Modal
closeScheduleModalBtn.addEventListener('click', () => {
    scheduleModal.style.display = 'none';
    clearStatus(scheduleStatus); // Clear status on close
});

// Open Log Modal
openLogModalBtn.addEventListener('click', () => {
    logModal.style.display = 'flex'; // Use flex to center the modal
    addLogEntry('Opened Activity Log modal.', 'info');
});

// Close Log Modal
closeLogModalBtn.addEventListener('click', () => {
    logModal.style.display = 'none';
});

// Close modal if click outside content
window.addEventListener('click', (event) => {
    if (event.target == scheduleModal) {
        scheduleModal.style.display = 'none';
        clearStatus(scheduleStatus);
    }
    if (event.target == logModal) {
        logModal.style.display = 'none';
    }
});

// Schedule functionality within modal
scheduleTypeSelect.addEventListener('change', () => {
    if (scheduleTypeSelect.value === 'none') {
        scheduleTimeGroup.style.display = 'none';
    } else {
        scheduleTimeGroup.style.display = 'flex';
    }
});

saveScheduleBtn.addEventListener('click', async () => {
    clearStatus(scheduleStatus);
    const scheduleType = scheduleTypeSelect.value;
    const scheduleTime = scheduleTimeInput.value;
    const scheduleRenameFiles = scheduleRenameFilesCheckbox.checked;
    const targetDirectory = currentDirectory; // Automatically use the selected directory

    if (!targetDirectory) {
        displayStatus(scheduleStatus, 'No directory selected for scheduling.', 'error');
        return;
    }
    if (scheduleType !== 'none' && !scheduleTime) {
        displayStatus(scheduleStatus, 'Please select a time for the schedule.', 'error');
        return;
    }

    toggleLoading(saveScheduleBtn, true, 'Save Schedule');
    addLogEntry(`Attempting to save schedule: Dir=${targetDirectory}, Type=${scheduleType}, Time=${scheduleTime}, Rename=${scheduleRenameFiles ? 'Yes' : 'No'}`, 'info');

    try {
        const response = await fetch(`${FLASK_BACKEND_URL}/save_schedule`, {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({
                 directory: targetDirectory,
                 schedule_type: scheduleType,
                 schedule_time: scheduleTime,
                 rename_files: scheduleRenameFiles
             })
         });
         const result = await response.json();

         if (response.ok && result.status === 'success') {
             // MODIFIED LINE HERE: Use window.electronAPI.pathBasename
             displayStatus(scheduleStatus, `Schedule saved successfully for "${window.electronAPI.pathBasename(targetDirectory)}"! Type: ${scheduleType} Time: ${scheduleTime}`, 'success');
             addLogEntry(`Schedule saved: Type=${scheduleType}, Time=${scheduleTime}, Directory=${targetDirectory}.`, 'success');
         } else {
             displayStatus(scheduleStatus, `Error saving schedule: ${result.message || 'Unknown error.'}`, 'error');
             addLogEntry(`Failed to save schedule: ${result.message || 'Unknown error.'}`, 'error');
         }
    } catch (error) {
        console.error('Error saving schedule:', error);
        displayStatus(scheduleStatus, `Network error saving schedule: ${error.message}. Ensure Flask endpoint '/save_schedule' exists.`, 'error');
        addLogEntry(`Network error saving schedule: ${error.message}`, 'error');
    } finally {
        toggleLoading(saveScheduleBtn, false, 'Save Schedule');
    }
});


// --- Initial Setup / Version Info ---
if (window.versions) {
    document.getElementById('node-version').textContent = window.versions.node();
    document.getElementById('chrome-version').textContent = window.versions.chrome();
    document.getElementById('electron-version').textContent = window.versions.electron();
} else {
    console.warn('window.versions is not available. Version info will not be displayed. Ensure preload.js is correctly configured.');
    const versionInfoElement = document.querySelector('.version-info');
    if (versionInfoElement) versionInfoElement.style.display = 'none';
}


// Initialize UI state when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Clear any initial status messages
    clearStatus(fileListStatus);
    clearStatus(organizeStatus);
    clearStatus(scheduleStatus);

    // Initial log entry
    addLogEntry('FilePilot application started.', 'info');
});