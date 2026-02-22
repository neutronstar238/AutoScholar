import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 配置 axios 基础 URL
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
