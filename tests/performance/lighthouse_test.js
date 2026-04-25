/**
 * Lighthouse性能测试脚本
 * 使用Lighthouse CI进行性能评分测试
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  baseUrl: 'http://localhost:3000',
  pages: [
    { name: 'Login', path: '/login' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Jobs', path: '/jobs' },
    { name: 'Vault', path: '/vault' },
    { name: 'Tailor', path: '/tailor' }
  ],
  lighthouseConfig: {
    extends: 'lighthouse:default',
    settings: {
      onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
      formFactor: 'desktop',
      throttling: {
        rttMs: 40,
        throughputKbps: 10240,
        cpuSlowdownMultiplier: 1
      },
      screenEmulation: {
        mobile: false,
        width: 1350,
        height: 940,
        deviceScaleFactor: 1,
        disabled: false
      },
      emulatedUserAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
  },
  targetScores: {
    performance: 80,
    accessibility: 80,
    bestPractices: 80,
    seo: 80
  }
};

class LighthouseTester {
  constructor() {
    this.results = [];
  }

  async runLighthouse(url, pageName) {
    console.log(`  测试页面: ${pageName} (${url})`);
    
    const chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--no-sandbox', '--disable-gpu']
    });

    try {
      const options = {
        logLevel: 'error',
        output: 'json',
        port: chrome.port
      };

      const runnerResult = await lighthouse(url, options, CONFIG.lighthouseConfig);
      
      // 提取关键指标
      const scores = {
        performance: Math.round(runnerResult.lhr.categories.performance.score * 100),
        accessibility: Math.round(runnerResult.lhr.categories.accessibility.score * 100),
        bestPractices: Math.round(runnerResult.lhr.categories['best-practices'].score * 100),
        seo: Math.round(runnerResult.lhr.categories.seo.score * 100)
      };

      // 提取性能指标
      const audits = runnerResult.lhr.audits;
      const metrics = {
        firstContentfulPaint: audits['first-contentful-paint'].numericValue,
        largestContentfulPaint: audits['largest-contentful-paint'].numericValue,
        totalBlockingTime: audits['total-blocking-time'].numericValue,
        cumulativeLayoutShift: audits['cumulative-layout-shift'].numericValue,
        speedIndex: audits['speed-index'].numericValue,
        timeToInteractive: audits['interactive'].numericValue
      };

      return {
        page: pageName,
        url: url,
        scores,
        metrics
      };
    } finally {
      await chrome.kill();
    }
  }

  async runTests() {
    console.log('='.repeat(60));
    console.log('Lighthouse性能测试开始');
    console.log('='.repeat(60));

    for (const pageConfig of CONFIG.pages) {
      console.log(`\n--- 测试: ${pageConfig.name} ---`);
      const url = `${CONFIG.baseUrl}${pageConfig.path}`;
      
      try {
        const result = await this.runLighthouse(url, pageConfig.name);
        this.results.push(result);
        
        console.log(`  Performance: ${result.scores.performance}`);
        console.log(`  Accessibility: ${result.scores.accessibility}`);
        console.log(`  Best Practices: ${result.scores.bestPractices}`);
        console.log(`  SEO: ${result.scores.seo}`);
      } catch (error) {
        console.error(`  ✗ 测试失败: ${error.message}`);
        this.results.push({
          page: pageConfig.name,
          url: url,
          error: error.message
        });
      }
    }

    this.generateReport();
  }

  generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('Lighthouse性能测试报告');
    console.log('='.repeat(60));

    // 表格头
    console.log(`${'页面'.padEnd(15)} ${'Performance'.padEnd(12)} ${'Accessibility'.padEnd(14)} ${'Best Practices'.padEnd(15)} ${'SEO'.padEnd(8)} ${'状态'.padEnd(10)}`);
    console.log('-'.repeat(80));

    let allPassed = true;
    for (const result of this.results) {
      if (result.error) {
        console.log(`${result.page.padEnd(15)} ${'N/A'.padEnd(12)} ${'N/A'.padEnd(14)} ${'N/A'.padEnd(15)} ${'N/A'.padEnd(8)} ${'✗ 失败'.padEnd(10)}`);
        allPassed = false;
        continue;
      }

      const scores = result.scores;
      const passed = scores.performance >= CONFIG.targetScores.performance &&
                    scores.accessibility >= CONFIG.targetScores.accessibility &&
                    scores.bestPractices >= CONFIG.targetScores.bestPractices &&
                    scores.seo >= CONFIG.targetScores.seo;
      
      const status = passed ? '✓ 通过' : '✗ 失败';
      if (!passed) allPassed = false;

      console.log(
        `${result.page.padEnd(15)} ` +
        `${String(scores.performance).padEnd(12)} ` +
        `${String(scores.accessibility).padEnd(14)} ` +
        `${String(scores.bestPractices).padEnd(15)} ` +
        `${String(scores.seo).padEnd(8)} ` +
        `${status.padEnd(10)}`
      );
    }

    console.log('-'.repeat(80));

    // 目标指标对比
    console.log('\n目标指标对比 (目标分数 >= 80):');
    const validResults = this.results.filter(r => !r.error);
    
    if (validResults.length > 0) {
      const avgPerformance = Math.round(
        validResults.reduce((sum, r) => sum + r.scores.performance, 0) / validResults.length
      );
      const avgAccessibility = Math.round(
        validResults.reduce((sum, r) => sum + r.scores.accessibility, 0) / validResults.length
      );
      const avgBestPractices = Math.round(
        validResults.reduce((sum, r) => sum + r.scores.bestPractices, 0) / validResults.length
      );
      const avgSeo = Math.round(
        validResults.reduce((sum, r) => sum + r.scores.seo, 0) / validResults.length
      );

      console.log(`  - Performance: ${avgPerformance >= 80 ? '✓' : '✗'} ${avgPerformance}/100`);
      console.log(`  - Accessibility: ${avgAccessibility >= 80 ? '✓' : '✗'} ${avgAccessibility}/100`);
      console.log(`  - Best Practices: ${avgBestPractices >= 80 ? '✓' : '✗'} ${avgBestPractices}/100`);
      console.log(`  - SEO: ${avgSeo >= 80 ? '✓' : '✗'} ${avgSeo}/100`);
    }

    // 保存详细报告
    const report = {
      testTime: new Date().toISOString(),
      baseUrl: CONFIG.baseUrl,
      targetScores: CONFIG.targetScores,
      results: this.results,
      summary: {
        allPassed,
        totalPages: CONFIG.pages.length,
        passedPages: validResults.filter(r => 
          r.scores.performance >= CONFIG.targetScores.performance &&
          r.scores.accessibility >= CONFIG.targetScores.accessibility &&
          r.scores.bestPractices >= CONFIG.targetScores.bestPractices &&
          r.scores.seo >= CONFIG.targetScores.seo
        ).length
      }
    };

    const reportPath = path.join(__dirname, 'lighthouse_report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n详细报告已保存: ${reportPath}`);

    return allPassed;
  }
}

// 运行测试
async function main() {
  const tester = new LighthouseTester();
  await tester.runTests();
}

main().catch(console.error);
