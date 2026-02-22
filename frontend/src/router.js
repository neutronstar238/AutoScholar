import { createRouter, createWebHistory } from 'vue-router'
import Home from './pages/Home.vue'
import Notes from './pages/Notes.vue'
import Research from './pages/Research.vue'
import User from './pages/User.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/notes', name: 'Notes', component: Notes },
  { path: '/research', name: 'Research', component: Research },
  { path: '/user', name: 'User', component: User }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
