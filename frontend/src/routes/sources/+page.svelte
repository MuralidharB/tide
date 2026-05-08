<script lang="ts">
  import type { PageData } from './$types';
  export let data: PageData;

  function daysSince(iso: string | null): number | null {
    if (!iso) return null;
    const d = new Date(iso).getTime();
    if (Number.isNaN(d)) return null;
    return Math.floor((Date.now() - d) / 86_400_000);
  }

  function fmtAge(iso: string | null): string {
    const days = daysSince(iso);
    if (days == null) return '—';
    if (days === 0) return 'today';
    if (days === 1) return '1 day ago';
    return `${days} days ago`;
  }

  function ageClass(iso: string | null, cadence: string): string {
    const days = daysSince(iso);
    if (days == null) return 'neu';
    // Stale thresholds rough by cadence:
    if (cadence === 'daily' && days > 5) return 'neg';
    if (cadence === 'weekly' && days > 14) return 'neg';
    if (cadence === 'monthly' && days > 60) return 'neg';
    if (cadence === 'quarterly' && days > 200) return 'neg';
    return 'pos';
  }

  $: rows = data.sources?.rows ?? [];
  $: liveCount = rows.filter((r) => r.status === 'live').length;
  $: stubCount = rows.filter((r) => r.status === 'stub').length;
</script>

<header class="header">
  <div>
    <h1 class="header-title">Sources <em>· ingestion health</em></h1>
    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-3); margin-top: 8px; letter-spacing: 0.05em;">
      {liveCount} live · {stubCount} stubbed · staleness shown vs each source's expected cadence
    </div>
  </div>
</header>

{#if data.error}
  <div class="aside-note" style="border-left-color: var(--neg); color: var(--neg);">
    <strong>Sources unreachable</strong>
    {data.error}
  </div>
{:else}
  <div class="watchlist">
    <div class="sources-header">
      <div>Metric</div>
      <div>Tier</div>
      <div>Source</div>
      <div>Cadence</div>
      <div>Latest obs</div>
      <div>Last ingest</div>
      <div>Obs count</div>
      <div>Status</div>
    </div>
    {#each rows as r (r.metric_id)}
      <div class="sources-row">
        <div class="src-id">
          <div class="src-name">{r.name}</div>
          <div class="src-mid">{r.metric_id}</div>
        </div>
        <div class="src-tier">{r.tier}</div>
        <div class="src-source">{r.source}</div>
        <div class="src-cadence">{r.cadence}</div>
        <div class="src-age {r.last_observation ? ageClass(r.last_observation, r.cadence) : 'neu'}">
          {r.last_observation ?? '—'}
          {#if r.last_observation}
            <span class="src-age-rel">{fmtAge(r.last_observation)}</span>
          {/if}
        </div>
        <div class="src-age">{fmtAge(r.last_ingested_at)}</div>
        <div class="src-count">{r.obs_count.toLocaleString()}</div>
        <div class="src-status {r.status}">{r.status}</div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .sources-header {
    display: grid;
    grid-template-columns: 1.6fr 60px 1.8fr 90px 1.6fr 1.2fr 90px 80px;
    padding: 12px 20px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-3);
    border-bottom: 1px solid var(--border-soft);
    background: var(--bg-elev);
  }
  .sources-row {
    display: grid;
    grid-template-columns: 1.6fr 60px 1.8fr 90px 1.6fr 1.2fr 90px 80px;
    padding: 12px 20px;
    align-items: center;
    border-bottom: 1px solid var(--border-soft);
    font-size: 12px;
  }
  .sources-row:last-child { border-bottom: none; }
  .src-name { color: var(--text); font-size: 13px; }
  .src-mid {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-3);
    margin-top: 2px;
  }
  .src-tier {
    font-family: var(--serif);
    font-style: italic;
    color: var(--text-2);
    font-size: 16px;
  }
  .src-source { font-family: var(--mono); font-size: 11px; color: var(--text-2); }
  .src-cadence, .src-count {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-2);
  }
  .src-age {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text);
  }
  .src-age.pos { color: var(--pos); }
  .src-age.neg { color: var(--neg); }
  .src-age.neu { color: var(--text-2); }
  .src-age-rel {
    display: block;
    font-size: 9px;
    color: var(--text-3);
    margin-top: 2px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .src-status {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 3px;
    justify-self: start;
  }
  .src-status.live {
    background: rgba(111, 207, 151, 0.12);
    color: var(--pos);
    border: 1px solid rgba(111, 207, 151, 0.28);
  }
  .src-status.stub {
    background: rgba(148, 139, 122, 0.08);
    color: var(--text-2);
    border: 1px solid rgba(148, 139, 122, 0.22);
  }
</style>
