<script lang="ts">
  import type { CompositeHistoryPoint } from '$lib/types';

  export let history: CompositeHistoryPoint[] = [];

  const W = 800;
  const H = 220;
  const padX = 28;
  const padTop = 16;
  const padBottom = 16;

  // Z-scale runs ±2σ. The mockup labeled gridlines at 0σ, ±1σ.
  const zMin = -2;
  const zMax = 2;

  $: hasData = history.length >= 2;

  function yFor(z: number): number {
    const clamped = Math.max(zMin, Math.min(zMax, z));
    return padTop + (H - padTop - padBottom) * (1 - (clamped - zMin) / (zMax - zMin));
  }
  function xFor(i: number): number {
    if (history.length <= 1) return padX;
    return padX + ((W - padX - 30) * i) / (history.length - 1);
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
</script>

<div class="composite-chart">
  <div class="composite-chart-header">
    <span class="composite-chart-title">Index history · {history.length} business days</span>
  </div>
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
    {:else}
      <text x={W / 2} y={H / 2} font-family="JetBrains Mono" font-size="11" fill="#5C544A" text-anchor="middle">
        Run `make backfill-composite` to populate the history
      </text>
    {/if}
  </svg>
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
  .composite-svg {
    width: 100%;
    height: 220px;
  }
</style>
