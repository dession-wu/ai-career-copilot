const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function recordDemo() {
  const outputDir = path.join(__dirname, 'demo-output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const videoPath = path.join(outputDir, 'career-copilot-demo.mp4');

  console.log('🎬 启动浏览器并录制视频...');
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--window-size=1920,1080']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: outputDir,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  try {
    // 1. 访问首页
    console.log('📱 访问应用首页...');
    await page.goto('http://localhost:3000');
    await delay(3000);

    // 2. 注册页面
    console.log('📝 演示注册功能...');
    await page.click('text=注册');
    await delay(1000);
    
    await page.fill('input[name="username"]', 'demo_user');
    await delay(500);
    await page.fill('input[name="email"]', 'demo@example.com');
    await delay(500);
    await page.fill('input[name="password"]', 'demo123456');
    await delay(500);
    await page.fill('input[name="confirmPassword"]', 'demo123456');
    await delay(500);
    
    await page.click('button[type="submit"]');
    await delay(3000);

    // 3. 仪表盘
    console.log('📊 展示仪表盘...');
    await delay(2000);

    // 4. 经历总库
    console.log('📚 演示经历总库...');
    await page.click('text=经历总库');
    await delay(2000);

    // 5. 求职管理
    console.log('💼 演示求职管理...');
    await page.click('text=求职管理');
    await delay(2000);

    // 6. 简历定制
    console.log('✨ 演示简历定制...');
    await page.click('text=简历定制');
    await delay(3000);

    // 7. 面试准备
    console.log('🎯 演示面试准备...');
    await page.click('text=面试准备');
    await delay(2000);

    // 8. 面试复盘
    console.log('📝 演示面试复盘...');
    await page.click('text=面试复盘');
    await delay(2000);

    // 9. 设置页面
    console.log('⚙️ 演示设置页面...');
    await page.click('text=设置');
    await delay(2000);

    console.log('✅ 演示完成！');

  } catch (error) {
    console.error('❌ 演示过程中出错:', error);
  } finally {
    await context.close();
    await browser.close();
    
    // 查找录制的视频文件
    const files = fs.readdirSync(outputDir);
    const videoFile = files.find(f => f.endsWith('.webm') || f.endsWith('.mp4'));
    
    if (videoFile) {
      const sourcePath = path.join(outputDir, videoFile);
      console.log(`🎥 视频已录制: ${sourcePath}`);
      
      // 转换为MP4
      console.log('🔄 转换视频格式...');
      // 这里可以添加FFmpeg转换逻辑
    }
    
    console.log(`📁 输出目录: ${outputDir}`);
  }
}

recordDemo().catch(console.error);
