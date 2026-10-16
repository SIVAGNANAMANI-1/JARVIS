/**
 * JARVIS AI — Electron Native Desktop Host
 * Spawns the native desktop window, registers global summon shortcut, and attaches to local edge agent.
 */

const { app, BrowserWindow, globalShortcut, Tray, Menu } = require("electron");
const path = require("path");

let mainWindow = null;
let tray = null;
const AGENT_URL = "http://127.0.0.1:8765";

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "JARVIS AI — Personal Digital Operator",
    backgroundColor: "#080b14",
    frame: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Load the web dashboard served by the local agent, or fallback to file
  mainWindow.loadURL(AGENT_URL).catch(() => {
    // If agent is still warming up, load static file directly
    mainWindow.loadFile(path.join(__dirname, "../web/index.html"));
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  // Register Global Hotkey to summon / toggle JARVIS window (Ctrl+Alt+J)
  globalShortcut.register("CommandOrControl+Alt+J", () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
