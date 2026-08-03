<script lang="ts">
  import type { DetailPoint } from '$lib/types';

  export let series: DetailPoint[] = [];
  export let unit: string = '';
  export let color: string = 'var(--pos)';

  const W = 800;
  const H = 260;
  const padX = 60;    // extra room for y-axis value labels
  const padRight = 24;
  const padTop = 20;
  const padBottom = 20;
  const TICK_COUNT = 6;

  $: hasData = series.length >= 2;

  // ── y-scale from indicator values (all points, not just z-valid) ────────
  $: yMin = hasData ? Math.min(...series.map((p) => p.indicator)) : 0;
  $: yMax = hasData ? Math.max(...series.map((p) => p.indicator)) : 1;
  $: yRange = yMax - yMin || 1;
  $: yPad = yRange * 0.08;     // 8% headroom on both sides

  function yFor(v: number): number {
    const min = yMin - yPad;
    const max = yMax + yPad;
    const range = max - min || 1;
    return padTop + (H - padTop - padBottom) * (1 - (v - min) / range);
  }
  function xFor(i: number): number {
    if (series.length <= 1) return padX;
    return padX + ((W - padX - padRight) * i) / (series.length - 1);
  }
  function xPctFor(i: number): number {
    return (xFor(i) / W) * 100;
  }

  // ── ±1σ / ±2σ bands: computed from the indicator series' rolling μ, σ
  //    that produced each z. If we solve z = (v - μ) / σ, we can back out
  //    μ and σ at each point using the LATEST indicator + z. But easier:
  //    reconstruct band values as `series[i].indicator - series[i].z*σᵢ ± σᵢ`
  //    where σᵢ = (indicator - mean) / z … requires two points to derive.
  //
  //    Simpler approach: draw horizontal reference bands using the current-
  //    window mean and stdev, computed from the last N valid z-points via
  //    inversion:
  //       stdev = (indicator - mean) / z, but that needs mean.
  //    So instead we just derive mean and stdev directly from the indicator
  //    series over the same window depth that produced z.
  //
  //    Cleanest: compute over the full visible series. Not exactly the
  //    rolling window, but a good visual approximation and stable.
  $: mean = hasData ? series.reduce((s, p) => s + p.indicator, 0) / series.length : 0;
  $: variance = hasData
    ? series.reduce((s, p) => s + (p.indicator - mean) ** 2, 0) / Math.max(1, series.length - 1)
    : 0;
  $: sigma = Math.sqrt(variance);

  // ── Paths ───────────────────────────────────────────────────────────────
  $: linePath = (() => {
    if (!hasData) return '';
    return series
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i).toFixed(1)} ${yFor(p.indicator).toFixed(1)}`)
      .join(' ');
  })();

  $: latest = hasData ? series[series.length - 1] : null;
  $: latestX = latest ? xFor(series.length - 1) : 0;
  $: latestY = latest ? yFor(latest.indicator) : 0;

  // ── Timeline ────────────────────────────────────────────────────────────
  function fmtTick(iso: string, spanMonths: number): string {
    const d = new Date(iso);
    if (spanMonths >= 60) {
      return d.toLocaleDateString('en-US', { year: 'numeric' });
    }
    if (spanMonths >= 12) {
      return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    }
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  $: spanMonths = (() => {
    if (!hasData) return 0;
    const a = new Date(series[0].ts).getTime();
    const b = new Date(series[series.length - 1].ts).getTime();
    return (b - a) / (1000 * 60 * 60 * 24 * 30.44);
  })();
  $: timelineTicks = (() => {
    if (!hasData) return [];
    const n = series.length;
    const out: { idx: number; label: string; pct: number }[] = [];
    for (let k = 0; k < TICK_COUNT; k++) {
      const idx = Math.round((k * (n - 1)) / (TICK_COUNT - 1));
      out.push({ idx, label: fmtTick(series[idx].ts, spanMonths), pct: xPctFor(idx) });
    }
    return out;
  })();

  // ── y-axis labels ───────────────────────────────────────────────────────
  function fmtValue(v: number): string {
    const abs = Math.abs(v);
    if (abs >= 1e9) return (v / 1e9).toFixed(1) + 'B';
    if (abs >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (abs >= 100) return v.toFixed(0);
    if (abs >= 1) return v.toFixed(2);
    return v.toFixed(3);
  }
  $: yAxisLabels = (() => {
    if (!hasData) return [];
    return [
      { v: yMax, label: fmtValue(yMax) },
      { v: mean, label: fmtValue(mean) + ' μ' },
      { v: yMin, label: fmtValue(yMin) },
    ];
  })();

  // ── Hover ───────────────────────────────────────────────────────────────
  let container: HTMLDivElement | null = null;
  let hoverIdx: number | null = null;

  function onMouseMove(e: MouseEvent) {
    if (!container || !hasData) return;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const svgX = (x / rect.width) * W;
    const step = (W - padX - padRight) / Math.max(1, series.length - 1);
    const raw = (svgX - padX) / step;
    hoverIdx = Math.max(0, Math.min(series.length - 1, Math.round(raw)));
  }
  function onMouseLeave() {
    hoverIdx = null;
  }

  $: hover = hoverIdx != null && hasData ? series[hoverIdx] : null;
  $: hoverX = hoverIdx != null ? xFor(hoverIdx) : 0;
  $: hoverXPct = hoverIdx != null ? xPctFor(hoverIdx) : 0;
  $: hoverYPct = hover ? (yFor(hover.indicator) / H) * 100 : 0;
  $: hoverDateFmt = hover
    ? new Date(hover.ts).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';
  $: tooltipAlign = hoverXPct > 82 ? 'right' : hoverXPct < 12 ? 'left' : 'center';
</script>

<div
  class="detail-chart-container"
  bind:this={container}
  on:mousemove={onMouseMove}
  on:mouseleave={onMouseLeave}
  role="presentation"
>
  <svg class="detail-svg" viewBox="0 0 {W} {H}" preserveAspectRatio="none">
    <defs>
      <linearGradient id="detailGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color={color} stop-opacity="0.15" />
        <stop offset="100%" stop-color={color} stop-opacity="0" />
      </linearGradient>
    </defs>

    <!-- Reference bands: ±1σ (light) and ±2σ (lighter) around μ -->
    {#if hasData && sigma > 0}
      <rect
        x={padX}
        y={yFor(mean + sigma)}
        width={W - padX - padRight}
        height={Math.max(0, yFor(mean - sigma) - yFor(mean + sigma))}
        fill={color}
        opacity="0.05"
      />
      <line
        x1={padX} x2={W - padRight}
        y1={yFor(mean)} y2={yFor(mean)}
        stroke="#5C544A" stroke-width="0.5" stroke-dasharray="3,4"
      />
      <line
        x1={padX} x2={W - padRight}
        y1={yFor(mean + sigma)} y2={yFor(mean + sigma)}
        stroke="#B5AC94" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.7"
      />
      <line
        x1={padX} x2={W - padRight}
        y1={yFor(mean - sigma)} y2={yFor(mean - sigma)}
        stroke="#B5AC94" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.7"
      />
      <line
        x1={padX} x2={W - padRight}
        y1={yFor(mean + 2 * sigma)} y2={yFor(mean + 2 * sigma)}
        stroke="#B5AC94" stroke-width="0.4" stroke-dasharray="1,6" opacity="0.4"
      />
      <line
        x1={padX} x2={W - padRight}
        y1={yFor(mean - 2 * sigma)} y2={yFor(mean - 2 * sigma)}
        stroke="#B5AC94" stroke-width="0.4" stroke-dasharray="1,6" opacity="0.4"
      />

      <!-- y-axis labels -->
      {#each yAxisLabels as lab (lab.label)}
        <text x="6" y={yFor(lab.v) + 3} font-family="JetBrains Mono" font-size="9" fill="#948B7A">
          {lab.label}
        </text>
      {/each}
      <text x={padX + 6} y={yFor(mean + sigma) - 3} font-family="JetBrains Mono" font-size="9" fill="#948B7A" opacity="0.7">
        +1σ
      </text>
      <text x={padX + 6} y={yFor(mean - sigma) + 11} font-family="JetBrains Mono" font-size="9" fill="#948B7A" opacity="0.7">
        −1σ
      </text>
    {/if}

    {#if hasData}
      <path d={linePath} fill="none" stroke={color} stroke-width="1.5" stroke-linejoin="round" />
      <circle cx={latestX} cy={latestY} r="3.5" fill={color} />
      <circle cx={latestX} cy={latestY} r="8" fill={color} opacity="0.3" />

      {#if hoverIdx != null && hover}
        <line
          x1={hoverX} x2={hoverX} y1={padTop} y2={H - padBottom}
          stroke="var(--text-2)" stroke-width="0.7" stroke-dasharray="2,3" opacity="0.5"
        />
      {/if}
    {:else}
      <text x={W / 2} y={H / 2} font-family="JetBrains Mono" font-size="11" fill="#948B7A" text-anchor="middle">
        No data
      </text>
    {/if}
  </svg>

  {#if hasData && hoverIdx != null && hover}
    <div class="hover-dot" style="left: {hoverXPct}%; top: {hoverYPct}%; background: {color};"></div>
    <div class="chart-tooltip align-{tooltipAlign}" style="left: {hoverXPct}%;">
      <div class="tt-date">{hoverDateFmt}</div>
      <div class="tt-row">
        <span class="tt-swatch" style="background: {color}"></span>
        <span class="tt-label">{unit}</span>
        <span class="tt-val" style="color: {color}">{fmtValue(hover.indicator)}</span>
      </div>
      {#if hover.z != null}
        <div class="tt-row">
          <span class="tt-swatch" style="background: transparent; border: 1px dashed var(--text-3)"></span>
          <span class="tt-label">z-score</span>
          <span class="tt-val">
            {hover.z >= 0 ? '+' : ''}{hover.z.toFixed(2)}σ
          </span>
        </div>
      {/if}
    </div>
  {/if}
</div>

{#if hasData}
  <div class="detail-timeline">
    {#each timelineTicks as tick (tick.idx)}
      <span class="tl-label" style="left: {tick.pct}%">{tick.label}</span>
    {/each}
  </div>
{/if}

<style>
  .detail-chart-container {
    position: relative;
    width: 100%;
    height: 260px;
  }
  .detail-svg {
    width: 100%;
    height: 100%;
    display: block;
  }
  .detail-timeline {
    position: relative;
    height: 16px;
    margin-top: 6px;
    border-top: 1px solid var(--border-soft);
  }
  .tl-label {
    position: absolute;
    top: 4px;
    transform: translateX(-50%);
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.08em;
    color: var(--text-3);
    white-space: nowrap;
  }
  .hover-dot {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 0 2px var(--bg-card);
    pointer-events: none;
  }
  .chart-tooltip {
    position: absolute;
    top: -6px;
    transform: translateX(-50%);
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 8px 12px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.04em;
    line-height: 1.4;
    color: var(--text);
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    z-index: 2;
    min-width: 200px;
  }
  .chart-tooltip.align-left  { transform: translateX(0); }
  .chart-tooltip.align-right { transform: translateX(-100%); }
  .tt-date {
    color: var(--text-3);
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .tt-row {
    display: grid;
    grid-template-columns: 10px auto 1fr;
    align-items: baseline;
    gap: 8px;
    padding: 2px 0;
  }
  .tt-swatch {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .tt-label {
    color: var(--text-2);
    font-size: 10px;
  }
  .tt-val {
    text-align: right;
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
  }
</style>
