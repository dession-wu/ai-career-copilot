const express = require('express');
const puppeteer = require('puppeteer');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const PORT = process.env.PORT || 3002;

// 中间件
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002'],
  methods: ['POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json({ limit: '10mb' }));

// 主题样式定义
const RESUME_THEMES = {
  default: {
    name: '默认',
    styles: `
      :root {
        --primary-color: #2c2c2c;
        --secondary-color: #666;
        --accent-color: #c45c3e;
        --bg-color: #fff;
        --surface-color: #f8f9fa;
        --border-color: #e5e5e5;
        --font-heading: 'Georgia', 'Times New Roman', serif;
        --font-body: 'Helvetica Neue', Arial, sans-serif;
      }
    `
  },
  minimal: {
    name: '极简',
    description: '简洁干净，突出重点',
    styles: `
      :root {
        --primary-color: #1a1a1a;
        --secondary-color: #4a4a4a;
        --accent-color: #1a1a1a;
        --bg-color: #ffffff;
        --surface-color: #f8f9fa;
        --border-color: #e5e7eb;
        --font-heading: system-ui, -apple-system, sans-serif;
        --font-body: system-ui, -apple-system, sans-serif;
      }
    `
  },
  professional: {
    name: '专业',
    description: '经典商务风格，适合传统行业',
    styles: `
      :root {
        --primary-color: #1e3a5f;
        --secondary-color: #2c5282;
        --accent-color: #2b6cb0;
        --bg-color: #ffffff;
        --surface-color: #f7fafc;
        --border-color: #cbd5e0;
        --font-heading: Georgia, 'Times New Roman', serif;
        --font-body: system-ui, -apple-system, sans-serif;
      }
    `
  },
  modern: {
    name: '现代',
    description: '时尚现代，适合互联网/科技行业',
    styles: `
      :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #6366f1;
        --bg-color: #ffffff;
        --surface-color: #f5f3ff;
        --border-color: #e5e7eb;
        --font-heading: 'Inter', system-ui, sans-serif;
        --font-body: 'Inter', system-ui, sans-serif;
      }
    `
  },
  creative: {
    name: '创意',
    description: '大胆配色，适合设计/创意行业',
    styles: `
      :root {
        --primary-color: #ec4899;
        --secondary-color: #f472b6;
        --accent-color: #db2777;
        --bg-color: #fdf2f8;
        --surface-color: #fce7f3;
        --border-color: #fbcfe8;
        --font-heading: 'Poppins', sans-serif;
        --font-body: 'Open Sans', sans-serif;
      }
    `
  }
};

// HTML 模板生成
function generateResumeHTML(content, theme = 'default', customCSS = '') {
  const themeStyles = RESUME_THEMES[theme]?.styles || RESUME_THEMES.default.styles;
  
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>简历</title>
  <style>
    ${themeStyles}
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: var(--font-body);
      font-size: 11pt;
      line-height: 1.6;
      color: var(--primary-color);
      background: var(--bg-color);
      padding: 0;
      margin: 0;
    }
    
    .resume-container {
      max-width: 210mm;
      margin: 0 auto;
      padding: 20mm;
      background: white;
    }
    
    h1, h2, h3, h4, h5, h6 {
      font-family: var(--font-heading);
      color: var(--primary-color);
      margin-top: 1em;
      margin-bottom: 0.5em;
    }
    
    h1 { font-size: 1.8em; border-bottom: 2px solid var(--accent-color); padding-bottom: 0.3em; }
    h2 { font-size: 1.4em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.2em; }
    h3 { font-size: 1.2em; color: var(--secondary-color); }
    
    p {
      margin-bottom: 0.8em;
      text-align: justify;
    }
    
    ul, ol {
      margin-left: 1.5em;
      margin-bottom: 0.8em;
    }
    
    li {
      margin-bottom: 0.3em;
    }
    
    strong {
      font-weight: 600;
      color: var(--primary-color);
    }
    
    a {
      color: var(--accent-color);
      text-decoration: none;
    }
    
    blockquote {
      border-left: 3px solid var(--accent-color);
      padding-left: 1em;
      margin: 1em 0;
      color: var(--secondary-color);
      font-style: italic;
    }
    
    code {
      background: #f5f5f5;
      padding: 0.2em 0.4em;
      border-radius: 3px;
      font-family: 'Consolas', monospace;
      font-size: 0.9em;
    }
    
    pre {
      background: #f5f5f5;
      padding: 1em;
      border-radius: 5px;
      overflow-x: auto;
      margin: 1em 0;
    }
    
    hr {
      border: none;
      border-top: 1px solid var(--border-color);
      margin: 1.5em 0;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
    }
    
    th, td {
      border: 1px solid var(--border-color);
      padding: 0.5em;
      text-align: left;
    }
    
    th {
      background: #f5f5f5;
      font-weight: 600;
    }
    
    /* 打印优化 */
    @media print {
      body {
        background: white;
      }
      
      .resume-container {
        padding: 0;
        max-width: none;
      }
      
      h1, h2 {
        page-break-after: avoid;
      }
      
      p, li {
        page-break-inside: avoid;
      }
    }
    
    /* 自定义 CSS */
    ${customCSS}
  </style>
</head>
<body>
  <div class="resume-container">
    ${content}
  </div>
</body>
</html>
  `;
}

// PDF 导出端点
app.post('/export/pdf', async (req, res) => {
  let browser = null;
  
  try {
    const { html, theme = 'default', customCSS = '', filename = 'resume.pdf' } = req.body;
    
    if (!html) {
      return res.status(400).json({ error: 'HTML content is required' });
    }
    
    // 生成完整 HTML
    const fullHTML = generateResumeHTML(html, theme, customCSS);
    
    let pdfBuffer = null;
    let lastError = null;

    /* headless shell 模式下 Chrome 存在偶发崩溃(Target closed 等)，
       整体失败时自动重试一次，提升服务可用性 */
    for (let attempt = 1; attempt <= 2; attempt++) {
      try {
        // 启动 Puppeteer
        browser = await puppeteer.launch({
          headless: 'shell',
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--disable-gpu'
          ]
        });

        const page = await browser.newPage();

        // 设置页面内容
        await page.setContent(fullHTML, {
          waitUntil: 'domcontentloaded'
        });

        // 等待字体加载（失败不阻断，仅影响字体精细度）
        try {
          await page.evaluateHandle('document.fonts.ready');
        } catch (fontErr) {
          console.warn('fonts.ready skipped:', fontErr.message);
        }

        // 生成 PDF
        pdfBuffer = await page.pdf({
          format: 'A4',
          printBackground: true,
          margin: {
            top: '0',
            right: '0',
            bottom: '0',
            left: '0'
          },
          preferCSSPageSize: true,
          scale: 1.5
        });

        // 关闭浏览器
        await browser.close();
        browser = null;
        lastError = null;
        break;
      } catch (renderError) {
        lastError = renderError;
        console.error(`PDF render attempt ${attempt} failed:`, renderError.message);
        if (browser) {
          try { await browser.close(); } catch (e) { /* 忽略关闭异常 */ }
          browser = null;
        }
      }
    }

    if (!pdfBuffer || !pdfBuffer.length) {
      throw lastError || new Error('PDF generation produced empty result');
    }
    
    // 设置响应头
    // 对文件名进行编码，处理中文字符和特殊字符
    // 使用 RFC 5987 标准：filename 使用 ASCII 安全字符，filename* 使用 UTF-8 编码
    const encodedFilename = encodeURIComponent(filename);
    // 为 filename 参数创建 ASCII 安全版本（移除或替换非 ASCII 字符）
    const asciiFilename = filename.replace(/[^\x00-\x7F]/g, '_');
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${asciiFilename}"; filename*=UTF-8''${encodedFilename}`);
    res.setHeader('Content-Length', pdfBuffer.length);
    
    // 发送 PDF
    res.send(pdfBuffer);
    
  } catch (error) {
    console.error('PDF generation error:', error);
    
    if (browser) {
      await browser.close();
    }
    
    res.status(500).json({
      error: 'PDF generation failed',
      message: error.message
    });
  }
});

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 主题列表端点
app.get('/themes', (req, res) => {
  const themes = Object.entries(RESUME_THEMES).map(([key, value]) => ({
    id: key,
    name: value.name
  }));
  res.json({ themes });
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`PDF Service running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Available themes: ${Object.keys(RESUME_THEMES).join(', ')}`);
});
