import { app, BrowserWindow, Menu, ipcMain } from 'electron'
import path from 'path'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  const isDev = process.env.VITE_DEV_SERVER_URL
  if (isDev) {
    mainWindow.loadURL(isDev)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

ipcMain.handle('open-auth-window', async (_event, url: string) => {
  return new Promise<string>((resolve, reject) => {
    const authWindow = new BrowserWindow({
      width: 600,
      height: 700,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
      },
    })

    let resolved = false

    const checkUrl = (url: string) => {
      try {
        const parsed = new URL(url)
        if (parsed.searchParams.has('code')) {
          resolved = true
          authWindow.destroy()
          resolve(parsed.searchParams.get('code')!)
          return true
        }
      } catch {}
      return false
    }

    authWindow.webContents.on('will-redirect', (_e, url) => { checkUrl(url) })
    authWindow.webContents.on('will-navigate', (_e, url) => { checkUrl(url) })
    authWindow.webContents.on('did-navigate', (_e, url) => { checkUrl(url) })
    authWindow.webContents.on('did-navigate-in-page', (_e, url) => { checkUrl(url) })
    authWindow.webContents.on('did-fail-load', (_e, _code, _desc, url, isMainFrame) => {
      if (isMainFrame) checkUrl(url)
    })

    authWindow.loadURL(url)

    authWindow.on('closed', () => {
      if (!resolved) reject(new Error('Auth window closed'))
    })
  })
})

app.on('ready', createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

// Menu
const template = [
  {
    label: 'File',
    submenu: [
      { label: 'Exit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() },
    ],
  },
  {
    label: 'View',
    submenu: [
      { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow?.reload() },
      { label: 'Toggle DevTools', accelerator: 'CmdOrCtrl+Shift+I', click: () => mainWindow?.webContents.toggleDevTools() },
    ],
  },
]

Menu.setApplicationMenu(Menu.buildFromTemplate(template as any))
