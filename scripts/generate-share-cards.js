#!/usr/bin/env node
/**
 * ProteinHub MCP Browser Automation Demo
 * 
 * 功能：自动生成蛋白详情页的社交分享卡片截图
 * 应用场景：小红书式App的"生成分享图"功能
 */

const { chromium } = require('/root/.openclaw/workspace/projects/proteinhub/frontend/node_modules/playwright');
const fs = require('fs');
const path = require('path');

// 配置
const CONFIG = {
  baseUrl: 'http://localhost:5173',
  proteinId: 'PLIN1',
  outputDir: path.join(__dirname, '../screenshots'),
  devices: [
    { name: 'iPhone 14', width: 390, height: 844 },
    { name: 'Desktop', width: 1280, height: 800 }
  ]
};

async function generateShareCards() {
  console.log('🧬 ProteinHub MCP 浏览器自动化演示');
  console.log('======================================\n');

  // 确保输出目录存在
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }

  // 启动浏览器
  console.log('[1/5] 启动 Chromium...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    // 创建新页面
    console.log('[2/5] 创建新页面...');
    const context = await browser.newContext();
    const page = await context.newPage();

    // 访问蛋白详情页
    const proteinUrl = `${CONFIG.baseUrl}/protein/${CONFIG.proteinId}`;
    console.log(`[3/5] 访问蛋白详情页: ${proteinUrl}`);
    
    try {
      await page.goto(proteinUrl, { 
        waitUntil: 'networkidle',
        timeout: 10000 
      });
    } catch (e) {
      console.log('   ⚠️ 页面加载超时，继续截图...');
    }

    // 等待页面渲染
    await page.waitForTimeout(2000);

    // 为不同设备生成截图
    console.log('[4/5] 生成多设备截图...\n');
    
    for (const device of CONFIG.devices) {
      console.log(`   📱 ${device.name} (${device.width}x${device.height})`);
      
      await page.setViewportSize({
        width: device.width,
        height: device.height
      });
      
      await page.waitForTimeout(500);
      
      const screenshotPath = path.join(
        CONFIG.outputDir, 
        `${CONFIG.proteinId}_share_${device.name.toLowerCase().replace(' ', '_')}.png`
      );
      
      await page.screenshot({
        path: screenshotPath,
        fullPage: false
      });
      
      console.log(`      ✅ ${screenshotPath}`);
    }

    // 生成全页面截图
    console.log('\n   📄 Full Page Screenshot');
    const fullPagePath = path.join(CONFIG.outputDir, `${CONFIG.proteinId}_fullpage.png`);
    await page.screenshot({
      path: fullPagePath,
      fullPage: true
    });
    console.log(`      ✅ ${fullPagePath}`);

    // 提取页面信息
    console.log('\n[5/5] 提取页面信息...');
    const pageInfo = await page.evaluate(() => ({
      title: document.title,
      url: window.location.href,
      proteinName: document.querySelector('h1')?.textContent?.trim() || 'N/A',
      noteCount: document.querySelectorAll('.note-card').length || 0
    }));
    
    console.log('   📊 页面数据:');
    console.log(`      标题: ${pageInfo.title}`);
    console.log(`      蛋白名: ${pageInfo.proteinName}`);
    console.log(`      Note数量: ${pageInfo.noteCount}`);

    // 保存元数据
    const metadataPath = path.join(CONFIG.outputDir, `${CONFIG.proteinId}_metadata.json`);
    fs.writeFileSync(metadataPath, JSON.stringify({
      proteinId: CONFIG.proteinId,
      capturedAt: new Date().toISOString(),
      devices: CONFIG.devices.map(d => d.name),
      pageInfo
    }, null, 2));
    console.log(`      ✅ 元数据已保存: ${metadataPath}`);

  } finally {
    await browser.close();
  }

  console.log('\n✅ 全部完成！截图文件:');
  const files = fs.readdirSync(CONFIG.outputDir)
    .filter(f => f.startsWith(CONFIG.proteinId))
    .map(f => `   📷 ${path.join(CONFIG.outputDir, f)}`);
  files.forEach(f => console.log(f));
}

// 运行
generateShareCards().catch(err => {
  console.error('❌ 错误:', err.message);
  process.exit(1);
});
