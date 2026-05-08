<script lang="ts">
  import type { Dashboard, Tier } from '$lib/types';
  import TierGrid from './TierGrid.svelte';

  export let dashboard: Dashboard | null;
  export let tierNumber: 1 | 2 | 3 | 4;
  export let pageTitle: string;
  export let subtitle: string;

  const ROMAN = ['', 'I', 'II', 'III', 'IV'];

  $: tier = dashboard?.tiers.find((t) => t.tier === tierNumber) ?? null;
  $: tierAvg = tier?.avg_z != null ? tier.avg_z : null;

  function fmtZ(v: number | null): string {
    if (v == null) return '—';
    return `${v >= 0 ? '+' : ''}${v.toFixed(2)}σ`;
  }

  $: avgClass =
    tierAvg == null ? 'neu' : tierAvg > 0.3 ? 'pos' : tierAvg < -0.3 ? 'neg' : 'neu';
</script>

<header class="header">
  <div>
    <h1 class="header-title">
      <span style="color: var(--text-3); font-style: italic; font-weight: 300; margin-right: 12px;">{ROMAN[tierNumber]}.</span>
      {pageTitle} <em>· {subtitle}</em>
    </h1>
    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-3); margin-top: 8px; letter-spacing: 0.05em;">
      {tier?.cadence ?? ''}
    </div>
  </div>
  <div class="header-meta">
    <span class="composite-meta-value {avgClass}" style="font-size: 28px; font-family: var(--serif);">
      {fmtZ(tierAvg)}
    </span>
    <span style="font-family: var(--mono); font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-3);">
      Tier average
    </span>
  </div>
</header>

{#if tier}
  <TierGrid {tier} />
{:else}
  <div class="aside-note">
    <strong>No data</strong>
    Dashboard payload missing tier {tierNumber}.
  </div>
{/if}
