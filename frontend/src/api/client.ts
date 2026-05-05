import { getInitDataRaw } from '../hooks/useTelegram';

function buildAuthHeader(): Record<string, string> {
  const initData = getInitDataRaw();
  if (!initData) return {};
  return { Authorization: `tma ${initData}` };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    ...(init?.headers ?? {}),
    ...buildAuthHeader(),
  };

  const response = await fetch(path, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function buildCsvExportUrl(): string {
  const initData = getInitDataRaw();
  if (!initData) return '/api/export.csv';
  return `/api/export.csv?init_data=${encodeURIComponent(initData)}`;
}

export function buildZipExportUrl(): string {
  const initData = getInitDataRaw();
  if (!initData) return '/api/export.zip';
  return `/api/export.zip?init_data=${encodeURIComponent(initData)}`;
}
