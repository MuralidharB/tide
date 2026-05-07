import { env } from '$env/dynamic/private';
import type { Dashboard, Watchlist } from './types';

// SvelteKit loads .env via Vite (envDir: '..' in vite.config.ts). $env/dynamic/private
// reads non-VITE-prefixed vars at request time, server-side only.
const API_URL = env.TIDE_API_URL ?? 'http://127.0.0.1:8765';

/** Server-side fetch helper. Pass through SvelteKit's `fetch` for hot-module support. */
export async function fetchDashboard(fetch: typeof globalThis.fetch): Promise<Dashboard> {
  const res = await fetch(`${API_URL}/api/dashboard`);
  if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchWatchlist(fetch: typeof globalThis.fetch): Promise<Watchlist> {
  const res = await fetch(`${API_URL}/api/watchlist`);
  if (!res.ok) throw new Error(`Watchlist fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}
