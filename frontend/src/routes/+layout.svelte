<script lang="ts">
  import '../app.css';
</script>

<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">TIDE</div>
      <div class="brand-tag">Capital Pressure Obs.</div>
    </div>

    <div class="nav-section">
      <div class="nav-label">Dashboards</div>
      <div class="nav-item active"><span>Pressure Index</span><span class="badge">●</span></div>
      <div class="nav-item"><span>Macro Liquidity</span><span class="badge">5</span></div>
      <div class="nav-item"><span>Capital Flows</span><span class="badge">4</span></div>
      <div class="nav-item"><span>Microstructure</span><span class="badge">5</span></div>
      <div class="nav-item"><span>Positioning</span><span class="badge">5</span></div>
    </div>

    <div class="nav-section">
      <div class="nav-label">Portfolio</div>
      <div class="nav-item"><span>Watchlist</span></div>
      <div class="nav-item"><span>Theses</span></div>
    </div>

    <div class="nav-section">
      <div class="nav-label">System</div>
      <div class="nav-item"><span>Sources</span></div>
      <div class="nav-item"><span>Logs</span></div>
      <div class="nav-item"><span>Settings</span></div>
    </div>
  </aside>

  <main class="main">
    <slot />
  </main>
</div>
