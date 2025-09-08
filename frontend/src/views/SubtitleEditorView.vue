<template>
  <!-- 深色主题背景容器,min-h-screen:这个元素的最小高度等于整个视口的高度。 -->
  <div class="min-h-screen bg-[#1B316A]">
    <!-- Header -->
    <NavBar
      :showTranslation="showTranslation"
      :progress="videoProgress"
      :currentTime="currentTime"
      :videoLength="videoData.videoLength"
      :title="videoData.name"
      :filename="fileName"
      @toggle-translation="showTranslation = !showTranslation"
      @go-back="console.log('come back')"
      @open-settings="showSettingsDialog = true"
    />
    <div class="h-[calc(100vh+70px)] flex gap-6 p-6 min-w-0">
      <!-- 左侧视频和波形区域 -->
      <div class="flex-[2] flex flex-col min-h-0 gap-6 min-w-0">
        <!-- Video Player -->
        <div
          class="flex-[2] flex flex-col min-h-0 bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-lg rounded-2xl p-4 border border-slate-600/50 shadow-2xl min-w-0"
        >
          <!-- Use a fill container instead of aspect-video so it can stretch -->
          <div class="relative w-full h-full overflow-hidden">
            <VideoPlayer
              ref="playerRef"
              :src="videoSrc"
              :blobUrls="blobUrls"
              :videoId="videoData.id"
              @time-update="handleTimeUpdate"
              class="absolute inset-0 w-full h-full"
            />
          </div>
        </div>

        <!-- Waveform Viewer -->
        <div
          ref="waveformContainerRef"
          class="flex-[1] p-4 border border-slate-600/50 bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-lg rounded-2xl shadow-2xl min-w-0"
        >
          <WaveformViewer
            v-if="waveformReady"
            :subtitles="subtitles"
            :video-id="videoData.id"
            :video-url="videoSrc"
            :blobUrls="blobUrls"
            :current-time="currentTime"
            :duration="duration"
            :show-regions="showRegions"
            :height="waveformHeight"
            @seek="handleSeekFromWaveform"
            @update:show-regions="showRegions = $event"
            @subtitle-updated="handleSubtitleUpdated"
          />
        </div>
      </div>

      <!-- 右侧字幕编辑器 - 占满右侧 -->
      <div class="flex-[1] h-full min-h-0">
        <div
          class="bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-lg rounded-2xl border border-slate-600/50 shadow-2xl h-full min-h-0 min-w-0"
        >
          <SubtitleEditor
            ref="subtitleEditorRef"
            :current-time="currentTime"
            :id="videoData.id"
            :rawLang="videoData.rawLang"
            :videoName="videoData.name"
            :duration="duration"
            @seek-time="handleSeekFromSubs"
            @update-bloburls="updateBloburl"
            @subs-loaded="subsLoad"
            class="w-full h-full"
          />
        </div>
      </div>
    </div>
    <!-- Settings Dialog -->
    <SettingsDialog v-model:visible="showSettingsDialog" @close="showSettingsDialog = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import type { Subtitle } from '@/types/subtitle'
import { ElMessage } from 'element-plus'
import { blobUrls } from '@/composables/Buildvtt'
import type { VideoInfoData } from '@/types/media.d.ts'
import { getVideoInfo } from '@/composables/GetVideoInfo'
import { hhmmssToSeconds } from '@/composables/TimeFunc'
import { useRoute, useRouter } from 'vue-router'

import NavBar from '@/components/WatchVideo/NavBar.vue'
import VideoPlayer from '@/components/WatchVideo/VideoPlayer.vue'
import SubtitleEditor from '@/components/Editor/SubtitleEditor.vue'
import WaveformViewer from '@/components/Editor/WaveformViewer.vue'
import SettingsDialog from '@/components/dialogs/SettingsDialog.vue'

const subtitles = ref<Subtitle[]>([]) // 存真正的字幕数组
const waveformContainerRef = ref<HTMLDivElement>()
const waveformHeight = ref(200) // Default height
let waveformResizeObserver: ResizeObserver | null = null

function subsLoad(raw: Subtitle[]) {
  // 注意 raw 是数组
  console.log('subtitles accepted by editor:', raw)
  subtitles.value = raw
}

const defaultVideoInfo: VideoInfoData = {
  id: -1,
  name: '（未命名视频）',
  url: '',
  description: '暂无描述',
  thumbnailUrl: '',
  videoLength: '00:00',
  lastModified: '',
}

const playerRef = ref<InstanceType<typeof VideoPlayer> | null>(null) // ← ①
const subtitleEditorRef = ref<InstanceType<typeof SubtitleEditor> | null>(null)

// Router setup
const route = useRoute()

// Get route params and fix basename dot issue like WatchVideo.vue
const routeParams = route.params
const basenameRaw = (routeParams.basename || routeParams['basename.']) as string
const ext = routeParams.ext as string

// Remove trailing dot and create filename
const basename = basenameRaw?.replace(/\.$/, '') || ''
const fileName = ref(`${basename}.${ext?.toLowerCase() || ''}`)

const isAudio = /^(m4a|mp3|wav)$/.test(ext?.toLowerCase() || '')

// ───────────────── state ─────────────────
const showTranslation = ref(false)

function updateBloburl(blobUrlsAccepted: Array<string | undefined>) {
  blobUrls.value = [...blobUrlsAccepted]
  console.log(blobUrls)
}

function handleSeekFromWaveform(t: number) {
  // 点击对应位置的字幕,视频自动跳转到对应时间.
  currentTime.value = t
  console.log(currentTime.value)
  playerRef.value?.seek(t) // ← ② jump the player
}

const videoProgress = computed(() => (duration.value ? currentTime.value / duration.value : 0))
// 随时间变化改变"current-Time"等参数，从而影响Subtitle Editor 和wave surfer region的高亮。
function handleTimeUpdate(t: number) {
  currentTime.value = t
  console.log('currentTime', currentTime)
  console.log(videoProgress.value)
}
// No longer need props since we get route params directly

const videoData = ref<VideoInfoData>(defaultVideoInfo)

const showSettingsDialog = ref(false)
const showRegions = ref(true) // Control waveform regions visibility
const videoId = ref(-1)
const subtitleFont = ref('Arial')
const subtitleColor = ref('#6a9749')
const subtitleSize = ref(18)

const currentTime = ref(0)
function handleSeekFromSubs(t: number) {
  // 点击对应位置的字幕,视频自动跳转到对应时间.
  currentTime.value = t
  playerRef.value?.seek(t) // ← ② jump the player
}

function handleSubtitleUpdated(index: number, newStart: number, newEnd: number) {
  // Update the subtitle data when dragged in waveform
  if (subtitles.value[index]) {
    subtitles.value[index].start = newStart
    subtitles.value[index].end = newEnd

    // Force reactivity update
    subtitles.value = [...subtitles.value]

    // Also update the subtitle editor's internal data
    if (subtitleEditorRef.value && 'updateSubtitleTiming' in subtitleEditorRef.value) {
      ;(subtitleEditorRef.value as any).updateSubtitleTiming(index, newStart, newEnd)
    }

    console.log(`Subtitle ${index} updated: ${newStart}s - ${newEnd}s`)
  }
}

const duration = ref(0)
const progressPercentage = computed(() => {
  if (duration.value <= 0) return 0
  return (currentTime.value / duration.value) * 100
})

import { BACKEND } from '@/composables/ConfigAPI'
const videoSrc = computed(() => {
  const mediaType = isAudio ? 'audio' : 'video'
  const src = `${BACKEND}/media/${mediaType}/${fileName.value}`
  console.log('videoSrc updated:', src)
  return src
})

// Function to load video data like WatchVideo.vue
async function loadVideoData(filename: string) {
  try {
    console.log('Loading video data for:', filename)
    const data = await getVideoInfo(filename)

    // Ensure description is never null
    videoData.value = {
      ...data,
      description: data.description || '暂无描述',
    }

    // console.log('Video data loaded:', videoData.value)
    // console.log('Video rawLang:', videoData.value.rawLang)

    duration.value = hhmmssToSeconds(videoData.value.videoLength)
    videoId.value = videoData.value.id

    // Update browser tab title - check if name is not the default
    if (videoData.value.name && videoData.value.name !== '（未命名视频）') {
      document.title = `${videoData.value.name} - VidGo 字幕编辑器`
      console.log('Browser title updated to:', document.title)
    } else {
      console.warn('Video name is empty or default, not updating title')
      // Fallback to filename without extension
      const nameFromFile = filename.replace(/\.[^/.]+$/, '')
      document.title = `${nameFromFile} - VidGo 字幕编辑器`
    }
  } catch (error) {
    console.error('Failed to load video info:', error)
    // Set default video data
    videoData.value = { ...defaultVideoInfo }
    // Fallback to filename without extension
    const nameFromFile = filename.replace(/\.[^/.]+$/, '')
    document.title = `${nameFromFile} - VidGo 字幕编辑器`
    ElMessage.error('加载视频信息失败')
  }
}

// Watch for route params changes to reload video data
const waveformReady = ref(false)
onMounted(async () => {
  // console.log('Route params:', routeParams)
  // console.log('basename:', basename)
  // console.log('ext:', ext)
  // console.log('fileName:', fileName)
  // console.log('Current path:', route.path)
  await loadVideoData(fileName.value)
  waveformReady.value = true // 再让子组件挂载
  // Load saved preferences
  try {
    const savedFont = localStorage.getItem('subtitleFont')
    const savedColor = localStorage.getItem('subtitleColor')
    const savedSize = localStorage.getItem('subtitleSize')
    if (savedFont) subtitleFont.value = savedFont
    if (savedColor) subtitleColor.value = savedColor
    if (savedSize) subtitleSize.value = parseInt(savedSize, 10)
  } catch (e) {
    console.error('Failed to load subtitle preferences:', e)
  }

  // Setup waveform container ResizeObserver
  if (waveformContainerRef.value) {
    waveformResizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { height } = entry.contentRect
        // Calculate waveform height with padding adjustment
        const newHeight = Math.max(150, height - 80) // More conservative padding to account for header and margins
        // Only update if the change is significant to prevent feedback loops
        if (Math.abs(newHeight - waveformHeight.value) > 10) {
          console.log('Updating waveform height from', waveformHeight.value, 'to', newHeight)
          waveformHeight.value = newHeight
        }
      }
    })
    waveformResizeObserver.observe(waveformContainerRef.value)
  }
})

onBeforeUnmount(() => {
  if (waveformResizeObserver) {
    waveformResizeObserver.disconnect()
    waveformResizeObserver = null
  }
})
</script>
