import { createRouter, createWebHistory } from 'vue-router'
import Feed from '../views/Feed.vue'
import ProteinProfile from '../views/ProteinProfile.vue'
import LoginForm from '../components/LoginForm.vue'
import RegisterForm from '../components/RegisterForm.vue'
import NoteDetail from '../views/NoteDetail.vue'
import UserProfile from '../views/UserProfile.vue'

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
    component: () => import('../views/FollowedFeed.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/explore',
    name: 'Explore',
    component: () => import('../views/Explore.vue'),
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
