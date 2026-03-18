import { createRouter, createWebHistory } from 'vue-router'

// 首屏关键组件同步加载
import Feed from '../views/Feed.vue'

// 其他组件懒加载
const NoteDetail = () => import('../views/NoteDetail.vue')
const UserProfile = () => import('../views/UserProfile.vue')
const ProteinProfile = () => import('../views/ProteinProfile.vue')
const LoginForm = () => import('../components/LoginForm.vue')
const RegisterForm = () => import('../components/RegisterForm.vue')
const FollowedFeed = () => import('../views/FollowedFeed.vue')
const Explore = () => import('../views/Explore.vue')
const Search = () => import('../views/Search.vue')

const routes = [
  {
    path: '/',
    name: 'Feed',
    component: Feed,
    meta: { requiresAuth: false }
  },
  {
    path: '/note/:id',
    name: 'NoteDetail',
    component: NoteDetail,
    meta: { requiresAuth: false }
  },
  {
    path: '/user/:id',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: false }
  },
  {
    path: '/protein/:id',
    name: 'ProteinProfile',
    component: ProteinProfile,
    props: true,
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginForm,
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterForm,
    meta: { guest: true }
  },
  {
    path: '/followed',
    name: 'FollowedFeed',
    component: FollowedFeed,
    meta: { requiresAuth: true }
  },
  {
    path: '/explore',
    name: 'Explore',
    component: Explore,
    meta: { requiresAuth: false }
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/')
  } else {
    next()
  }
})

export default router