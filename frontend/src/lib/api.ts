import { env } from '$env/dynamic/private';
import type { Dashboard, MetricDetail, SchedulerPayload, SourcesPayload, TierHistory, Watchlist } from './types';

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

export async function fetchSources(fetch: typeof globalThis.fetch): Promise<SourcesPayload> {
  const res = await fetch(`${API_URL}/api/sources`);
  if (!res.ok) throw new Error(`Sources fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchScheduler(fetch: typeof globalThis.fetch): Promise<SchedulerPayload> {
  const res = await fetch(`${API_URL}/api/scheduler`);
  if (!res.ok) throw new Error(`Scheduler fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchMetricDetail(
  fetch: typeof globalThis.fetch,
  id: string
): Promise<MetricDetail> {
  const res = await fetch(`${API_URL}/api/metrics/${encodeURIComponent(id)}/detail`);
  if (!res.ok) throw new Error(`Metric ${id} fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchTierHistory(
  fetch: typeof globalThis.fetch,
  tier: number
): Promise<TierHistory> {
  const res = await fetch(`${API_URL}/api/tier/${tier}/history`);
  if (!res.ok) throw new Error(`Tier ${tier} history fetch failed: ${res.status} ${res.statusText}`);
  return res.json();
}
