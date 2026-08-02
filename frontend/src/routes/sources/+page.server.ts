import { fetchScheduler, fetchSources } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const [sources, scheduler] = await Promise.all([
      fetchSources(fetch),
      fetchScheduler(fetch).catch(() => null)
    ]);
    return { sources, scheduler, error: null };
  } catch (err) {
    return {
      sources: null,
      scheduler: null,
      error: err instanceof Error ? err.message : String(err)
    };
  }
};
