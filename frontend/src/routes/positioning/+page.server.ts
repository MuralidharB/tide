import { fetchDashboard, fetchTierHistory } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const [dashboard, history] = await Promise.all([
      fetchDashboard(fetch),
      fetchTierHistory(fetch, 4).catch(() => null)
    ]);
    return { dashboard, history, error: null };
  } catch (err) {
    return { dashboard: null, history: null, error: err instanceof Error ? err.message : String(err) };
  }
};
