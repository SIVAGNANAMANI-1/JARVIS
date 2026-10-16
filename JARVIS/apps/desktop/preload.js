/**
 * JARVIS AI — Electron Secure Preload Script
 * Bridges safe desktop system metadata to renderer context.
 */

const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("desktopEnv", {
  isDesktop: true,
  platform: process.platform,
  arch: process.arch,
  version: process.versions.electron,
});
