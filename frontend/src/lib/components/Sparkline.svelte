<script lang="ts">
  export let data: number[];
  export let color: string = 'var(--pos)';
  export let width: number = 200;
  export let height: number = 38;
  export let strokeWidth: number = 1.3;
  export let pad: number = 2;

  $: path = pathFromData(data, width, height, pad);
  $: fill = pathFilled(data, width, height, pad);
  $: gradientId = `spark_${Math.random().toString(36).slice(2, 9)}`;

  function pathFromData(d: number[], w: number, h: number, p: number): string {
    if (!d.length) return '';
    const min = Math.min(...d);
    const max = Math.max(...d);
    const range = max - min || 1;
    const dx = (w - p * 2) / Math.max(d.length - 1, 1);
    return d
      .map((v, i) => {
        const x = p + i * dx;
        const y = p + (h - p * 2) * (1 - (v - min) / range);
        return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  }

  function pathFilled(d: number[], w: number, h: number, p: number): string {
    const line = pathFromData(d, w, h, p);
    if (!line) return '';
    return `${line} L ${w - p} ${h - p} L ${p} ${h - p} Z`;
  }
</script>

<svg class="metric-spark" viewBox="0 0 {width} {height}" preserveAspectRatio="none" style="height: {height}px;">
  <defs>
    <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color={color} stop-opacity="0.25" />
      <stop offset="100%" stop-color={color} stop-opacity="0" />
    </linearGradient>
  </defs>
  <path d={fill} fill="url(#{gradientId})" stroke="none" />
  <path d={path} fill="none" stroke={color} stroke-width={strokeWidth} stroke-linejoin="round" />
</svg>
