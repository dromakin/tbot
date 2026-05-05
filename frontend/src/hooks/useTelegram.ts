declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        initData: string;
      };
    };
  }
}

export function getInitDataRaw(): string {
  return window.Telegram?.WebApp?.initData ?? '';
}

export function initTelegramWebApp(): void {
  const webApp = window.Telegram?.WebApp;
  if (!webApp) return;
  webApp.ready();
  webApp.expand();
}
