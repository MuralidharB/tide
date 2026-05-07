<script lang="ts">
  import type { Tally } from '$lib/types';

  export let tally: Tally;
  export let withLabels: boolean = false;
</script>

<span class="tier-tally">
  <span class="tally-segment bull"><span class="arrow">↑</span>{tally.bull}{#if withLabels}&nbsp;bull{/if}</span>
  <span class="tally-segment neutral"><span class="arrow">—</span>{tally.neutral}{#if withLabels}&nbsp;neutral{/if}</span>
  <span class="tally-segment bear"><span class="arrow">↓</span>{tally.bear}{#if withLabels}&nbsp;bear{/if}</span>
</span>
