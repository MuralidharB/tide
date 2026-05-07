<script lang="ts">
  import type { Watchlist } from '$lib/types';
  import Sparkline from './Sparkline.svelte';

  export let watchlist: Watchlist;

  function fmt(v: number | null, digits = 2): string {
    return v == null ? '—' : v.toFixed(digits);
  }
  function pct(v: number | null): string {
    return v == null ? '—' : `${(v * 100 >= 0 ? '+' : '')}${(v * 100).toFixed(1)}%`;
  }

  function relColor(rel: number | null): string {
    if (rel == null) return 'var(--text-2)';
    return rel >= 0 ? 'var(--pos)' : 'var(--neg)';
  }
</script>

<section class="watchlist-section">
  <h2 class="section-title">Watchlist <em>· healthcare de-rated quality</em></h2>
  <div class="watchlist">
    <div class="watchlist-header">
      <div>Ticker</div>
      <div>Company</div>
      <div>Price</div>
      <div>Target</div>
      <div>Fwd P/E</div>
      <div>Status</div>
      <div>30D · relative to {watchlist.benchmark}</div>
    </div>
    {#each watchlist.rows as r (r.ticker)}
      <div class="watchlist-row">
        <div class="wl-ticker">{r.ticker}</div>
        <div class="wl-name">{r.name}<span>{r.sub}</span></div>
        <div class="wl-price">{r.price != null ? `$${fmt(r.price)}` : '—'}</div>
        <div class="wl-target">${fmt(r.target, 0)}</div>
        <div class="wl-pe">{r.fwd_pe}</div>
        <div class="wl-status {r.status}">{r.status}</div>
        <div class="wl-spark-cell">
          <Sparkline data={r.sparkline} color={relColor(r.return_30d_relative)} height={28} strokeWidth={1.3} pad={2} />
          <span class="wl-rel" style="color: {relColor(r.return_30d_relative)};">{pct(r.return_30d_relative)}</span>
        </div>
      </div>
    {/each}
  </div>
</section>

<style>
  .wl-spark-cell {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 12px;
  }
  .wl-rel {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 500;
  }
</style>
