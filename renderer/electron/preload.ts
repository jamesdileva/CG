import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electron', {
  isDev: process.env.NODE_ENV === 'development',
  openAuthWindow: (url: string) => ipcRenderer.invoke('open-auth-window', url),
})
