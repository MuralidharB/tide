<script lang="ts">
  import { page } from '$app/stores';

  type NavItem = {
    href: string | null;       // null = disabled (no route yet)
    label: string;
    badge?: string | null;
  };

  const dashboards: NavItem[] = [
    { href: '/',                  label: 'Pressure Index',   badge: '●' },
    { href: '/macro-liquidity',   label: 'Macro Liquidity',  badge: '5' },
    { href: '/capital-flows',     label: 'Capital Flows',    badge: '2' },
    { href: '/microstructure',    label: 'Microstructure',   badge: '4' },
    { href: '/positioning',       label: 'Positioning',      badge: '4' }
  ];

  const portfolio: NavItem[] = [
    { href: '/watchlist',         label: 'Watchlist',        badge: '8' },
    { href: null,                 label: 'Theses',           badge: 'soon' }
  ];

  const system: NavItem[] = [
    { href: '/sources',           label: 'Sources',          badge: '15' },
    { href: null,                 label: 'Logs',             badge: 'soon' },
    { href: null,                 label: 'Settings',         badge: 'soon' }
  ];

  $: pathname = $page.url.pathname;

  function isActive(href: string | null, pathname: string): boolean {
    if (href === null) return false;
    if (href === '/') return pathname === '/';
    return pathname === href || pathname.startsWith(href + '/');
  }
</script>

<aside class="sidebar">
  <a href="/" class="brand">
    <div class="brand-mark">TIDE</div>
    <div class="brand-tag">Capital Pressure Obs.</div>
  </a>

  <div class="nav-section">
    <div class="nav-label">Dashboards</div>
    {#each dashboards as item (item.label)}
      {#if item.href}
        <a class="nav-item" class:active={isActive(item.href, pathname)} href={item.href}>
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </a>
      {:else}
        <div class="nav-item disabled">
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </div>
      {/if}
    {/each}
  </div>

  <div class="nav-section">
    <div class="nav-label">Portfolio</div>
    {#each portfolio as item (item.label)}
      {#if item.href}
        <a class="nav-item" class:active={isActive(item.href, pathname)} href={item.href}>
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </a>
      {:else}
        <div class="nav-item disabled">
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </div>
      {/if}
    {/each}
  </div>

  <div class="nav-section">
    <div class="nav-label">System</div>
    {#each system as item (item.label)}
      {#if item.href}
        <a class="nav-item" class:active={isActive(item.href, pathname)} href={item.href}>
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </a>
      {:else}
        <div class="nav-item disabled">
          <span>{item.label}</span>
          {#if item.badge}<span class="badge">{item.badge}</span>{/if}
        </div>
      {/if}
    {/each}
  </div>
</aside>

<style>
  .brand { display: block; text-decoration: none; }
  a.nav-item { text-decoration: none; }
  .nav-item.disabled {
    color: var(--text-3);
    cursor: not-allowed;
    opacity: 0.55;
  }
  .nav-item.disabled:hover { background: transparent; color: var(--text-3); }
  .nav-item .badge {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
</style>
