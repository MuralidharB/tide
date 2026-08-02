<script lang="ts">
  import type { Reading } from '$lib/types';
  import Sparkline from './Sparkline.svelte';

  export let reading: Reading;

  const arrowFor = (direction: string) =>
    direction === 'bull' ? '↑' : direction === 'bear' ? '↓' : '—';
  const labelFor = (direction: string) =>
    direction === 'bull' ? 'Bull' : direction === 'bear' ? 'Bear' : 'Neutral';

  $: sparkColor =
    reading.vote.direction === 'bull'
      ? 'var(--pos)'
      : reading.vote.direction === 'bear'
      ? 'var(--neg)'
      : 'var(--text-2)';

  $: asOf = new Date(reading.as_of).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
</script>

<div class="metric">
  <div class="metric-top">
    <div>
      <div class="metric-name">{reading.name}</div>
      <div class="metric-source">{reading.source} · as of {asOf}</div>
      {#if !reading.include_in_composite}
        <div class="loadedness-chip" title="Loadedness gauge — held out of the directional composite">
          not in composite
        </div>
      {/if}
    </div>
    <span class="metric-z {reading.z_class}">{reading.z_label}</span>
  </div>
  <div class="metric-value">{reading.value}</div>
  <div class="metric-change">
    {reading.unit} · <span class="delta {reading.delta_class}">{reading.delta}</span>
  </div>
  <Sparkline data={reading.sparkline} color={sparkColor} />
  <div class="metric-vote">
    <span class="vote-chip {reading.vote.direction}">
      <span class="arrow">{arrowFor(reading.vote.direction)}</span>{labelFor(reading.vote.direction)}
    </span>
    <span class="vote-reason">{reading.vote.reason}</span>
  </div>
</div>
