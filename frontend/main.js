// main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('node:path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1000,
    height: 900,
    title: "DocPilot AI Organizer", // Sets window title
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    icon: path.join(__dirname, 'icons', '../assets/logo.ico') // Windows/Linux icon
  });

  // Load the index.html of the app.
  mainWindow.loadFile('index.html');

  // Open DevTools if needed
  // mainWindow.webContents.openDevTools();
}

// Set macOS dock icon
app.whenReady().then(() => {
  if (process.platform === 'darwin') {
    try {
      const iconPath = path.resolve(__dirname, '../assets/logo.jpg');
      app.dock.setIcon(iconPath);
    } catch (err) {
      console.warn('Failed to set dock icon:', err);
    }
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Directory picker
ipcMain.handle('dialog:openDirectory', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  return canceled ? null : filePaths[0];
});

// Get basename
ipcMain.handle('path:basename', (event, filePath) => {
  return path.basename(filePath);
});