import '@/assets/main.css'

import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from '@/App.vue'
import 'video.js/dist/video-js.css'
import './assets/tailwind.css'
import '@/assets/vjs-luxmty/vjs-luxmty.css'

import router from '@/router'
import en from '@/locales/en'
import zh from '@/locales/zh'

import ElementPlus from 'element-plus'
import enEl from 'element-plus/es/locale/lang/en'
import zhEl from 'element-plus/es/locale/lang/zh-cn'

import 'element-plus/dist/index.css'
import '@/assets/tailwind.css' // <-  if you keep Tailwind

// 全局处理未捕获的 Promise 错误（API 调用失败）
window.addEventListener('unhandledrejection', (event) => {
  console.warn('API request failed (this is normal in static mode):', event.reason)
  event.preventDefault() // 防止应用崩溃
})

// 全局处理 JavaScript 错误
window.addEventListener('error', (event) => {
  console.warn('JavaScript error:', event.error)
  event.preventDefault()
})

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('lang') || 'en',
  fallbackLocale: 'zh',
  messages: { en, zh },
})

const app = createApp(App)

// Vue 应用级错误处理
app.config.errorHandler = (err, instance, info) => {
  console.warn('Vue error:', err, info)
}

app.use(i18n)
app.use(ElementPlus, { locale: i18n.global.locale.value === 'zh' ? zhEl : enEl })
app.use(router)

const vueApp = app.mount('#app')
// Add this after mounting the app
;(window as any).vueApp = vueApp
