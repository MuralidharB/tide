<script lang="ts">
  import '../app.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
</script>

<div class="app">
  <Sidebar />
  <main class="main">
    <slot />
  </main>
</div>
