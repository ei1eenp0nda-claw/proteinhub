#!/usr/bin/env node
/**
 * ProteinHub 截图测试 - 首页
 */

const { chromium } = require('/root/.openclaw/workspace/projects/proteinhub/frontend/node_modules/playwright');
const path = require('path');

async function testHomepage() {
  console.log('🧪 测试 ProteinHub 首页...\n');
  
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 }
    });
    const page = await context.newPage();

    // 访问首页
    console.log('[1/2] 访问首页...');
    await page.goto('http://localhost:5173/', { 
      waitUntil: 'networkidle',
      timeout: 15000 
    });
    await page.waitForTimeout(3000);

    // 截图
    console.log('[2/2] 截图...');
    const outputDir = path.join(__dirname, '../screenshots');
    await page.screenshot({
      path: path.join(outputDir, 'homepage_test.png'),
      fullPage: true
    });

    // 获取页面信息
    const info = await page.evaluate(() => ({
      title: document.title,
      hasContent: document.body.innerText.length > 100,
      text: document.body.innerText.substring(0, 200)
    }));
    
    console.log('\n📊 页面信息:');
    console.log(`   标题: ${info.title}`);
    console.log(`   有内容: ${info.hasContent}`);
    console.log(`   内容预览: ${info.text}...`);

    console.log('\n✅ 截图已保存: screenshots/homepage_test.png');

  } catch (err) {
    console.error('❌ 错误:', err.message);
  } finally {
    await browser.close();
  }
}

testHomepage();
