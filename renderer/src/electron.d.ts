interface Window {
  electron: {
    isDev: boolean;
    openAuthWindow: (url: string) => Promise<string>;
  };
}
