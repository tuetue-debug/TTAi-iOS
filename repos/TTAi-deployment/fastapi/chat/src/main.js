import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import ChatPage from './pages/ChatPage.vue'
import LoginPage from './pages/LoginPage.vue'
import MemoryPage from './pages/MemoryPage.vue'
import ProjectsPage from './pages/ProjectsPage.vue'
import './style.css'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/c/new' },
    { path: '/login', component: LoginPage, name: 'login' },
    { path: '/c/new', component: ChatPage, name: 'new-chat' },
    { path: '/c/:id', component: ChatPage, name: 'chat' },
    { path: '/memory', component: MemoryPage, name: 'memory', meta: { requiresAuth: true } },
    { path: '/projects', component: ProjectsPage, name: 'projects', meta: { requiresAuth: true } },
  ],
})

const app = createApp(App)
app.use(router)
app.mount('#app')
