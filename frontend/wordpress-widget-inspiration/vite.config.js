import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // Handle binary responses (audio files)
            if (req.url.includes('/text-to-speech')) {
              proxyRes.headers['access-control-allow-origin'] = '*';
            }
          });
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  }
});

