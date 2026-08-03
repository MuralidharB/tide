<script lang="ts">
  import type { Composite, CompositeHistoryPoint } from '$lib/types';
  import CompositeChart from './CompositeChart.svelte';
  import Tally from './Tally.svelte';

  export let composite: Composite | null;
  export let metricsCount: number;
  export let history: CompositeHistoryPoint[] = [];

  $: signChar = composite && composite.z >= 0 ? '+' : composite ? '−' : '';
  $: absValue = composite ? Math.abs(composite.z).toFixed(2) : '—';

  // Latest per-tier decomposition — pulled from the last composite_history point.
  $: latestPoint = history.length > 0 ? history[history.length - 1] : null;
  $: tierZs = latestPoint?.tier_zs ?? {};

  const TIER_META: Record<number, { name: string; href: string; color: string }> = {
    1: { name: 'Macro Liquidity',   href: '/macro-liquidity', color: '#4A8FE7' },
    2: { name: 'Capital Flows',     href: '/capital-flows',   color: '#B97AE0' },
    3: { name: 'Microstructure',    href: '/microstructure',  color: '#5DD3C0' },
    4: { name: 'Sentiment/Position',href: '/positioning',     color: '#F4C95D' },
  };

  function fmtZ(v: number | null | undefined): string {
    if (v == null) return '—';
    return `${v >= 0 ? '+' : ''}${v.toFixed(2)}σ`;
  }
</script>

<section class="composite">
  <div>
    <div class="composite-label">Composite Reading</div>
    <div class="composite-name">Capital pressure index</div>
    {#if composite}
      <div class="composite-value {composite.sign_class}">
        <span class="sign">{signChar}</span>{absValue}
        <span style="font-size: 28px; color: var(--text-3); font-family: var(--mono); margin-left: 12px; align-self: center;">σ</span>
      </div>

      {#if Object.keys(tierZs).length > 0}
        <div class="tier-decomp">
          <div class="tier-decomp-label">Composed of</div>
          <div class="tier-decomp-row">
            {#each [1, 2, 3, 4] as tier}
              {@const val = tierZs[String(tier)]}
              {@const meta = TIER_META[tier]}
              <a class="tier-chip" href={meta.href}>
                <span class="tier-chip-dot" style="background: {meta.color}"></span>
                <span class="tier-chip-name">{meta.name}</span>
                <span class="tier-chip-val" style="color: {val != null ? meta.color : 'var(--text-3)'}">
                  {fmtZ(val)}
                </span>
              </a>
            {/each}
          </div>
        </div>
      {/if}

      <div class="composite-vote">
        <div class="composite-vote-label">Vote tally · {metricsCount} indicator{metricsCount === 1 ? '' : 's'}</div>
        <div class="composite-tally">
          <Tally tally={composite.tally} withLabels={true} />
        </div>
      </div>
    {:else}
      <div class="composite-value neu"><span class="sign">·</span>—</div>
      <div class="composite-vote">
        <div class="composite-vote-label">No metrics ingested yet</div>
      </div>
    {/if}
  </div>

  <CompositeChart {history} />
</section>

<style>
  .tier-decomp {
    margin-top: 18px;
    padding-top: 16px;
    border-top: 1px solid var(--border-soft);
  }
  .tier-decomp-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 8px;
  }
  .tier-decomp-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 12px;
  }
  .tier-chip {
    display: grid;
    grid-template-columns: 8px 1fr auto;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 3px;
    text-decoration: none;
    color: inherit;
    transition: border-color 0.12s, background 0.12s;
  }
  .tier-chip:hover {
    border-color: rgba(244, 201, 93, 0.4);
    background: var(--bg-card-hover);
  }
  .tier-chip-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .tier-chip-name {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.06em;
    color: var(--text-2);
    text-transform: uppercase;
  }
  .tier-chip-val {
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 13px;
    font-weight: 500;
    text-align: right;
  }
</style>
