#!/bin/bash
# ProteinHub MCP Browser Automation Demo
# 功能：自动截图生成蛋白详情页分享卡片

echo "🧬 ProteinHub MCP 浏览器自动化演示"
echo "======================================"

# 步骤1：访问蛋白详情页
echo "[1/3] 访问蛋白详情页 (PLIN1)..."
mcporter call playwright.playwright_navigate \
  url="http://localhost:5173/protein/PLIN1" \
  browserType="chromium" \
  headless=true

# 步骤2：等待页面加载并设置移动端视口（模拟手机分享卡片）
echo "[2/3] 设置 iPhone 14 视口..."
mcporter call playwright.playwright_resize \
  device="iPhone 14"

# 步骤3：截图保存
echo "[3/3] 生成分享卡片截图..."
mkdir -p /root/.openclaw/workspace/projects/proteinhub/screenshots
mcporter call playwright.playwright_screenshot \
  path="/root/.openclaw/workspace/projects/proteinhub/screenshots/PLIN1_share_card.png" \
  fullPage=false

echo "✅ 完成！截图已保存至:"
echo "   /root/.openclaw/workspace/projects/proteinhub/screenshots/PLIN1_share_card.png"
