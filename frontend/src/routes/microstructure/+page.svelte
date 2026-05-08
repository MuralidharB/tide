<script lang="ts">
  import TierFocusPage from '$lib/components/TierFocusPage.svelte';
  import type { PageData } from './$types';
  export let data: PageData;
</script>

<TierFocusPage
  dashboard={data.dashboard}
  tierNumber={3}
  pageTitle="Market Microstructure"
  subtitle="capacity to transact · daily"
/>
