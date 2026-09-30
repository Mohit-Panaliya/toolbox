import path from 'path'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import { defineConfig } from 'vite'

import { toolboxPwaBuild } from './build/pwaBuildPlugin.js'

export default defineConfig({
  plugins: [
    frappeui({
      // Toolbox is published under a prefix rather than at the site root, so the router base is
      // that prefix. This is the one value the client, the built page and the assets all agree on.
      frontendRoute: '/toolbox',
      // The plugin names the output HTML after frontendRoute, which is why the file lands at
      // `toolbox/www/toolbox.html` and Frappe serves the page from that module. It only forwards
      // nested `buildConfig` options, so the path is set here rather than alongside frontendRoute.
      buildConfig: {
        indexHtmlPath: '../toolbox/www/toolbox.html',
      },
    }),
    vue(),
    toolboxPwaBuild(),
  ],
  server: {
    host: '127.0.0.1',
    allowedHosts: ['localhost', 'toolbox.localhost', 'pd.localhost'],
  },
  build: {
    manifest: 'manifest.json',
  },
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, 'src'),
    },
  },
})
