// Конфиг настройки Playwright для имитации работы в браузере
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests', // Папка с E2E сценарием
  fullyParallel: true, // Прогонять тесты параллельно для ускорения
  forbidOnly: false,
  retries: 0,
  workers: undefined,
  reporter: 'html', // Генерация удобного HTML-отчета после прогона
  use: {
    baseURL: 'http://localhost:3000', // Базовый адрес React-приложения
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium', // Тестируем сценарии прямо внутри Chrome Web Engine
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
