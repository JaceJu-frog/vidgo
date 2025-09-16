// 字幕样式处理
import { ref, computed, watch } from 'vue'
import { loadConfig, type FrontendSettings } from './ConfigAPI'

// 字幕样式类型定义
interface SubtitleStyleSettings {
  fontFamily: string
  fontColor: string
  fontSize: number
  fontWeight: string
  backgroundStyle: 'none' | 'solid' | 'semi-transparent' // 合并背景设置
  backgroundColor: string
  borderRadius: number
  textShadow: boolean
  textStroke: boolean // 新增：文字描边效果
  textStrokeColor: string // 新增：描边颜色
  textStrokeWidth: number // 新增：描边宽度
  bottomDistance: number // 新增：距底边距离（像素）
}

// 外文字幕样式类型定义
interface ForeignSubtitleStyleSettings {
  fontFamily: string
  fontColor: string
  fontSize: number
  fontWeight: string
  backgroundStyle: 'none' | 'solid' | 'semi-transparent'
  backgroundColor: string
  borderRadius: number
  textShadow: boolean
  textStroke: boolean // 新增：文字描边效果
  textStrokeColor: string // 新增：描边颜色
  textStrokeWidth: number // 新增：描边宽度
  bottomDistance: number
}

// 全局字幕样式状态 (原文字幕)
const subtitleSettings = ref<SubtitleStyleSettings>({
  fontFamily: '宋体',
  fontColor: '#ea9749',
  fontSize: 18,
  fontWeight: '400',
  backgroundStyle: 'semi-transparent', // 默认半透明背景
  backgroundColor: '#000000',
  borderRadius: 4,
  textShadow: false,
  textStroke: false, // 默认不开启描边
  textStrokeColor: '#000000', // 默认黑色描边
  textStrokeWidth: 2, // 默认描边宽度2px
  bottomDistance: 80, // 默认距离底边80像素
})

// 外文字幕样式状态
const foreignSubtitleSettings = ref<ForeignSubtitleStyleSettings>({
  fontFamily: 'Arial',
  fontColor: '#ffffff',
  fontSize: 16,
  fontWeight: '400',
  backgroundStyle: 'semi-transparent',
  backgroundColor: '#000000',
  borderRadius: 4,
  textShadow: false,
  textStroke: false, // 默认不开启描边
  textStrokeColor: '#000000', // 默认黑色描边
  textStrokeWidth: 2, // 默认描边宽度2px
  bottomDistance: 120, // 默认距离底边120像素，避免与原文重叠
})

// 全屏状态检测
const isFullscreen = ref(false)

// 监听全屏状态变化
const updateFullscreenState = () => {
  isFullscreen.value = !!(document.fullscreenElement || (document as any).webkitFullscreenElement)
}

// 响应式字体大小计算
const getResponsiveFontSize = (baseFontSize: number) => {
  // 在全屏模式下，根据视口宽度调整字体大小
  if (isFullscreen.value) {
    // 全屏模式：使用视口宽度的相对单位，确保字体在不同屏幕尺寸下保持合适比例
    const viewportWidth = window.innerWidth
    // const scaleFactor = Math.min(viewportWidth / 1280, 2) // 基于1920px宽度，最大放大2倍
    const scaleFactor = 1 // 基于1920px宽度，最大放大2倍
    console.log(
      `[SubtitleStyle] Fullscreen mode: viewportWidth=${viewportWidth}, scaleFactor=${scaleFactor.toFixed(2)}`,
    )
    return `${Math.round(baseFontSize * scaleFactor)}px`
  } else {
    // 浏览器模式：使用固定像素大小
    return `${baseFontSize}px`
  }
}

// 计算背景颜色
const getBackgroundColor = (style: string, color: string) => {
  switch (style) {
    case 'none':
      return 'transparent'
    case 'solid':
      return color
    case 'semi-transparent':
      // 将hex颜色转换为rgba，透明度0.8
      const hex = color.replace('#', '')
      const r = parseInt(hex.substring(0, 2), 16)
      const g = parseInt(hex.substring(2, 4), 16)
      const b = parseInt(hex.substring(4, 6), 16)
      return `rgba(${r}, ${g}, ${b}, 0.8)`
    default:
      return 'transparent'
  }
}

// 生成文字描边样式（使用多重text-shadow模拟描边效果）
const getTextStroke = (enabled: boolean, color: string, width: number) => {
  if (!enabled) return 'none'

  // 使用多重text-shadow创建描边效果，比-webkit-text-stroke兼容性更好
  const shadows = []
  for (let x = -width; x <= width; x++) {
    for (let y = -width; y <= width; y++) {
      if (x === 0 && y === 0) continue // 跳过中心点
      shadows.push(`${x}px ${y}px 0 ${color}`)
    }
  }
  return shadows.join(', ')
}

// 结合text-shadow和text-stroke效果
const getCombinedTextShadow = (
  textShadow: boolean,
  textStroke: boolean,
  strokeColor: string,
  strokeWidth: number,
) => {
  const effects = []

  // 添加描边效果
  if (textStroke) {
    const strokeEffect = getTextStroke(true, strokeColor, strokeWidth)
    if (strokeEffect !== 'none') {
      effects.push(strokeEffect)
    }
  }

  // 添加阴影效果
  if (textShadow) {
    effects.push('2px 2px 4px rgba(0,0,0,0.5)')
  }

  return effects.length > 0 ? effects.join(', ') : 'none'
}

// CSS变量样式字符串 (原文字幕)
const subtitleCSSVars = computed(() => ({
  '--subtitle-font-family': subtitleSettings.value.fontFamily,
  '--subtitle-color': subtitleSettings.value.fontColor,
  '--subtitle-font-size': `${subtitleSettings.value.fontSize}px`,
  '--subtitle-font-weight': subtitleSettings.value.fontWeight,
  '--subtitle-background-color': getBackgroundColor(
    subtitleSettings.value.backgroundStyle,
    subtitleSettings.value.backgroundColor,
  ),
  '--subtitle-border-radius': `${subtitleSettings.value.borderRadius}px`,
  '--subtitle-text-shadow': subtitleSettings.value.textShadow
    ? '2px 2px 4px rgba(0,0,0,0.5)'
    : 'none',
  '--subtitle-text-stroke': getTextStroke(
    subtitleSettings.value.textStroke,
    subtitleSettings.value.textStrokeColor,
    subtitleSettings.value.textStrokeWidth,
  ),
  '--subtitle-bottom-distance': `${subtitleSettings.value.bottomDistance}px`,
}))

// CSS变量样式字符串 (外文字幕)
const foreignSubtitleCSSVars = computed(() => ({
  '--foreign-subtitle-font-family': foreignSubtitleSettings.value.fontFamily,
  '--foreign-subtitle-color': foreignSubtitleSettings.value.fontColor,
  '--foreign-subtitle-font-size': `${foreignSubtitleSettings.value.fontSize}px`,
  '--foreign-subtitle-font-weight': foreignSubtitleSettings.value.fontWeight,
  '--foreign-subtitle-background-color': getBackgroundColor(
    foreignSubtitleSettings.value.backgroundStyle,
    foreignSubtitleSettings.value.backgroundColor,
  ),
  '--foreign-subtitle-border-radius': `${foreignSubtitleSettings.value.borderRadius}px`,
  '--foreign-subtitle-text-shadow': foreignSubtitleSettings.value.textShadow
    ? '2px 2px 4px rgba(0,0,0,0.5)'
    : 'none',
  '--foreign-subtitle-text-stroke': getTextStroke(
    foreignSubtitleSettings.value.textStroke,
    foreignSubtitleSettings.value.textStrokeColor,
    foreignSubtitleSettings.value.textStrokeWidth,
  ),
  '--foreign-subtitle-bottom-distance': `${foreignSubtitleSettings.value.bottomDistance}px`,
}))

// WebVTT字幕样式CSS字符串 (原文字幕)
const webVTTStyleCSS = computed(() => {
  const bgColor = getBackgroundColor(
    subtitleSettings.value.backgroundStyle,
    subtitleSettings.value.backgroundColor,
  )
  const padding = subtitleSettings.value.backgroundStyle === 'none' ? '2px 4px' : '4px 8px'
  const responsiveFontSize = getResponsiveFontSize(subtitleSettings.value.fontSize)

  const foreignBgColor = getBackgroundColor(
    foreignSubtitleSettings.value.backgroundStyle,
    foreignSubtitleSettings.value.backgroundColor,
  )
  const foreignPadding =
    foreignSubtitleSettings.value.backgroundStyle === 'none' ? '2px 4px' : '4px 8px'
  const foreignResponsiveFontSize = getResponsiveFontSize(foreignSubtitleSettings.value.fontSize)

  return `
  /* 原文字幕显示容器 - 强制设置位置，覆盖Video.js的inset-block */
  .video-js .vjs-text-track-display[data-subtitle-lang="primary"],
  .video-js .vjs-text-track-display:not([data-subtitle-lang]) {
    bottom: ${subtitleSettings.value.bottomDistance}px !important;
    top: auto !important;
    inset-block: auto !important;
    inset-block-end: ${subtitleSettings.value.bottomDistance}px !important;
    inset-block-start: auto !important;
    position: absolute !important;
  }

  /* 外文字幕显示容器 */
  .video-js .vjs-text-track-display[data-subtitle-lang="translation"] {
    bottom: ${foreignSubtitleSettings.value.bottomDistance}px !important;
    top: auto !important;
    inset-block: auto !important;
    inset-block-end: ${foreignSubtitleSettings.value.bottomDistance}px !important;
    inset-block-start: auto !important;
    position: absolute !important;
  }

  /* 双语字幕容器 - 需要特殊处理，可能包含两种语言 */
  .video-js .vjs-text-track-display[data-subtitle-lang="both"] {
    bottom: ${Math.min(subtitleSettings.value.bottomDistance, foreignSubtitleSettings.value.bottomDistance)}px !important;
    top: auto !important;
    inset-block: auto !important;
    inset-block-end: ${Math.min(subtitleSettings.value.bottomDistance, foreignSubtitleSettings.value.bottomDistance)}px !important;
    inset-block-start: auto !important;
    position: absolute !important;
  }

  /* 字幕轨道容器 - 移除任何背景 */
  .video-js .vjs-text-track-display .vjs-text-track-cue {
    background-color: transparent !important;
    background: none !important;
  }

  /* 原文字幕最内层的文字div设置样式和背景 */
  .video-js .vjs-text-track-display[data-subtitle-lang="primary"] .vjs-text-track-cue > div,
  .video-js .vjs-text-track-display:not([data-subtitle-lang]) .vjs-text-track-cue > div {
    font-family: ${subtitleSettings.value.fontFamily} !important;
    color: ${subtitleSettings.value.fontColor} !important;
    font-size: ${responsiveFontSize} !important;
    font-weight: ${subtitleSettings.value.fontWeight} !important;
    background-color: ${bgColor} !important;
    border-radius: ${subtitleSettings.value.borderRadius}px !important;
    padding: ${padding} !important;
    text-shadow: ${getCombinedTextShadow(
      subtitleSettings.value.textShadow,
      subtitleSettings.value.textStroke,
      subtitleSettings.value.textStrokeColor,
      subtitleSettings.value.textStrokeWidth,
    )} !important;
    line-height: 1.4 !important;
    display: inline !important;
    box-decoration-break: clone !important;
    -webkit-box-decoration-break: clone !important;
  }

  /* 外文字幕最内层的文字div设置样式和背景 */
  .video-js .vjs-text-track-display[data-subtitle-lang="translation"] .vjs-text-track-cue > div {
    font-family: ${foreignSubtitleSettings.value.fontFamily} !important;
    color: ${foreignSubtitleSettings.value.fontColor} !important;
    font-size: ${foreignResponsiveFontSize} !important;
    font-weight: ${foreignSubtitleSettings.value.fontWeight} !important;
    background-color: ${foreignBgColor} !important;
    border-radius: ${foreignSubtitleSettings.value.borderRadius}px !important;
    padding: ${foreignPadding} !important;
    text-shadow: ${getCombinedTextShadow(
      foreignSubtitleSettings.value.textShadow,
      foreignSubtitleSettings.value.textStroke,
      foreignSubtitleSettings.value.textStrokeColor,
      foreignSubtitleSettings.value.textStrokeWidth,
    )} !important;
    line-height: 1.4 !important;
    display: inline !important;
    box-decoration-break: clone !important;
    -webkit-box-decoration-break: clone !important;
  }

  /* 双语字幕样式 - 使用原文字幕样式，强制换行显示 */
  .video-js .vjs-text-track-display[data-subtitle-lang="both"] .vjs-text-track-cue > div {
    font-family: ${subtitleSettings.value.fontFamily} !important;
    color: ${subtitleSettings.value.fontColor} !important;
    font-size: ${responsiveFontSize} !important;
    font-weight: ${subtitleSettings.value.fontWeight} !important;
    background-color: ${bgColor} !important;
    border-radius: ${subtitleSettings.value.borderRadius}px !important;
    padding: ${padding} !important;
    text-shadow: ${getCombinedTextShadow(
      subtitleSettings.value.textShadow,
      subtitleSettings.value.textStroke,
      subtitleSettings.value.textStrokeColor,
      subtitleSettings.value.textStrokeWidth,
    )} !important;
    line-height: 1.4 !important;
    display: inline-block !important;
    box-decoration-break: clone !important;
    -webkit-box-decoration-break: clone !important;
    white-space: pre-line !important; /* 保持换行符显示为换行 */
  }

  /* WebVTT原文字幕cue样式 - 用于浏览器原生渲染 */
  .video-js ::cue[data-language="primary"],
  .video-js ::cue:not([data-language]) {
    font-family: ${subtitleSettings.value.fontFamily} !important;
    color: ${subtitleSettings.value.fontColor} !important;
    font-size: ${responsiveFontSize} !important;
    font-weight: ${subtitleSettings.value.fontWeight} !important;
    background-color: ${bgColor} !important;
    text-shadow: ${getCombinedTextShadow(
      subtitleSettings.value.textShadow,
      subtitleSettings.value.textStroke,
      subtitleSettings.value.textStrokeColor,
      subtitleSettings.value.textStrokeWidth,
    )} !important;
  }

  /* WebVTT外文字幕cue样式 - 用于浏览器原生渲染 */
  .video-js ::cue[data-language="translation"] {
    font-family: ${foreignSubtitleSettings.value.fontFamily} !important;
    color: ${foreignSubtitleSettings.value.fontColor} !important;
    font-size: ${foreignResponsiveFontSize} !important;
    font-weight: ${foreignSubtitleSettings.value.fontWeight} !important;
    background-color: ${foreignBgColor} !important;
    text-shadow: ${getCombinedTextShadow(
      foreignSubtitleSettings.value.textShadow,
      foreignSubtitleSettings.value.textStroke,
      foreignSubtitleSettings.value.textStrokeColor,
      foreignSubtitleSettings.value.textStrokeWidth,
    )} !important;
  }

  /* WebVTT双语字幕cue样式 */
  .video-js ::cue[data-language="both"] {
    font-family: ${subtitleSettings.value.fontFamily} !important;
    color: ${subtitleSettings.value.fontColor} !important;
    font-size: ${responsiveFontSize} !important;
    font-weight: ${subtitleSettings.value.fontWeight} !important;
    background-color: ${bgColor} !important;
    text-shadow: ${getCombinedTextShadow(
      subtitleSettings.value.textShadow,
      subtitleSettings.value.textStroke,
      subtitleSettings.value.textStrokeColor,
      subtitleSettings.value.textStrokeWidth,
    )} !important;
  }

  /* 确保背景不会延展到整行 */
  .video-js .vjs-text-track-display div[style*="background-color"] {
    background-color: transparent !important;
  }
  
  /* 只保留最内层文字元素的背景 */
  .video-js .vjs-text-track-display .vjs-text-track-cue > div[style*="font-family"] {
    background-color: transparent !important;
  }
  .video-js .vjs-text-track-display[data-subtitle-lang="primary"] .vjs-text-track-cue > div[style*="font-family"],
  .video-js .vjs-text-track-display:not([data-subtitle-lang]) .vjs-text-track-cue > div[style*="font-family"] {
    background-color: ${bgColor} !important;
  }
  .video-js .vjs-text-track-display[data-subtitle-lang="translation"] .vjs-text-track-cue > div[style*="font-family"] {
    background-color: ${foreignBgColor} !important;
  }
  .video-js .vjs-text-track-display[data-subtitle-lang="both"] .vjs-text-track-cue > div[style*="font-family"] {
    background-color: ${bgColor} !important;
  }
`
})

// 全局样式注入标识
let globalStyleElement: HTMLStyleElement | null = null

// 注入全局字幕样式
function injectGlobalSubtitleStyles() {
  // 移除旧的样式
  if (globalStyleElement) {
    globalStyleElement.remove()
  }

  // 创建新的样式元素
  globalStyleElement = document.createElement('style')
  globalStyleElement.id = 'vidgo-subtitle-styles'
  globalStyleElement.textContent = webVTTStyleCSS.value
  document.head.appendChild(globalStyleElement)
}

// 监听样式变化并自动更新
watch(
  [webVTTStyleCSS, isFullscreen],
  () => {
    injectGlobalSubtitleStyles()
  },
  { immediate: true },
)

// 设置全屏状态监听器
if (typeof document !== 'undefined') {
  document.addEventListener('fullscreenchange', updateFullscreenState)
  document.addEventListener('webkitfullscreenchange', updateFullscreenState)
  window.addEventListener('resize', updateFullscreenState)
}

// 从配置加载字幕样式
async function loadSubtitleSettings() {
  try {
    const config = await loadConfig()

    // 加载原文字幕设置
    subtitleSettings.value = {
      fontFamily: config.fontFamily || '宋体',
      fontColor: config.fontColor || '#ea9749',
      fontSize: config.fontSize || 18,
      fontWeight: config.fontWeight || '400',
      backgroundStyle: config.backgroundStyle || 'semi-transparent',
      backgroundColor: config.backgroundColor || '#000000',
      borderRadius: config.borderRadius || 4,
      textShadow: config.textShadow ?? false,
      textStroke: config.textStroke ?? false,
      textStrokeColor: config.textStrokeColor || '#000000',
      textStrokeWidth: config.textStrokeWidth || 2,
      bottomDistance: config.bottomDistance || 80,
    }

    // 加载外文字幕设置
    foreignSubtitleSettings.value = {
      fontFamily: config.foreignFontFamily || 'Arial',
      fontColor: config.foreignFontColor || '#ffffff',
      fontSize: config.foreignFontSize || 16,
      fontWeight: config.foreignFontWeight || '400',
      backgroundStyle: config.foreignBackgroundStyle || 'semi-transparent',
      backgroundColor: config.foreignBackgroundColor || '#000000',
      borderRadius: config.foreignBorderRadius || 4,
      textShadow: config.foreignTextShadow ?? false,
      textStroke: config.foreignTextStroke ?? false,
      textStrokeColor: config.foreignTextStrokeColor || '#000000',
      textStrokeWidth: config.foreignTextStrokeWidth || 2,
      bottomDistance: config.foreignBottomDistance || 120,
    }

    console.log('[SubtitleStyle] Loaded raw subtitle settings:', subtitleSettings.value)
    console.log('[SubtitleStyle] Loaded foreign subtitle settings:', foreignSubtitleSettings.value)
  } catch (error) {
    console.error('[SubtitleStyle] Failed to load subtitle settings:', error)
  }
}

// 更新原文字幕样式
function updateSubtitleSettings(newSettings: Partial<typeof subtitleSettings.value>) {
  Object.assign(subtitleSettings.value, newSettings)
  console.log('[SubtitleStyle] Updated raw subtitle settings:', subtitleSettings.value)
}

// 更新外文字幕样式
function updateForeignSubtitleSettings(newSettings: Partial<typeof foreignSubtitleSettings.value>) {
  Object.assign(foreignSubtitleSettings.value, newSettings)
  console.log('[SubtitleStyle] Updated foreign subtitle settings:', foreignSubtitleSettings.value)
}

// 清理函数
function cleanup() {
  if (globalStyleElement) {
    globalStyleElement.remove()
    globalStyleElement = null
  }
  // 移除事件监听器
  if (typeof document !== 'undefined') {
    document.removeEventListener('fullscreenchange', updateFullscreenState)
    document.removeEventListener('webkitfullscreenchange', updateFullscreenState)
    window.removeEventListener('resize', updateFullscreenState)
  }
}

export function useSubtitleStyle() {
  return {
    // 原文字幕相关
    subtitleSettings: subtitleSettings,
    subtitleCSSVars,
    updateSubtitleSettings,
    // 外文字幕相关
    foreignSubtitleSettings: foreignSubtitleSettings,
    foreignSubtitleCSSVars,
    updateForeignSubtitleSettings,
    // 通用功能
    webVTTStyleCSS,
    isFullscreen,
    loadSubtitleSettings,
    updateFullscreenState,
    injectGlobalSubtitleStyles,
    cleanup,
  }
}
