<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-content">
        <div class="footer-section">
          <h4>关于 ProteinHub</h4>
          <p>ProteinHub 是专注于生物医学领域的笔记分享平台，让知识传播更高效。</p>
        </div>
        <div class="footer-section">
          <h4>快速链接</h4>
          <ul>
            <li><a href="/">首页</a></li>
            <li><a href="/explore">发现</a></li>
            <li><a href="/publish">发布</a></li>
          </ul>
        </div>
        <div class="footer-section">
          <h4>联系我们</h4>
          <ul>
            <li><a href="mailto:contact@proteinhub.com">contact@proteinhub.com</a></li>
            <li><a href="#">帮助中心</a></li>
            <li><a href="#">用户协议</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2024 ProteinHub. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
.app-footer {
  background: #fff;
  border-top: 1px solid #eee;
  padding: 40px 0 20px;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 60px;
  margin-bottom: 40px;
}

.footer-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.footer-section p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.footer-section ul {
  list-style: none;
}

.footer-section li {
  margin-bottom: 8px;
}

.footer-section a {
  font-size: 14px;
  color: #666;
  text-decoration: none;
  transition: color 0.3s;
}

.footer-section a:hover {
  color: #ff2442;
}

.footer-bottom {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.footer-bottom p {
  font-size: 13px;
  color: #999;
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 30px;
  }
}
</style>