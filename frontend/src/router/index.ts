import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
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
    name: 'UserSpace',
    component: UserProfileView
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
    component: CreatorStudioView
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView
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

export default router
