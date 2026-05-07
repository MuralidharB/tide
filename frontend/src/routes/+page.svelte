<script lang="ts">
  import CompositeHero from '$lib/components/CompositeHero.svelte';
  import TierGrid from '$lib/components/TierGrid.svelte';
  import Watchlist from '$lib/components/Watchlist.svelte';
  import type { PageData } from './$types';

  export let data: PageData;

  $: dashboard = data.dashboard;
  $: watchlist = data.watchlist;
  $: error = data.error;
  $: now = new Date().toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  $: regime = dashboard?.composite
    ? dashboard.composite.z > 0.3
      ? 'Risk-on · Expansionary'
      : dashboard.composite.z < -0.3
      ? 'Risk-off · Contractionary'
      : 'Neutral · Trendless'
    : 'No data';
</script>

<header class="header">
  <div>
    <h1 class="header-title">Pressure Index <em>· composite read</em></h1>
    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-3); margin-top: 8px; letter-spacing: 0.05em;">
      Synthesis of liquidity · flow · microstructure · positioning · {dashboard?.composite?.metrics_total ?? 0} series live
    </div>
  </div>
  <div class="header-meta">
    <span class="regime-pill">{regime}</span>
    <span>{now}</span>
  </div>
</header>

{#if error}
  <div class="aside-note" style="border-left-color: var(--neg); color: var(--neg);">
    <strong>Backend unreachable</strong>
    {error}<br />
    Start the API with <code>make dev-api</code>, then <code>make ingest-m2</code> to load M2 from FRED.
  </div>
{:else if dashboard}
  <CompositeHero
    composite={dashboard.composite}
    metricsCount={dashboard.composite?.metrics_total ?? 0}
    history={dashboard.composite_history ?? []}
  />
  {#each dashboard.tiers as tier (tier.tier)}
    <TierGrid {tier} />
  {/each}
  {#if watchlist}
    <Watchlist {watchlist} />
  {/if}
{/if}

<div class="footer">
  <div>
    <span class="live-badge">● Live</span>
    <span style="margin-left: 16px;">{dashboard?.composite?.metrics_total ?? 0} of 19 metrics live · daily refresh</span>
  </div>
  <div>FRED · Yahoo · Treasury TIC · CFTC · AAII · SqueezeMetrics</div>
</div>
