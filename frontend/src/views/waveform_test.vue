<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.js'
import { Play, Pause, SkipBack, SkipForward } from 'lucide-vue-next'

// 组件状态
const waveformContainer = ref<HTMLDivElement>()
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isLoading = ref(true)
const audioUrl = ref('')
const zoomLevel = ref(100) // 缩放级别

// WaveSurfer 实例
let wavesurfer: WaveSurfer | null = null

// 测试用的音频文件名
const testAudioFile = '一部关于糖的电影---最甜蜜的慢性杀手就在我们身边(双语字幕).mp3'

// 获取波形峰值数据
async function fetchWaveformPeaks() {
  try {
    // 构建后端API URL获取波形数据
    console.log(`http://172.28.241.92:8000/api/waveform/${encodeURIComponent(testAudioFile)}`)
    const response = await fetch(
      `http://172.28.241.92:8000/api/waveform/${encodeURIComponent(testAudioFile)}`,
    )
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    const peaksData = await response.json()
    return peaksData
  } catch (error) {
    console.error('Failed to fetch waveform peaks:', error)
    // 如果API不存在，返回模拟数据
    return generateMockPeaks()
  }
}

// 生成模拟波形数据
function generateMockPeaks() {
  const peaks = []
  const length = 5000 // 5000个采样点
  for (let i = 0; i < length; i++) {
    // 生成模拟的音频波形数据
    const t = (i / length) * Math.PI * 20
    const amplitude = Math.sin(t) * Math.exp(-t / 10) * (0.3 + 0.7 * Math.random())
    peaks.push(Math.max(-1, Math.min(1, amplitude)))
  }

  return {
    version: '1.0',
    audio_file: testAudioFile,
    duration: 5815.12,
    samples_per_second: 10,
    length: peaks.length,
    peaks: peaks,
  }
}

// 初始化 WaveSurfer
async function initWaveSurfer() {
  if (!waveformContainer.value) {
    console.error('waveformContainer is not available')
    isLoading.value = false
    return
  }

  isLoading.value = true

  try {
    // 获取波形峰值数据
    const peaksData = await fetchWaveformPeaks()
    // console.log(peaksData)
    // 设置音频URL
    audioUrl.value = `http://172.28.241.92:8000/media/saved_audio/${testAudioFile}`

    // 创建 WaveSurfer 实例
    wavesurfer = WaveSurfer.create({
      container: waveformContainer.value,
      height: 120,
      waveColor: '#3b82f6',
      progressColor: '#1d4ed8',
      cursorColor: '#ef4444',
      barWidth: 1,
      barGap: 0.5,
      barRadius: 1,
      normalize: true,
      mediaControls: false,
      minPxPerSec: 100, // 增加最小像素密度，确保有水平滚动
      peaks: [peaksData.peaks], // 使用预生成的峰值数据
      duration: peaksData.duration, // 设置总时长
      autoScroll: true,
    })

    // 监听事件
    wavesurfer.on('ready', () => {
      isLoading.value = false
      duration.value = wavesurfer?.getDuration() || peaksData.duration
      console.log('Waveform ready, duration:', duration.value)
    })

    wavesurfer.on('play', () => {
      isPlaying.value = true
    })

    wavesurfer.on('pause', () => {
      isPlaying.value = false
    })

    // wavesurfer.on('timeupdate', (time) => {
    //   currentTime.value = time
    // })

    wavesurfer.on('error', (error) => {
      console.error('WaveSurfer error:', error)
      isLoading.value = false
    })

    // 点击波形跳转
    wavesurfer.on('interaction', (newTime) => {
      currentTime.value = newTime
    })
  } catch (error) {
    console.error('Failed to initialize waveform:', error)
    isLoading.value = false
  }
}

// 播放/暂停控制
function togglePlayback() {
  if (!wavesurfer) return

  if (isPlaying.value) {
    wavesurfer.pause()
  } else {
    wavesurfer.play()
  }
}

// 跳转控制
function skipBackward() {
  if (!wavesurfer) return
  const newTime = Math.max(0, currentTime.value - 10)
  wavesurfer.setTime(newTime)
}

function skipForward() {
  if (!wavesurfer) return
  const newTime = Math.min(duration.value, currentTime.value + 10)
  wavesurfer.setTime(newTime)
}

// 缩放控制
function updateZoom(newZoom: number) {
  if (!wavesurfer) return
  zoomLevel.value = newZoom
  wavesurfer.zoom(newZoom)
}

// 格式化时间显示
function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
}

// 生命周期钩子
onMounted(async () => {
  // 确保DOM已经渲染完成
  await nextTick()
  console.log('After nextTick, waveformContainer.value:', waveformContainer.value)
  initWaveSurfer()
})

onBeforeUnmount(() => {
  if (wavesurfer) {
    wavesurfer.destroy()
    wavesurfer = null
  }
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 p-6">
    <div class="max-w-6xl mx-auto">
      <!-- 标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">音频波形测试</h1>
        <p class="text-slate-400">测试预生成的波形峰值数据渲染效果</p>
      </div>

      <!-- 音频信息卡片 -->
      <div class="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 mb-6 border border-slate-700/50">
        <h2 class="text-xl font-semibold text-white mb-4">音频信息</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-slate-400">文件名:</span>
            <p class="text-white mt-1 font-mono text-xs break-all">{{ testAudioFile }}</p>
          </div>
          <div>
            <span class="text-slate-400">总时长:</span>
            <p class="text-white mt-1">{{ formatTime(duration) }}</p>
          </div>
          <div>
            <span class="text-slate-400">当前时间:</span>
            <p class="text-white mt-1">{{ formatTime(currentTime) }}</p>
          </div>
        </div>
      </div>

      <!-- 波形容器 -->
      <div class="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-white">音频波形</h2>

          <!-- 缩放和播放控制器 -->
          <div class="flex items-center gap-4">
            <!-- 缩放控制 -->
            <div class="flex items-center gap-2 bg-slate-700/30 px-3 py-1 rounded-lg">
              <span class="text-xs text-slate-400 whitespace-nowrap">缩放:</span>
              <input
                type="range"
                :value="zoomLevel"
                @input="updateZoom(Number(($event.target as HTMLInputElement).value))"
                min="50"
                max="500"
                step="10"
                class="w-20 h-1 bg-slate-600 rounded-lg appearance-none cursor-pointer zoom-slider"
              />
              <span class="text-xs text-slate-400 min-w-[3rem] text-right">{{ zoomLevel }}</span>
            </div>

            <!-- 播放控制器 -->
            <div class="flex items-center gap-2">
              <button
                @click="skipBackward"
                :disabled="isLoading"
                class="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-600/70 transition-colors border border-slate-600/30 disabled:opacity-50 disabled:cursor-not-allowed text-white"
              >
                <SkipBack :size="18" />
              </button>

              <button
                @click="togglePlayback"
                :disabled="isLoading"
                class="p-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors border border-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed text-white"
              >
                <Play v-if="!isPlaying" :size="20" />
                <Pause v-else :size="20" />
              </button>

              <button
                @click="skipForward"
                :disabled="isLoading"
                class="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-600/70 transition-colors border border-slate-600/30 disabled:opacity-50 disabled:cursor-not-allowed text-white"
              >
                <SkipForward :size="18" />
              </button>
            </div>
          </div>
        </div>

        <!-- WaveSurfer 容器 - 始终渲染，但在加载时隐藏内容 -->
        <div class="relative">
          <!-- 加载状态覆盖层 -->
          <div
            v-if="isLoading"
            class="absolute inset-0 flex items-center justify-center bg-slate-800/80 rounded-lg z-10"
          >
            <div class="text-center">
              <div
                class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
              ></div>
              <p class="text-slate-400 mt-2">正在加载波形数据...</p>
            </div>
          </div>

          <!-- WaveSurfer 容器 -->
          <div
            ref="waveformContainer"
            class="waveform-container rounded-lg bg-slate-900/80 backdrop-blur-sm border border-slate-700/30"
            :class="{ 'opacity-50': isLoading }"
          ></div>

          <!-- 操作提示 -->
          <p class="text-xs text-slate-500 mt-2 text-center">
            点击波形可以跳转到指定位置 • 使用控制按钮播放/暂停/跳转
          </p>
        </div>
      </div>

      <!-- 技术信息 -->
      <div class="mt-6 bg-slate-800/30 backdrop-blur-sm rounded-xl p-4 border border-slate-700/30">
        <h3 class="text-lg font-semibold text-white mb-3">技术信息</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h4 class="text-slate-300 font-medium mb-2">波形生成</h4>
            <ul class="text-slate-400 space-y-1 text-xs">
              <li>• 使用 FFmpeg 提取音频数据</li>
              <li>• 每秒10个采样点进行峰值计算</li>
              <li>• RMS 值作为峰值指标</li>
              <li>• JSON 格式存储峰值数据</li>
            </ul>
          </div>
          <div>
            <h4 class="text-slate-300 font-medium mb-2">前端渲染</h4>
            <ul class="text-slate-400 space-y-1 text-xs">
              <li>• WaveSurfer.js v7.9.9</li>
              <li>• 预加载峰值数据，避免实时解码</li>
              <li>• 支持时间轴和交互式播放控制</li>
              <li>• 响应式设计，适配不同屏幕</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.waveform-container {
  min-height: 140px;
  box-shadow: inset 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

/* 自定义滚动条样式 - 放大版本 */
.waveform-container :deep(*)::-webkit-scrollbar {
  height: 12px; /* 增加高度 */
}

.waveform-container :deep(*)::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  margin: 0 4px; /* 增加边距 */
}

.waveform-container :deep(*)::-webkit-scrollbar-thumb {
  background: linear-gradient(
    to right,
    rgba(59, 130, 246, 0.8),
    rgba(37, 99, 235, 0.9)
  ); /* 蓝色渐变 */
  border-radius: 6px;
  border: 2px solid rgba(15, 23, 42, 0.5); /* 增加边框 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 添加阴影 */
  min-width: 40px; /* 最小宽度 */
}

.waveform-container :deep(*)::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to right, rgba(37, 99, 235, 0.9), rgba(29, 78, 216, 1));
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
  transform: scaleY(1.1); /* 悬停时稍微放大 */
  transition: all 0.2s ease;
}

.waveform-container :deep(*)::-webkit-scrollbar-thumb:active {
  background: linear-gradient(to right, rgba(29, 78, 216, 1), rgba(30, 64, 175, 1));
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

/* WaveSurfer 时间轴样式 */
.waveform-container :deep(.wavesurfer-timeline) {
  background: rgba(15, 23, 42, 0.5) !important;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

/* 缩放滑块样式 */
.zoom-slider {
  background: linear-gradient(to right, rgba(71, 85, 105, 0.8), rgba(71, 85, 105, 0.8));
}

.zoom-slider::-webkit-slider-thumb {
  appearance: none;
  height: 14px;
  width: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.zoom-slider::-webkit-slider-thumb:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.zoom-slider::-moz-range-thumb {
  height: 14px;
  width: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
