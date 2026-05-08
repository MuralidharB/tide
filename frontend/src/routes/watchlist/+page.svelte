<script lang="ts">
  import Watchlist from '$lib/components/Watchlist.svelte';
  import type { PageData } from './$types';
  export let data: PageData;
</script>

<header class="header">
  <div>
    <h1 class="header-title">Watchlist <em>· healthcare de-rated quality</em></h1>
    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-3); margin-top: 8px; letter-spacing: 0.05em;">
      Edit <code>watchlist.toml</code> to adjust targets, P/E, or status. Live fields refresh via
      <code>make ingest-watchlist</code>.
    </div>
  </div>
</header>

{#if data.error}
  <div class="aside-note" style="border-left-color: var(--neg); color: var(--neg);">
    <strong>Watchlist unreachable</strong>
    {data.error}
  </div>
{:else if data.watchlist}
  <Watchlist watchlist={data.watchlist} />
{/if}
