<script lang="ts">
  import type { CompositeHistoryPoint } from '$lib/types';

  export let history: CompositeHistoryPoint[] = [];

  const W = 800;
  const H = 220;
  const padX = 28;
  const padRight = 30;
  const padTop = 16;
  const padBottom = 16;

  const zMin = -2;
  const zMax = 2;

  const TICK_COUNT = 6;
  const SPY_COLOR = '#5DD3C0';   // muted teal, from --tier3 palette

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
    return (xFor(i) / W) * 100;
  }

  // ── SPY overlay: percent change from first visible close ────────────────
  $: spyBase = (() => {
    if (!hasData) return null;
    const first = history.find((p) => p.spy_close != null);
    return first ? first.spy_close : null;
  })();

  $: spyPcts = (() => {
    if (!hasData || spyBase == null) return [];
    return history.map((p) =>
      p.spy_close != null ? (p.spy_close / spyBase - 1) * 100 : null
    );
  })();

  // Dynamic right-axis range: symmetric around 0, rounded up to nearest 5%.
  $: spyPctBound = (() => {
    if (spyPcts.length === 0) return 0;
    const nonNull = spyPcts.filter((v): v is number => v != null);
    if (nonNull.length === 0) return 0;
    const m = Math.max(Math.abs(Math.min(...nonNull)), Math.abs(Math.max(...nonNull)));
    if (m === 0) return 5;
    const rounded = Math.ceil(m / 5) * 5;
    return Math.min(rounded, 80); // cap for sanity
  })();

  function yForSpyPct(pct: number): number {
    if (spyPctBound === 0) return H / 2;
    const clamped = Math.max(-spyPctBound, Math.min(spyPctBound, pct));
    return padTop + (H - padTop - padBottom) * (1 - (clamped + spyPctBound) / (2 * spyPctBound));
  }

  // ── Composite paths ─────────────────────────────────────────────────────
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

  // ── SPY path — thin line, no fill, skip missing ─────────────────────────
  $: spyPath = (() => {
    if (!hasData || spyBase == null || spyPctBound === 0) return '';
    const cmds: string[] = [];
    let started = false;
    for (let i = 0; i < history.length; i++) {
      const pct = spyPcts[i];
      if (pct == null) {
        started = false;
        continue;
      }
      const x = xFor(i).toFixed(1);
      const y = yForSpyPct(pct).toFixed(1);
      cmds.push(`${started ? 'L' : 'M'} ${x} ${y}`);
      started = true;
    }
    return cmds.join(' ');
  })();

  $: latest = hasData ? history[history.length - 1] : null;
  $: latestX = latest ? xFor(history.length - 1) : 0;
  $: latestY = latest ? yFor(latest.z) : 0;
  $: latestColor =
    latest == null ? 'var(--text-2)' : latest.z >= 0 ? 'var(--pos)' : 'var(--neg)';

  $: latestSpyPct = spyPcts.length > 0 ? spyPcts[spyPcts.length - 1] : null;

  // ── Timeline ────────────────────────────────────────────────────────────
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
      out.push({ idx, label: fmtTick(history[idx].ts, spanMonths), pct: xPctFor(idx) });
    }
    return out;
  })();

  // ── Hover ───────────────────────────────────────────────────────────────
  let container: HTMLDivElement | null = null;
  let hoverIdx: number | null = null;

  function onMouseMove(e: MouseEvent) {
    if (!container || !hasData) return;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const svgX = (x / rect.width) * W;
    const step = (W - padX - padRight) / Math.max(1, history.length - 1);
    const raw = (svgX - padX) / step;
    hoverIdx = Math.max(0, Math.min(history.length - 1, Math.round(raw)));
  }
  function onMouseLeave() {
    hoverIdx = null;
  }

  $: hover = hoverIdx != null && hasData ? history[hoverIdx] : null;
  $: hoverPct = hoverIdx != null ? xPctFor(hoverIdx) : 0;
  $: hoverYPct = hover ? (yFor(hover.z) / H) * 100 : 0;
  $: hoverSpyPct = hoverIdx != null ? spyPcts[hoverIdx] : null;
  $: hoverSpyYPct =
    hoverIdx != null && hoverSpyPct != null ? (yForSpyPct(hoverSpyPct) / H) * 100 : null;
  $: hoverX = hoverIdx != null ? xFor(hoverIdx) : 0;
  $: hoverSignClass = hover == null ? 'neu' : hover.z >= 0 ? 'pos' : 'neg';
  $: hoverDateFmt = hover
    ? new Date(hover.ts).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';
  $: tooltipAlign = hoverPct > 82 ? 'right' : hoverPct < 12 ? 'left' : 'center';
</script>

<div class="composite-chart">
  <div class="composite-chart-header">
    <span class="composite-chart-title">Index history · {history.length} business days</span>
    <span class="chart-legend">
      <span class="legend-item">
        <span class="legend-dot" style="background: {latestColor}"></span>
        <span class="legend-label">Composite</span>
      </span>
      {#if spyBase != null}
        <span class="legend-item">
          <span class="legend-dot" style="background: {SPY_COLOR}"></span>
          <span class="legend-label">
            S&amp;P 500
            {#if latestSpyPct != null}
              <span class="legend-sub">
                {latestSpyPct >= 0 ? '+' : ''}{latestSpyPct.toFixed(1)}%
              </span>
            {/if}
          </span>
        </span>
      {/if}
    </span>
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

      <!-- Left y-axis (σ) labels -->
      <text x="6" y={yFor(0) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">0.0σ</text>
      <text x="6" y={yFor(1) - 4} font-family="JetBrains Mono" font-size="9" fill="#5C544A">+1.0σ</text>
      <text x="6" y={yFor(-1) + 12} font-family="JetBrains Mono" font-size="9" fill="#5C544A">−1.0σ</text>

      <!-- Right y-axis (SPY %) labels -->
      {#if spyBase != null && spyPctBound > 0}
        <text x={W - 6} y={yForSpyPct(spyPctBound) - 4} font-family="JetBrains Mono" font-size="9" fill={SPY_COLOR} opacity="0.7" text-anchor="end">
          +{spyPctBound}%
        </text>
        <text x={W - 6} y={yForSpyPct(0) - 4} font-family="JetBrains Mono" font-size="9" fill={SPY_COLOR} opacity="0.7" text-anchor="end">
          0%
        </text>
        <text x={W - 6} y={yForSpyPct(-spyPctBound) + 12} font-family="JetBrains Mono" font-size="9" fill={SPY_COLOR} opacity="0.7" text-anchor="end">
          −{spyPctBound}%
        </text>
      {/if}

      {#if hasData}
        <!-- Composite fill + line -->
        <path d={fillPath} fill="url(#gradComposite)" stroke="none" />
        <path d={linePath} fill="none" stroke={latestColor} stroke-width="1.6" stroke-linejoin="round" />
        <circle cx={latestX} cy={latestY} r="3.5" fill={latestColor} />
        <circle cx={latestX} cy={latestY} r="8" fill={latestColor} opacity="0.3" />

        <!-- SPY overlay line -->
        {#if spyPath}
          <path d={spyPath} fill="none" stroke={SPY_COLOR} stroke-width="1.2" stroke-linejoin="round" opacity="0.75" />
        {/if}

        <!-- Hover guide -->
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
      <div class="hover-dot {hoverSignClass}" style="left: {hoverPct}%; top: {hoverYPct}%;"></div>
      {#if hoverSpyYPct != null}
        <div class="hover-dot spy" style="left: {hoverPct}%; top: {hoverSpyYPct}%;"></div>
      {/if}
      <div class="chart-tooltip align-{tooltipAlign}" style="left: {hoverPct}%;">
        <div class="tt-date">{hoverDateFmt}</div>
        <div class="tt-row">
          <span class="tt-swatch" style="background: {latestColor}"></span>
          <span class="tt-label">Composite</span>
          <span class="tt-val {hoverSignClass}">
            {hover.z >= 0 ? '+' : ''}{hover.z.toFixed(2)}σ
          </span>
        </div>
        {#if hover.spy_close != null && hoverSpyPct != null}
          <div class="tt-row">
            <span class="tt-swatch" style="background: {SPY_COLOR}"></span>
            <span class="tt-label">S&amp;P 500</span>
            <span class="tt-val spy">
              ${hover.spy_close.toFixed(2)}
              <span class="tt-sub">
                {hoverSpyPct >= 0 ? '+' : ''}{hoverSpyPct.toFixed(1)}%
              </span>
            </span>
          </div>
        {/if}
        {#if hover.tier_zs && Object.keys(hover.tier_zs).length > 0}
          <div class="tt-divider"></div>
          {#each [1, 2, 3, 4] as tier}
            {@const tv = hover.tier_zs[String(tier)]}
            {#if tv != null}
              {@const tColor = tier === 1 ? '#4A8FE7' : tier === 2 ? '#B97AE0' : tier === 3 ? '#5DD3C0' : '#F4C95D'}
              <div class="tt-row tt-tier">
                <span class="tt-swatch" style="background: {tColor}; opacity: 0.7"></span>
                <span class="tt-label tt-tier-label">Tier {['','I','II','III','IV'][tier]}</span>
                <span class="tt-val tt-tier-val" style="color: {tColor}; opacity: 0.9">
                  {tv >= 0 ? '+' : ''}{tv.toFixed(2)}σ
                </span>
              </div>
            {/if}
          {/each}
        {/if}
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
    gap: 20px;
  }
  .composite-chart-title {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-3);
  }
  .chart-legend {
    display: inline-flex;
    gap: 18px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.05em;
    color: var(--text-2);
  }
  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .legend-label { color: var(--text-2); }
  .legend-sub {
    color: var(--text-3);
    margin-left: 6px;
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
  .hover-dot.spy { background: #5DD3C0; opacity: 0.9; }
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
  .tt-divider {
    height: 1px;
    background: var(--border-soft);
    margin: 6px 0 2px;
  }
  .tt-row.tt-tier {
    padding: 1px 0;
  }
  .tt-tier-label { font-size: 9px; }
  .tt-tier-val {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 500;
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
  }
  .tt-val.pos { color: var(--pos); }
  .tt-val.neg { color: var(--neg); }
  .tt-val.neu { color: var(--text-2); }
  .tt-val.spy { color: #5DD3C0; }
  .tt-sub {
    display: block;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-3);
    margin-top: 2px;
  }
</style>
