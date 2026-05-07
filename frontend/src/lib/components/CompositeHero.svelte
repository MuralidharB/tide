<script lang="ts">
  import type { Composite, CompositeHistoryPoint } from '$lib/types';
  import CompositeChart from './CompositeChart.svelte';
  import Tally from './Tally.svelte';

  export let composite: Composite | null;
  export let metricsCount: number;
  export let history: CompositeHistoryPoint[] = [];

  $: signChar = composite && composite.z >= 0 ? '+' : composite ? '−' : '';
  $: absValue = composite ? Math.abs(composite.z).toFixed(2) : '—';
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
