<script lang="ts">
  import TierFocusPage from '$lib/components/TierFocusPage.svelte';
  import type { PageData } from './$types';
  export let data: PageData;
</script>

<TierFocusPage
  dashboard={data.dashboard}
  tierNumber={1}
  pageTitle="Macro Liquidity"
  subtitle="the base · multi-year"
  history={data.history}
/>
