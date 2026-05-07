import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  // Read .env from the project root so backend + frontend share one env file.
  envDir: '..',
  server: {
    host: '0.0.0.0',
    port: 5173
  }
});
