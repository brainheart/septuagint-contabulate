const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  workers: 2,
  use: {
    baseURL: 'http://localhost:8782',
    headless: true,
  },
  webServer: {
    command: 'python3 -m http.server 8782 -d docs',
    port: 8782,
    stdout: 'ignore',
    stderr: 'ignore',
    reuseExistingServer: false,
  },
});
