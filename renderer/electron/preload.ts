import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('electron', {
  isDev: process.env.NODE_ENV === 'development',
})
