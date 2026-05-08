<script lang="ts">
  import TierFocusPage from '$lib/components/TierFocusPage.svelte';
  import type { PageData } from './$types';
  export let data: PageData;
</script>

<TierFocusPage
  dashboard={data.dashboard}
  tierNumber={2}
  pageTitle="Capital Flows"
  subtitle="capital direction · months"
/>
