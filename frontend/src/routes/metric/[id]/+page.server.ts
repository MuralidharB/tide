import { error } from '@sveltejs/kit';
import { fetchMetricDetail } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params }) => {
  try {
    const detail = await fetchMetricDetail(fetch, params.id);
    return { detail };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes('404')) {
      throw error(404, `Unknown metric: ${params.id}`);
    }
    throw error(500, msg);
  }
};
