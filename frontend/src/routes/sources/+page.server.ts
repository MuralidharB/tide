import { fetchSources } from '$lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const sources = await fetchSources(fetch);
    return { sources, error: null };
  } catch (err) {
    return { sources: null, error: err instanceof Error ? err.message : String(err) };
  }
};
