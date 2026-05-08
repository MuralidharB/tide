import { fetchWatchlist } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const watchlist = await fetchWatchlist(fetch);
    return { watchlist, error: null };
  } catch (err) {
    return { watchlist: null, error: err instanceof Error ? err.message : String(err) };
  }
};
