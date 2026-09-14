import api from '@/services/api';

/**
 * Resolves a storage file path (from MinIO/S3 or database) to a full accessible URL.
 * Works seamlessly in local dev, Vite proxy, and production Docker setups.
 */
export function resolveStorageUrl(path?: string | null): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path;
  }
  if (path.startsWith('/avatars/') || path.startsWith('avatars/') || path.startsWith('/assets/')) {
    return path.startsWith('/') ? path : `/${path}`;
  }
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  let rawBase = api.defaults.baseURL || '';
  if (rawBase.endsWith('/')) {
    rawBase = rawBase.slice(0, -1);
  }
  return `${rawBase}/storage/${cleanPath}`;
}
