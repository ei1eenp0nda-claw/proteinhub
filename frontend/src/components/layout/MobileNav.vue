<template>
  <nav class="mobile-nav">
    <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
      <HomeFilled v-if="$route.path === '/'" />
      <HomeFilled v-else />
      <span>首页</span>
    </router-link>
    <router-link to="/explore" class="nav-item" :class="{ active: $route.path === '/explore' }">
      <Compass />
      <span>发现</span>
    </router-link>
    <router-link to="/publish" class="nav-item nav-publish">
      <div class="publish-icon">
        <Plus />
      </div>
    </router-link>
    <router-link to="/favorites" class="nav-item" :class="{ active: $route.path === '/favorites' }">
      <Star />
      <span>收藏</span>
    </router-link>
    <router-link to="/profile" class="nav-item" :class="{ active: $route.path === '/profile' }">
      <User />
      <span>我的</span>
    </router-link>
  </nav>
</template>

<script setup>
</script>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  padding: 0 10px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #999;
  text-decoration: none;
  font-size: 11px;
  transition: color 0.3s;
}

.nav-item.active {
  color: #ff2442;
}

.nav-item svg {
  font-size: 22px;
}

.nav-publish {
  margin-top: -20px;
}

.publish-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #ff2442 0%, #ff6b7a 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 36, 66, 0.4);
}

.publish-icon svg {
  font-size: 24px;
}
</style>