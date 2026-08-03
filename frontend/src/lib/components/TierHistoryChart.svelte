<script lang="ts">
  import type { TierHistoryPoint } from '$lib/types';

  export let history: TierHistoryPoint[] = [];
  export let tierNumber: 1 | 2 | 3 | 4;
  export let tierName: string;

  const W = 800;
  const H = 200;
  const padX = 32;
  const padRight = 30;
  const padTop = 16;
  const padBottom = 16;

  // Wider z-range for tier averages: a single tier can swing further than the
  // 4-tier-mean composite. ±2.5σ still keeps the plot area meaningful.
  const zMin = -2.5;
  const zMax = 2.5;

  const TICK_COUNT = 6;
  const TIER_COLORS: Record<number, string> = {
    1: '#4A8FE7',
    2: '#B97AE0',
    3: '#5DD3C0',
    4: '#F4C95D',
  };

  $: color = TIER_COLORS[tierNumber];
  $: hasData = history.length >= 2;

  function yFor(z: number): number {
    const c = Math.max(zMin, Math.min(zMax, z));
    return padTop + (H - padTop - padBottom) * (1 - (c - zMin) / (zMax - zMin));
  }
  function xFor(i: number): number {
    if (history.length <= 1) return padX;
    return padX + ((W - padX - padRight) * i) / (history.length - 1);
  }
  function xPctFor(i: number): number { return (xFor(i) / W) * 100; }

  $: linePath = hasData
    ? history.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i).toFixed(1)} ${yFor(p.z).toFixed(1)}`).join(' ')
    : '';

  $: fillPath = (() => {
    if (!hasData) return '';
    const baseY = yFor(0);
    const lastX = xFor(history.length - 1);
    return linePath + ` L ${lastX.toFixed(1)} ${baseY.toFixed(1)} L ${padX} ${baseY.toFixed(1)} Z`;
  })();

  $: latest = hasData ? history[history.length - 1] : null;
  $: latestX = latest ? xFor(history.length - 1) : 0;
  $: latestY = latest ? yFor(latest.z) : 0;

  // ── Timeline ───────────────────────────────────────────────
  function fmtTick(iso: string, spanMonths: number): string {
    const d = new Date(iso);
    if (spanMonths >= 12) return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  $: spanMonths = (() => {
    if (!hasData) return 0;
    const a = new Date(history[0].ts).getTime();
    const b = new Date(history[history.length - 1].ts).getTime();
    return (b - a) / (1000 * 60 * 60 * 24 * 30.44);
  })();
  $: timelineTicks = (() => {
    if (!hasData) return [];
    const n = history.length;
    const out: { idx: number; label: string; pct: number }[] = [];
    for (let k = 0; k < TICK_COUNT; k++) {
      const idx = Math.round((k * (n - 1)) / (TICK_COUNT - 1));
      out.push({ idx, label: fmtTick(history[idx].ts, spanMonths), pct: xPctFor(idx) });
    }
    return out;
  })();

  // ── Hover ──────────────────────────────────────────────────
  let container: HTMLDivElement | null = null;
  let hoverIdx: number | null = null;

  function onMouseMove(e: MouseEvent) {
    if (!container || !hasData) return;
    const rect = container.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * W;
    const step = (W - padX - padRight) / Math.max(1, history.length - 1);
    hoverIdx = Math.max(0, Math.min(history.length - 1, Math.round((svgX - padX) / step)));
  }
  function onMouseLeave() { hoverIdx = null; }

  $: hover = hoverIdx != null && hasData ? history[hoverIdx] : null;
  $: hoverX = hoverIdx != null ? xFor(hoverIdx) : 0;
  $: hoverXPct = hoverIdx != null ? xPctFor(hoverIdx) : 0;
  $: hoverYPct = hover ? (yFor(hover.z) / H) * 100 : 0;
  $: hoverDateFmt = hover
    ? new Date(hover.ts).toLocaleDateString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
      })
    : '';
  $: tooltipAlign = hoverXPct > 82 ? 'right' : hoverXPct < 12 ? 'left' : 'center';
</script>

<div class="tier-chart">
  <div class="tier-chart-header">
    <span class="tier-chart-title">
      <em style="color: var(--text-2); font-style: italic; font-family: var(--serif); font-size: 14px; margin-right: 6px;">
        {['', 'I', 'II', 'III', 'IV'][tierNumber]}.
      </em>
      {tierName} · tier-average history · {history.length} business days
    </span>
    {#if latest != null}
      <span class="tier-latest" style="color: {color}">
        {latest.z >= 0 ? '+' : ''}{latest.z.toFixed(2)}σ
      </span>
    {/if}
  </div>

  <div
    class="tier-container"
    bind:this={container}
    on:mousemove={onMouseMove}
    on:mouseleave={onMouseLeave}
    role="presentation"
  >
    <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="tierGrad{tierNumber}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color={color} stop-opacity="0.25" />
          <stop offset="100%" stop-color={color} stop-opacity="0" />
        </linearGradient>
      </defs>

      <line x1="0" y1={yFor(0)} x2={W} y2={yFor(0)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="3,4" />
      <line x1="0" y1={yFor(1)} x2={W} y2={yFor(1)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.6" />
      <line x1="0" y1={yFor(-1)} x2={W} y2={yFor(-1)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.6" />
      <text x="6" y={yFor(0) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">0.0σ</text>
      <text x="6" y={yFor(1) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">+1.0σ</text>
      <text x="6" y={yFor(-1) + 12} font-family="JetBrains Mono" font-size="9" fill="#5C544A">−1.0σ</text>

      {#if hasData}
        <path d={fillPath} fill="url(#tierGrad{tierNumber})" stroke="none" />
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
        <text x={W / 2} y={H / 2} font-family="JetBrains Mono" font-size="11" fill="#5C544A" text-anchor="middle">
          Run `make backfill-composite` to populate the history
        </text>
      {/if}
    </svg>

    {#if hasData && hoverIdx != null && hover}
      <div class="hover-dot" style="left: {hoverXPct}%; top: {hoverYPct}%; background: {color};"></div>
      <div class="chart-tooltip align-{tooltipAlign}" style="left: {hoverXPct}%;">
        <div class="tt-date">{hoverDateFmt}</div>
        <div class="tt-row">
          <span class="tt-swatch" style="background: {color}"></span>
          <span class="tt-label">Tier avg</span>
          <span class="tt-val" style="color: {color}">
            {hover.z >= 0 ? '+' : ''}{hover.z.toFixed(2)}σ
          </span>
        </div>
      </div>
    {/if}
  </div>

  {#if hasData}
    <div class="chart-timeline">
      {#each timelineTicks as tick (tick.idx)}
        <span class="tl-label" style="left: {tick.pct}%">{tick.label}</span>
      {/each}
    </div>
  {/if}
</div>

<style>
  .tier-chart {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 20px 24px;
    margin-bottom: 24px;
  }
  .tier-chart-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 12px;
  }
  .tier-chart-title {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-3);
  }
  .tier-latest {
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 20px;
    font-weight: 500;
  }
  .tier-container {
    position: relative;
    width: 100%;
    height: 200px;
  }
  .tier-container svg { width: 100%; height: 100%; display: block; }
  .chart-timeline {
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
    min-width: 180px;
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
  .tt-swatch { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
  .tt-label { color: var(--text-2); font-size: 10px; }
  .tt-val {
    text-align: right;
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 14px;
    font-weight: 500;
  }
</style>
