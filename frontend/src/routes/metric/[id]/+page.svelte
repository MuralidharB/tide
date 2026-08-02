<script lang="ts">
  import MetricDetailChart from '$lib/components/MetricDetailChart.svelte';
  import Sparkline from '$lib/components/Sparkline.svelte';
  import type { PageData } from './$types';

  export let data: PageData;

  $: detail = data.detail;
  $: reading = detail.reading;

  const ROMAN = ['', 'I', 'II', 'III', 'IV'];
  const TIER_NAMES: Record<number, string> = {
    1: 'Macro Liquidity',
    2: 'Capital Flows',
    3: 'Market Microstructure',
    4: 'Sentiment & Positioning',
  };
  const TIER_HREFS: Record<number, string> = {
    1: '/macro-liquidity',
    2: '/capital-flows',
    3: '/microstructure',
    4: '/positioning',
  };
  const DIRECTION_LABEL: Record<string, string> = {
    natural: 'natural (higher is bullish)',
    inverted: 'inverted (lower is bullish)',
    contrarian_long: 'contrarian (extremes reverse the sign)',
  };
  const INDICATOR_LABEL: Record<string, string> = {
    level: 'level (raw value)',
    yoy: 'YoY % change',
  };

  $: sparkColor = reading
    ? reading.vote.direction === 'bull'
      ? 'var(--pos)'
      : reading.vote.direction === 'bear'
      ? 'var(--neg)'
      : 'var(--text-2)'
    : 'var(--text-2)';

  $: seriesFirst = detail.series[0];
  $: seriesLast = detail.series[detail.series.length - 1];
</script>

<header class="header">
  <div>
    <div style="font-family: var(--mono); font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-3); margin-bottom: 8px;">
      <a href={TIER_HREFS[detail.tier]} style="color: var(--text-3); text-decoration: none;">
        <em style="color: var(--text-2); font-style: italic; font-family: var(--serif); font-size: 14px; margin-right: 6px;">{ROMAN[detail.tier]}.</em>
        {TIER_NAMES[detail.tier]}
      </a>
    </div>
    <h1 class="header-title">{detail.name}</h1>
    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-3); margin-top: 8px; letter-spacing: 0.05em;">
      {detail.source} · {detail.cadence} · {detail.obs_count.toLocaleString()} obs
    </div>
  </div>
  {#if reading}
    <div class="header-meta" style="flex-direction: column; align-items: flex-end; gap: 4px;">
      <span class="detail-value {reading.z_class}">{reading.value}</span>
      <span style="font-family: var(--mono); font-size: 11px; color: var(--text-2);">
        {reading.z_label}
      </span>
    </div>
  {/if}
</header>

{#if detail.description}
  <div class="aside-note">
    <strong>What is this?</strong>
    {detail.description}
  </div>
{/if}

{#if reading}
  <div class="detail-reading">
    <div class="dr-block">
      <div class="dr-label">Latest value</div>
      <div class="dr-value {reading.z_class}">{reading.value}</div>
      <div class="dr-sub">{reading.unit} · as of {new Date(reading.as_of).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'})}</div>
    </div>
    <div class="dr-block">
      <div class="dr-label">Z-score (3y rolling)</div>
      <div class="dr-value {reading.z_class}">{reading.z_label}</div>
      <div class="dr-sub">
        <span class="delta {reading.delta_class}">{reading.delta}</span>
      </div>
    </div>
    <div class="dr-block">
      <div class="dr-label">Vote</div>
      <div class="dr-vote">
        <span class="vote-chip {reading.vote.direction}">
          <span class="arrow">{reading.vote.direction === 'bull' ? '↑' : reading.vote.direction === 'bear' ? '↓' : '—'}</span>{reading.vote.direction.charAt(0).toUpperCase() + reading.vote.direction.slice(1)}
        </span>
      </div>
      <div class="dr-sub" style="font-family: var(--serif); font-style: italic; font-variation-settings: 'opsz' 14; line-height: 1.35;">
        {reading.vote.reason}
      </div>
    </div>
    <div class="dr-block">
      <div class="dr-label">Recent trend</div>
      <div style="margin: 6px 0;">
        <Sparkline data={reading.sparkline} color={sparkColor} height={38} />
      </div>
      <div class="dr-sub">Last {reading.sparkline.length} readings</div>
    </div>
  </div>
{/if}

<section style="margin-top: 32px;">
  <h2 class="section-title">
    Full history <em>· {detail.series.length.toLocaleString()} points{#if seriesFirst && seriesLast} · {seriesFirst.ts} → {seriesLast.ts}{/if}</em>
  </h2>
  <MetricDetailChart series={detail.series} unit={detail.unit} color={sparkColor} />
  <div style="margin-top: 10px; font-family: var(--mono); font-size: 10px; color: var(--text-3); letter-spacing: 0.05em;">
    Bands are ±1σ / ±2σ around the visible mean · μ line dashed
  </div>
</section>

<section class="detail-metadata">
  <h2 class="section-title">Registry <em>· how this metric is configured</em></h2>
  <div class="meta-grid">
    <div><span class="meta-label">Metric ID</span><span class="meta-val mono">{detail.metric_id}</span></div>
    <div><span class="meta-label">Tier</span><span class="meta-val">{ROMAN[detail.tier]} · {TIER_NAMES[detail.tier]}</span></div>
    <div><span class="meta-label">Source</span><span class="meta-val">{detail.source}</span></div>
    <div><span class="meta-label">Upstream series</span><span class="meta-val mono">{detail.source_series ?? '—'}</span></div>
    <div><span class="meta-label">Cadence</span><span class="meta-val">{detail.cadence}</span></div>
    <div><span class="meta-label">Unit</span><span class="meta-val">{detail.unit}</span></div>
    <div><span class="meta-label">Indicator kind</span><span class="meta-val">{INDICATOR_LABEL[detail.indicator_kind]}</span></div>
    {#if detail.indicator_kind === 'yoy'}
      <div><span class="meta-label">YoY lag</span><span class="meta-val mono">{detail.indicator_lag} periods</span></div>
    {/if}
    <div><span class="meta-label">Rolling z window</span><span class="meta-val mono">{detail.indicator_window} periods ({detail.zscore_years}y)</span></div>
    <div><span class="meta-label">Direction</span><span class="meta-val">{DIRECTION_LABEL[detail.direction_kind]}</span></div>
    <div><span class="meta-label">In composite</span>
      <span class="meta-val">
        {detail.include_in_composite ? 'yes' : 'no · loadedness gauge'}
      </span>
    </div>
    <div><span class="meta-label">Raw observations</span><span class="meta-val mono">{detail.obs_count.toLocaleString()}</span></div>
  </div>
</section>

<style>
  .detail-value {
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-weight: 400;
    font-size: 42px;
    line-height: 1;
    letter-spacing: -0.02em;
  }
  .detail-value.pos { color: var(--pos); }
  .detail-value.neg { color: var(--neg); }
  .detail-value.neu { color: var(--text); }

  .detail-reading {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 24px;
    padding: 20px 24px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px;
  }
  .dr-block { min-width: 0; }
  .dr-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 6px;
  }
  .dr-value {
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 26px;
    line-height: 1;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
  }
  .dr-value.pos { color: var(--pos); }
  .dr-value.neg { color: var(--neg); }
  .dr-value.neu { color: var(--text); }
  .dr-sub {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-2);
    line-height: 1.4;
  }
  .dr-sub .delta { font-weight: 500; }
  .dr-sub .delta.pos { color: var(--pos); }
  .dr-sub .delta.neg { color: var(--neg); }
  .dr-vote { margin: 6px 0; }

  .detail-metadata { margin-top: 40px; }
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 10px 24px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 18px 22px;
  }
  .meta-grid > div {
    display: grid;
    grid-template-columns: 140px 1fr;
    align-items: baseline;
    gap: 12px;
    padding: 4px 0;
    border-bottom: 1px dashed var(--border-soft);
  }
  .meta-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-3);
    letter-spacing: 0.06em;
  }
  .meta-val {
    color: var(--text-2);
    font-size: 12px;
  }
  .meta-val.mono {
    font-family: var(--mono);
    color: var(--text);
  }
</style>
