import { fetchDashboard } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const dashboard = await fetchDashboard(fetch);
    return { dashboard, error: null };
  } catch (err) {
    return { dashboard: null, error: err instanceof Error ? err.message : String(err) };
  }
};
