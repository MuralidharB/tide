import { fetchDashboard, fetchWatchlist } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const [dashboard, watchlist] = await Promise.all([
      fetchDashboard(fetch),
      fetchWatchlist(fetch).catch(() => null)
    ]);
    return { dashboard, watchlist, error: null };
  } catch (err) {
    return {
      dashboard: null,
      watchlist: null,
      error: err instanceof Error ? err.message : String(err)
    };
  }
};
