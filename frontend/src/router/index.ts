import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import HomeView from '../views/HomeView.vue'
import PlayerView from '../views/PlayerView.vue'
import LandingView from '../views/LandingView.vue'
import CreatorStudioView from '../views/CreatorStudioView.vue'
import AdminView from '../views/AdminView.vue'
import LoginView from '../views/LoginView.vue'
import UserProfileView from '../views/UserProfileView.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/landing',
    name: 'Landing',
    component: LandingView
  },
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/register',
    name: 'Register',
    component: LoginView
  },
  {
    path: '/user/space',
    alias: '/profile',
    name: 'UserSpace',
    component: UserProfileView,
    meta: { requiresAuth: true }
  },
  {
    path: '/video/:id?',
    name: 'Player',
    component: PlayerView,
    props: true
  },
  {
    path: '/play/:id?',
    name: 'PlayerAlias',
    component: PlayerView,
    props: true
  },
  {
    path: '/creator',
    name: 'CreatorStudio',
    component: CreatorStudioView,
    meta: { requiresAuth: true, allowedRoles: ['ADMIN', 'CREATOR'] }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAuth: true, allowedRoles: ['ADMIN', 'REVIEWER'] }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 全局路由导航前置守卫：三权分立与越权拦截
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token')
  let user: any = null
  try {
    const raw = localStorage.getItem('user')
    if (raw) user = JSON.parse(raw)
  } catch (e) {
    user = null
  }

  // 1. 登录状态强拦截
  if (to.meta.requiresAuth && !token) {
    ElMessage.warning('请先登录后再进行此操作')
    return next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  }

  // 2. 角色越权强拦截
  const allowedRoles = to.meta.allowedRoles as string[] | undefined
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = (user?.role || 'USER').toUpperCase()
    const isCreatorBool = !!user?.is_creator
    const isReviewerBool = !!user?.is_reviewer

    let hasPermission = allowedRoles.includes(userRole)
    if (!hasPermission && allowedRoles.includes('CREATOR') && isCreatorBool) {
      hasPermission = true
    }
    if (!hasPermission && allowedRoles.includes('REVIEWER') && isReviewerBool) {
      hasPermission = true
    }
    if (userRole === 'ADMIN') {
      hasPermission = true
    }

    if (!hasPermission) {
      ElMessage.error('您当前的账号角色无权访问该管理中台，已自动返回大厅')
      return next('/')
    }
  }

  next()
})

export default router

