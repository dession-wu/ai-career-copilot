/**
 * 前端性能测试脚本
 * 使用Playwright测试首屏加载时间和内存占用
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  baseUrl: 'http://localhost:3000',
  testUser: {
    username: 'testuser',
    password: 'testpass123'
  },
  pages: [
    { name: 'Login', path: '/login' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Jobs', path: '/jobs' },
    { name: 'Vault', path: '/vault' }
  ],
  iterations: 3 // 每个页面测试次数
};

class FrontendPerformanceTester {
  constructor() {
    this.results = [];
  }

  async login(page) {
    console.log('  正在登录...');
    await page.goto(`${CONFIG.baseUrl}/login`);
    await page.fill('input[name="username"]', CONFIG.testUser.username);
    await page.fill('input[name="password"]', CONFIG.testUser.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('  ✓ 登录成功');
  }

  async measurePageLoad(page, pageConfig) {
    const url = `${CONFIG.baseUrl}${pageConfig.path}`;
    console.log(`  测试页面: ${pageConfig.name} (${url})`);

    // 清除缓存
    await page.context().clearCookies();
    
    // 记录性能数据
    const performanceMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          resolve(entries);
        });
        observer.observe({ entryTypes: ['navigation', 'paint', 'measure'] });
        
        // 如果已经有数据，直接返回
        if (performance.getEntriesByType('navigation').length > 0) {
          resolve(performance.getEntriesByType('navigation'));
        }
      });
    });

    // 导航到页面并测量
    const startTime = Date.now();
    await page.goto(url, { waitUntil: 'networkidle' });
    const loadTime = Date.now() - startTime;

    // 获取详细的性能指标
    const timing = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0];
      const paint = performance.getEntriesByType('paint');
      
      return {
        // 导航时间
        dnsLookup: nav ? nav.domainLookupEnd - nav.domainLookupStart : 0,
        tcpConnection: nav ? nav.connectEnd - nav.connectStart : 0,
        serverResponse: nav ? nav.responseEnd - nav.requestStart : 0,
        domProcessing: nav ? nav.domComplete - nav.responseEnd : 0,
        // 关键时间点
        domContentLoaded: nav ? nav.domContentLoadedEventEnd - nav.startTime : 0,
        loadComplete: nav ? nav.loadEventEnd - nav.startTime : 0,
        // 首屏渲染
        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0
      };
    });

    // 获取内存使用情况
    const memory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });

    // 获取资源加载信息
    const resources = await page.evaluate(() => {
      return performance.getEntriesByType('resource').map(r => ({
        name: r.name,
        duration: r.duration,
        size: r.transferSize
      }));
    });

    const totalResourceSize = resources.reduce((sum, r) => sum + (r.size || 0), 0);

    return {
      page: pageConfig.name,
      url: url,
      loadTime,
      timing,
      memory: memory ? {
        usedMB: (memory.usedJSHeapSize / 1024 / 1024).toFixed(2),
        totalMB: (memory.totalJSHeapSize / 1024 / 1024).toFixed(2),
        limitMB: (memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)
      } : null,
      resources: {
        count: resources.length,
        totalSizeKB: (totalResourceSize / 1024).toFixed(2)
      }
    };
  }

  async runTests() {
    console.log('='.repeat(60));
    console.log('前端性能测试开始');
    console.log('='.repeat(60));

    const browser = await chromium.launch({ headless: true });
    
    try {
      for (const pageConfig of CONFIG.pages) {
        console.log(`\n--- 测试页面: ${pageConfig.name} ---`);
        
        const pageResults = [];
        
        for (let i = 0; i < CONFIG.iterations; i++) {
          const context = await browser.newContext();
          const page = await context.newPage();
          
          // 如果需要登录，先登录
          if (pageConfig.name !== 'Login') {
            await this.login(page);
          }
          
          const result = await this.measurePageLoad(page, pageConfig);
          pageResults.push(result);
          
          console.log(`  迭代 ${i + 1}: 加载时间 ${result.loadTime}ms, 内存 ${result.memory?.usedMB || 'N/A'}MB`);
          
          await context.close();
        }

        // 计算平均值
        const avgLoadTime = Math.round(
          pageResults.reduce((sum, r) => sum + r.loadTime, 0) / pageResults.length
        );
        const avgMemory = pageResults[0].memory ? 
          (pageResults.reduce((sum, r) => sum + parseFloat(r.memory.usedMB), 0) / pageResults.length).toFixed(2) :
          'N/A';

        this.results.push({
          page: pageConfig.name,
          iterations: pageResults,
          average: {
            loadTime: avgLoadTime,
            memoryUsedMB: avgMemory,
            firstContentfulPaint: Math.round(
              pageResults.reduce((sum, r) => sum + r.timing.firstContentfulPaint, 0) / pageResults.length
            )
          }
        });
      }

      this.generateReport();
    } finally {
      await browser.close();
    }
  }

  generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('前端性能测试报告');
    console.log('='.repeat(60));

    // 表格头
    console.log(`${'页面'.padEnd(15)} ${'平均加载(ms)'.padEnd(15)} ${'FCP(ms)'.padEnd(12)} ${'内存(MB)'.padEnd(12)} ${'状态'.padEnd(10)}`);
    console.log('-'.repeat(70));

    let allPassed = true;
    for (const result of this.results) {
      const avg = result.average;
      const passed = avg.loadTime < 3000; // 目标: < 3s
      const status = passed ? '✓ 通过' : '✗ 失败';
      if (!passed) allPassed = false;

      console.log(
        `${result.page.padEnd(15)} ` +
        `${String(avg.loadTime).padEnd(15)} ` +
        `${String(avg.firstContentfulPaint).padEnd(12)} ` +
        `${String(avg.memoryUsedMB).padEnd(12)} ` +
        `${status.padEnd(10)}`
      );
    }

    console.log('-'.repeat(70));

    // 目标指标对比
    console.log('\n目标指标对比:');
    const maxLoadTime = Math.max(...this.results.map(r => r.average.loadTime));
    const maxMemory = Math.max(...this.results
      .filter(r => r.average.memoryUsedMB !== 'N/A')
      .map(r => parseFloat(r.average.memoryUsedMB)));
    
    console.log(`  - 首屏加载时间 < 3s: ${maxLoadTime < 3000 ? '✓ 达标' : '✗ 未达标'} (实际: ${maxLoadTime}ms)`);
    console.log(`  - 内存占用 < 100MB: ${maxMemory < 100 ? '✓ 达标' : '✗ 未达标'} (实际: ${maxMemory.toFixed(2)}MB)`);

    // 保存详细报告
    const report = {
      testTime: new Date().toISOString(),
      baseUrl: CONFIG.baseUrl,
      results: this.results,
      summary: {
        allPassed,
        targetLoadTime: 3000,
        targetMemoryMB: 100,
        maxLoadTime,
        maxMemoryMB: maxMemory
      }
    };

    const reportPath = path.join(__dirname, 'frontend_performance_report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n详细报告已保存: ${reportPath}`);

    return allPassed;
  }
}

// 运行测试
async function main() {
  const tester = new FrontendPerformanceTester();
  await tester.runTests();
}

main().catch(console.error);
