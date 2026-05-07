<script lang="ts">
  import type { Tier } from '$lib/types';
  import MetricCard from './MetricCard.svelte';
  import Tally from './Tally.svelte';

  export let tier: Tier;

  const ROMAN = ['', 'I', 'II', 'III', 'IV'];

  $: tally = {
    bull: tier.metrics.filter((m) => m.vote.direction === 'bull').length,
    neutral: tier.metrics.filter((m) => m.vote.direction === 'neutral').length,
    bear: tier.metrics.filter((m) => m.vote.direction === 'bear').length
  };
</script>

<section class="tier tier-{tier.tier}">
  <div class="tier-header">
    <span class="tier-numeral">{ROMAN[tier.tier]}</span>
    <h2 class="tier-name">{tier.name}</h2>
    <span class="tier-tag">{tier.tag}</span>
    {#if tier.metrics.length > 0}
      <Tally {tally} />
    {/if}
    <span class="tier-cadence">{tier.cadence}</span>
  </div>

  {#if tier.metrics.length === 0}
    <div class="tier-empty">No metrics ingested for this tier yet.</div>
  {:else}
    <div class="tier-grid">
      {#each tier.metrics as reading (reading.metric_id)}
        <MetricCard {reading} />
      {/each}
    </div>
  {/if}
</section>
