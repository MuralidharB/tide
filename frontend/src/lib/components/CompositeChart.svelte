<script lang="ts">
  import type { CompositeHistoryPoint } from '$lib/types';

  export let history: CompositeHistoryPoint[] = [];

  const W = 800;
  const H = 220;
  const padX = 28;
  const padRight = 30;      // reserve room for the terminal-value label
  const padTop = 16;
  const padBottom = 16;

  const zMin = -2;
  const zMax = 2;

  const TICK_COUNT = 6;     // date labels along the x-axis

  $: hasData = history.length >= 2;

  function yFor(z: number): number {
    const clamped = Math.max(zMin, Math.min(zMax, z));
    return padTop + (H - padTop - padBottom) * (1 - (clamped - zMin) / (zMax - zMin));
  }
  function xFor(i: number): number {
    if (history.length <= 1) return padX;
    return padX + ((W - padX - padRight) * i) / (history.length - 1);
  }

  function xPctFor(i: number): number {
    // Container-local percent (0..100). Since the SVG uses preserveAspectRatio="none"
    // and stretches to container width, viewBox-x/W is the same fraction as pixel-x/width.
    return (xFor(i) / W) * 100;
  }

  $: linePath = (() => {
    if (!hasData) return '';
    return history
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i).toFixed(1)} ${yFor(p.z).toFixed(1)}`)
      .join(' ');
  })();

  $: fillPath = (() => {
    if (!hasData) return '';
    const baseY = yFor(0);
    const lastX = xFor(history.length - 1);
    return linePath + ` L ${lastX.toFixed(1)} ${baseY.toFixed(1)} L ${padX} ${baseY.toFixed(1)} Z`;
  })();

  $: latest = hasData ? history[history.length - 1] : null;
  $: latestX = latest ? xFor(history.length - 1) : 0;
  $: latestY = latest ? yFor(latest.z) : 0;
  $: latestColor =
    latest == null ? 'var(--text-2)' : latest.z >= 0 ? 'var(--pos)' : 'var(--neg)';

  // ── x-axis timeline labels ──────────────────────────────────────────────
  function fmtTick(iso: string, spanMonths: number): string {
    const d = new Date(iso);
    if (spanMonths >= 12) {
      return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    }
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
      out.push({
        idx,
        label: fmtTick(history[idx].ts, spanMonths),
        pct: xPctFor(idx),
      });
    }
    return out;
  })();

  // ── hover popover ───────────────────────────────────────────────────────
  let container: HTMLDivElement | null = null;
  let hoverIdx: number | null = null;

  function onMouseMove(e: MouseEvent) {
    if (!container || !hasData) return;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const w = rect.width;
    // Convert container-local pixel x → viewBox-x (0..W)
    const svgX = (x / w) * W;
    // Invert xFor: idx = (svgX - padX) / step
    const step = (W - padX - padRight) / Math.max(1, history.length - 1);
    const raw = (svgX - padX) / step;
    const idx = Math.max(0, Math.min(history.length - 1, Math.round(raw)));
    hoverIdx = idx;
  }

  function onMouseLeave() {
    hoverIdx = null;
  }

  $: hover = hoverIdx != null && hasData ? history[hoverIdx] : null;
  $: hoverX = hoverIdx != null ? xFor(hoverIdx) : 0;
  $: hoverY = hover ? yFor(hover.z) : 0;
  $: hoverPct = hoverIdx != null ? xPctFor(hoverIdx) : 0;
  $: hoverYPct = hover ? (yFor(hover.z) / H) * 100 : 0;
  $: hoverColor = hover == null ? 'var(--text-2)' : hover.z >= 0 ? 'var(--pos)' : 'var(--neg)';
  $: hoverSignClass = hover == null ? 'neu' : hover.z >= 0 ? 'pos' : 'neg';
  $: hoverDateFmt = hover
    ? new Date(hover.ts).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';
  // Keep the tooltip inside the container by shifting it left near the right edge.
  $: tooltipAlign = hoverPct > 82 ? 'right' : hoverPct < 12 ? 'left' : 'center';
</script>

<div class="composite-chart">
  <div class="composite-chart-header">
    <span class="composite-chart-title">Index history · {history.length} business days</span>
  </div>
  <div
    class="chart-container"
    bind:this={container}
    on:mousemove={onMouseMove}
    on:mouseleave={onMouseLeave}
    role="presentation"
  >
    <svg class="composite-svg" viewBox="0 0 {W} {H}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="gradComposite" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color={latestColor} stop-opacity="0.3" />
          <stop offset="100%" stop-color={latestColor} stop-opacity="0" />
        </linearGradient>
        <pattern id="gridComposite" width="80" height="44" patternUnits="userSpaceOnUse">
          <path d="M 80 0 L 0 0 0 44" fill="none" stroke="#221F1A" stroke-width="0.5" />
        </pattern>
      </defs>
      <rect width={W} height={H} fill="url(#gridComposite)" />
      <line x1="0" y1={yFor(0)} x2={W} y2={yFor(0)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="3,4" />
      <line x1="0" y1={yFor(1)} x2={W} y2={yFor(1)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.6" />
      <line x1="0" y1={yFor(-1)} x2={W} y2={yFor(-1)} stroke="#2C2823" stroke-width="0.5" stroke-dasharray="2,5" opacity="0.6" />
      <text x="6" y={yFor(0) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">0.0σ</text>
      <text x="6" y={yFor(1) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">+1.0σ</text>
      <text x="6" y={yFor(-1) + 12} font-family="JetBrains Mono" font-size="9" fill="#5C544A">−1.0σ</text>
      {#if hasData}
        <path d={fillPath} fill="url(#gradComposite)" stroke="none" />
        <path d={linePath} fill="none" stroke={latestColor} stroke-width="1.6" stroke-linejoin="round" />
        <circle cx={latestX} cy={latestY} r="3.5" fill={latestColor} />
        <circle cx={latestX} cy={latestY} r="8" fill={latestColor} opacity="0.3" />
        <text x={W - 6} y="36" font-family="JetBrains Mono" font-size="10" fill={latestColor} text-anchor="end">
          {latest && latest.z >= 0 ? '+' : ''}{latest?.z.toFixed(2)}σ
        </text>

        {#if hoverIdx != null && hover}
          <line
            x1={hoverX}
            x2={hoverX}
            y1={padTop}
            y2={H - padBottom}
            stroke="var(--text-2)"
            stroke-width="0.7"
            stroke-dasharray="2,3"
            opacity="0.5"
          />
        {/if}
      {:else}
        <text x={W / 2} y={H / 2} font-family="JetBrains Mono" font-size="11" fill="#5C544A" text-anchor="middle">
          Run `make backfill-composite` to populate the history
        </text>
      {/if}
    </svg>

    {#if hasData && hoverIdx != null && hover}
      <div
        class="hover-dot {hoverSignClass}"
        style="left: {hoverPct}%; top: {hoverYPct}%;"
      ></div>
      <div
        class="chart-tooltip align-{tooltipAlign}"
        style="left: {hoverPct}%;"
      >
        <div class="tt-date">{hoverDateFmt}</div>
        <div class="tt-z {hoverSignClass}">
          {hover.z >= 0 ? '+' : ''}{hover.z.toFixed(2)}σ
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
  .composite-chart-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 16px;
  }
  .composite-chart-title {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-3);
  }
  .chart-container {
    position: relative;
    width: 100%;
    height: 220px;
  }
  .composite-svg {
    width: 100%;
    height: 100%;
    display: block;
  }
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
  .hover-dot.pos { background: var(--pos); }
  .hover-dot.neg { background: var(--neg); }
  .hover-dot.neu { background: var(--text-2); }
  .chart-tooltip {
    position: absolute;
    top: -6px;
    transform: translateX(-50%);
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 6px 10px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.04em;
    line-height: 1.4;
    color: var(--text);
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    z-index: 2;
  }
  .chart-tooltip.align-left  { transform: translateX(0); }
  .chart-tooltip.align-right { transform: translateX(-100%); }
  .tt-date {
    color: var(--text-3);
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .tt-z {
    font-family: var(--serif);
    font-variation-settings: 'opsz' 144;
    font-size: 16px;
    font-weight: 500;
    margin-top: 2px;
  }
  .tt-z.pos { color: var(--pos); }
  .tt-z.neg { color: var(--neg); }
  .tt-z.neu { color: var(--text-2); }
</style>
