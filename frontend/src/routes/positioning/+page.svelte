<script lang="ts">
  import TierFocusPage from '$lib/components/TierFocusPage.svelte';
  import type { PageData } from './$types';
  export let data: PageData;
</script>

<TierFocusPage
  dashboard={data.dashboard}
  tierNumber={4}
  pageTitle="Sentiment & Positioning"
  subtitle="willingness to transact · days–weeks"
  history={data.history}
/>
