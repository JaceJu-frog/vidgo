<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { isProxy, toRaw, markRaw } from 'vue'
import { View, Hide } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
import { ElMessage } from 'element-plus'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js'
import { normalizePeaks } from '@/composables/peaks'
import type { Subtitle } from '@/types/subtitle'
import type { WaveformPeakData } from '@/composables/AudioWaveformAPI'
import { useWaveformPeaks } from '@/composables/AudioWaveformAPI'

const regions = RegionsPlugin.create()
const timeline = TimelinePlugin.create({
  height: 28,
  timeInterval: 0.2,
  primaryLabelInterval: 5,
  secondaryLabelInterval: 1,
  insertPosition: 'beforebegin', // This positions the timeline above the waveform
  style: {
    fontSize: '12px',
    color: '#e2e8f0', // Lighter color for better visibility
    fontWeight: '500',
  },
})

// Props 是从父元素传进来的子元素只读变量，变通的方式是通过emit提交修改信号,在父元素中修改。
const props = withDefaults(
  defineProps<{
    audioUrl?: string | null // 改为可选，因为现在只使用 waveform peaks 数据
    videoId?: number // Video ID for waveform peak generation
    videoUrl?: string // Video URL for fileName extraction
    blobUrls?: (string | undefined)[] // [ zhUrl?, bothUrl?, enUrl? ] And can be null.
    subtitles?: Subtitle[] // Subtitle data for regions
    currentTime?: number
    duration?: number
    showRegions?: boolean
    isLoading?: boolean
    loadingMessage?: string
    waveformPeaks?: WaveformPeakData | null
    height?: number // Height of the waveform viewer
  }>(),
  {
    // default values
    audioUrl: null,
    subtitles: () => [],
    currentTime: 0,
    duration: 30,
    showRegions: true,
    isLoading: false,
    loadingMessage: 'Loading audio...',
    waveformPeaks: null,
    height: 200,
  },
)
const zoom = ref(50) // 降低初始缩放，减少初始画布宽度

const emit = defineEmits<{
  (e: 'update:zoom', v: number): void
  (e: 'update:showRegions', v: boolean): void
  (e: 'seek', t: number): void
  (e: 'subtitle-updated', index: number, newStart: number, newEnd: number): void
}>()

const waveformContainer = ref<HTMLDivElement>()
let ws: WaveSurfer | null = null

let waveformPeaksComposable: ReturnType<typeof useWaveformPeaks> | null = null

// Debouncing for region updates to prevent text duplication
let regionUpdateTimeout: ReturnType<typeof setTimeout> | null = null

// Flag to prevent cascade updates when we're updating from drag
let isUpdatingFromDrag = false

// Validation function to check subtitle overlaps
function validateSubtitleTiming(index: number, newStart: number, newEnd: number): boolean {
  if (!props.subtitles || props.subtitles.length === 0) return true

  // Check if start time is after end time
  if (newStart >= newEnd) {
    return false
  }

  // Check overlap with previous subtitle
  if (index > 0) {
    const prevSubtitle = props.subtitles[index - 1]
    if (newStart < prevSubtitle.end) {
      return false
    }
  }

  // Check overlap with next subtitle
  if (index < props.subtitles.length - 1) {
    const nextSubtitle = props.subtitles[index + 1]
    if (newEnd > nextSubtitle.start) {
      return false
    }
  }

  return true
}

function redrawRegions(subs: Subtitle[]) {
  if (!ws || !props.showRegions) return

  // Clear ALL existing regions (including default ones)
  regions.clearRegions()

  // Add new regions only if we have real subtitles
  if (subs && subs.length > 0) {
    subs.forEach((s, i) => {
      regions.addRegion({
        id: `sub-${i}`,
        start: s.start,
        end: s.end,
        content: s.text,
        color: 'rgba(56, 189, 248, 0.25)', // Modern glass blue with transparency
        drag: true,
        resize: true,
      })
    })
  }
}

function toggleRegionsVisibility() {
  if (!ws) return

  if (props.showRegions) {
    // Show regions - only use actual subtitles, no defaults
    regions.clearRegions()
    if (props.subtitles && props.subtitles.length > 0) {
      props.subtitles.forEach((s, i) => {
        regions.addRegion({
          id: `sub-${i}`,
          start: s.start,
          end: s.end,
          content: s.text,
          color: 'rgba(56, 189, 248, 0.25)', // Modern glass blue with transparency
          drag: true,
          resize: true,
        })
      })
    }
  } else {
    // Hide regions - clear all
    regions.clearRegions()
  }
}

watch(
  () => props.showRegions,
  () => toggleRegionsVisibility(),
  { immediate: true },
)

// Watch for subtitle changes and update regions
watch(
  () => props.subtitles,
  (newSubs) => {
    // Skip redraw if we're updating from a drag operation to prevent cascade
    if (isUpdatingFromDrag) {
      return
    }
    
    if (newSubs && newSubs.length > 0) {
      // Add a small delay to ensure proper cleanup of previous regions
      nextTick(() => {
        redrawRegions(newSubs)
      })
    }
  },
  { immediate: true, deep: true },
)

function initWaveSurfer() {
  if (ws) ws.destroy()

  if (waveformPeaksComposable?.isLoading.value) return

  const peaksData = waveformPeaksComposable?.waveformPeaks.value || props.waveformPeaks

  const raw = peaksData?.peaks
  const peaksArray = normalizePeaks(raw) // -> number[]
  const safePeaks = markRaw(peaksArray) // 避免再次被代理
  console.log(safePeaks)
  const dur = Number(peaksData?.duration ?? props.duration ?? 0)
  if (!dur || !Number.isFinite(dur)) {
    console.warn('Invalid duration:', peaksData?.duration, props.duration)
    return
  }

  if (!waveformContainer.value) {
    console.error('waveformContainer not available')
    return
  }

  ws = WaveSurfer.create({
    container: waveformContainer.value!,
    height: props.height,
    waveColor: '#38bdf8', // Modern cyan-blue
    progressColor: '#0ea5e9', // Darker cyan for progress
    cursorColor: '#f59e0b', // Modern amber cursor for better visibility
    barWidth: 2,
    barGap: 1,
    barRadius: 1,
    normalize: true,
    mediaControls: false,
    minPxPerSec: zoom.value, // Use zoom value for waveform scaling
    peaks: [safePeaks], // ✅ 保持用规范化后的 peaks
    duration: dur, // ✅ 用规范化后的时长
    fillParent: false, // ✅ 允许内容宽度 = duration * minPxPerSec（可超出容器）
    hideScrollbar: false, // ✅ 显示内部横向滚动条
    autoCenter: true, // ✅ 播放时不要强制把光标居中
    autoScroll: true, // ✅ 播放时不要自动跟随滚动
  })

  // 5) 用 ready（不是 decode）添加/启用 Regions
  ws.on('ready', () => {
    // Add timeline plugin
    ws!.registerPlugin(timeline)
    // Add regions plugin
    ws!.registerPlugin(regions)

    // Add subtitle regions if showRegions is true and we have real subtitles
    if (props.showRegions && props.subtitles && props.subtitles.length > 0) {
      props.subtitles.forEach((s, i) => {
        regions.addRegion({
          id: `sub-${i}`,
          start: s.start,
          end: s.end,
          content: s.text,
          color: 'rgba(56, 189, 248, 0.25)', // Modern glass blue with transparency
          drag: true,
          resize: true,
        })
      })
    }

    // Enable drag selection for creating new regions
    regions.enableDragSelection({
      color: 'rgba(96, 165, 250, 0.3)', // Lighter blue for drag selection
      resize: true,
      drag: true,
    })

    // Add region event listeners
    regions.on('region-created', (region) => {
      console.log('Region created:', region)
    })

    regions.on('region-updated', (region) => {
      console.log('Region updated:', region)

      // Clear any pending update timeout
      if (regionUpdateTimeout) {
        clearTimeout(regionUpdateTimeout)
      }

      // Extract subtitle index from region ID
      const regionId = region.id
      if (!regionId || !regionId.startsWith('sub-')) return

      const subtitleIndex = parseInt(regionId.replace('sub-', ''))
      if (isNaN(subtitleIndex)) return

      // Set flag to prevent cascade updates
      isUpdatingFromDrag = true

      // Debounce the update to prevent rapid firing during drag
      regionUpdateTimeout = setTimeout(() => {
        // Validate the new timing
        const isValid = validateSubtitleTiming(subtitleIndex, region.start, region.end)

        if (!isValid) {
          // Show error message
          ElMessage.error('Unallowed dragging of overlayed subtitles')

          // Revert the region to original position by recreating it
          if (props.subtitles && props.subtitles[subtitleIndex]) {
            const originalSubtitle = props.subtitles[subtitleIndex]

            // Remove the current region
            region.remove()

            // Add a new region with the original timing
            regions.addRegion({
              id: `sub-${subtitleIndex}`,
              start: originalSubtitle.start,
              end: originalSubtitle.end,
              content: originalSubtitle.text,
              color: 'rgba(56, 189, 248, 0.25)',
              drag: true,
              resize: true,
            })
          }
          // Reset flag
          isUpdatingFromDrag = false
          return
        }

        // If validation passes, emit the update event
        emit('subtitle-updated', subtitleIndex, region.start, region.end)
        
        // Reset flag after a short delay to allow parent to update
        setTimeout(() => {
          isUpdatingFromDrag = false
        }, 100)
        
        regionUpdateTimeout = null
      }, 200) // 200ms debounce
    })

    regions.on('region-clicked', (region) => {
      console.log('Region clicked:', region)
      // Seek to region start when clicked
      emit('seek', region.start)
    })

    // 设置初始缩放 - 只有在 ready 之后才能调用 zoom
    ws!.zoom(zoom.value)
  })

  ws.on('interaction', (t) => emit('seek', t))
}

watch(
  () => zoom.value,
  (newZoom) => {
    if (ws) {
      ws.zoom(newZoom)
    }
    emit('update:zoom', newZoom)
  },
)

// Watch for height changes and reinitialize waveform with debouncing
let heightWatchTimeout: ReturnType<typeof setTimeout> | null = null
watch(
  () => props.height,
  (newHeight) => {
    if (!ws) return

    // Clear any pending timeout
    if (heightWatchTimeout) {
      clearTimeout(heightWatchTimeout)
    }

    // Debounce reinitializations to prevent rapid redraws
    heightWatchTimeout = setTimeout(() => {
      console.log('Reinitializing waveform with height:', newHeight)
      initWaveSurfer()
      heightWatchTimeout = null
    }, 100) // 100ms debounce
  },
)

// 光标时间同步：只更新播放光标位置，不强制滚动视图
watch(
  () => props.currentTime,
  (t) => {
    if (!ws || props.duration === 0) return
    const pct = t / props.duration
    if (Math.abs(ws.getCurrentTime() - t) > 0.05) ws.seekTo(pct)
  },
)

onMounted(async () => {
  // Initialize waveform peaks composable if videoId and videoUrl are provided
  if (props.videoId && props.videoUrl) {
    waveformPeaksComposable = useWaveformPeaks(props.videoId, props.videoUrl)
    await waveformPeaksComposable.initialize()
  }
  await nextTick()
  // console.log('After nextTick, waveformContainer.value:', waveformContainer.value)
  initWaveSurfer()
})

onBeforeUnmount(() => {
  ws?.destroy()
  // Clear any pending timeouts
  if (heightWatchTimeout) {
    clearTimeout(heightWatchTimeout)
    heightWatchTimeout = null
  }
  if (regionUpdateTimeout) {
    clearTimeout(regionUpdateTimeout)
    regionUpdateTimeout = null
  }
  // Cleanup composable
  if (waveformPeaksComposable) {
    waveformPeaksComposable.cleanup()
  }
})
</script>

<template>
  <div class="flex flex-col gap-4 h-full">
    <!-- Header with controls -->
    <div class="flex flex-col gap-3 mb-3">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white">{{ t('audioWaveform') }}</h3>
        <!-- 右侧工具条 -->
        <div class="flex items-center gap-3">
          <!-- 缩放控件，宽度缩小 50% -->
          <div
            class="flex items-center gap-3 bg-slate-700/30 px-4 py-2 rounded-lg border border-slate-600/30"
            style="width: 50%; min-width: 200px"
          >
            <span class="text-xs text-slate-400 font-medium flex-shrink-0">{{ t('zoom') }}:</span>
            <el-slider class="flex-1 min-w-0" v-model="zoom" :min="10" :max="500" size="small" />
            <span class="text-xs text-slate-400 min-w-[3rem] text-right flex-shrink-0">
              {{ zoom }}
            </span>
          </div>

          <!-- View Icon 按钮 -->
          <el-tooltip
            :content="props.showRegions ? t('hideRegions') : t('showRegions')"
            placement="top"
          >
            <button
              @click="emit('update:showRegions', !props.showRegions)"
              class="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-600/70 transition-colors border border-slate-600/30"
              :class="props.showRegions ? 'text-blue-400' : 'text-slate-400'"
            >
              <el-icon size="16">
                <component :is="props.showRegions ? View : Hide" />
              </el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- Waveform container -->
    <div
      v-if="waveformPeaksComposable?.isLoading.value"
      class="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur-sm z-10 min-w-0"
    >
      <div class="text-center">
        <div
          class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-3"
        ></div>
        <p class="text-slate-400 text-sm">
          {{ waveformPeaksComposable?.loadingMessage.value || 'Loading waveform data...' }}
        </p>
      </div>
    </div>

    <div
      v-else-if="!waveformPeaksComposable && props.waveformPeaks?.peaks.length === 0"
      class="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10"
    >
      <div class="text-center">
        <p class="text-slate-400 text-sm">No waveform data available</p>
      </div>
    </div>

    <div
      id="waveform"
      ref="waveformContainer"
      class="waveform-container scrollbar-hidden rounded-lg bg-slate-900/80 backdrop-blur-sm border border-slate-700/30 flex-1 min-h-0"
      :class="{
        'opacity-50': waveformPeaksComposable?.isLoading.value,
      }"
    ></div>
  </div>
</template>

<style scoped>
/* WaveSurfer 时间轴样式 */
.waveform-container :deep(.wavesurfer-timeline) {
  background: rgba(15, 23, 42, 0.8) !important;
  border-bottom: 2px solid rgba(226, 232, 240, 0.4) !important;
  backdrop-filter: blur(4px);
}

/* Timeline tick marks - make them thicker and more visible */
.waveform-container :deep(.wavesurfer-timeline canvas) {
  opacity: 0.9 !important;
}

/* Timeline labels styling */
.waveform-container :deep(.wavesurfer-timeline .timeline-label) {
  color: #e2e8f0 !important;
  font-weight: 500 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

/* Timeline tick lines - make them more prominent */
.waveform-container :deep(.wavesurfer-timeline::after) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(226, 232, 240, 0.1) 20%,
    rgba(226, 232, 240, 0.2) 50%,
    rgba(226, 232, 240, 0.1) 80%,
    transparent 100%
  );
  pointer-events: none;
}

/* Make timeline canvas strokes thicker */
.waveform-container :deep(.wavesurfer-timeline) {
  --timeline-primary-color: rgba(226, 232, 240, 0.8);
  --timeline-secondary-color: rgba(148, 163, 184, 0.6);
}

/* Timeline container enhancement */
.waveform-container :deep(.wavesurfer-timeline) {
  border-top: 1px solid rgba(226, 232, 240, 0.2) !important;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(226, 232, 240, 0.05) !important;
}

/* 时间轴样式 */
/* :deep(.wavesurfer-timeline) {
  background: rgba(15, 23, 42, 0.5) !important;
} */

/* Region text 样式，positioning - force text to start from top */
.waveform-container :deep(.wavesurfer-region) {
  display: flex !important;
  align-items: flex-start !important;
  padding-top: 2px !important;
}

/* Prevent text duplication in regions */
.waveform-container :deep(.wavesurfer-region::before),
.waveform-container :deep(.wavesurfer-region::after) {
  display: none !important;
}

/* Ensure clean text rendering */
.waveform-container :deep(.wavesurfer-region) {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

:global(.waveform-container) wave-region::part(region-content) {
  top: 2px;
  left: 4px;
  right: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #f3f4f6; /* 文字颜色 */
  text-shadow:
    0 1px 3px rgba(0, 0, 0, 0.7),
    0 0 8px rgba(14, 165, 233, 0.4);
  /*pointer-events: none;*/ /*这里导致了ScrollBar拖动无效*/
  backdrop-filter: blur(1px);
}

/* Element Plus 滑块样式定制 */
:deep(.el-slider__runway) {
  background-color: rgba(51, 65, 85, 0.6) !important; /* slate-700 */
  border-radius: 4px !important;
  height: 4px !important;
}

:deep(.el-slider__bar) {
  background-color: #3b82f6 !important; /* blue-500 */
  border-radius: 4px !important;
}

:deep(.el-slider__button) {
  background-color: #3b82f6 !important; /* blue-500 */
  border: 2px solid rgba(59, 130, 246, 0.3) !important;
  width: 14px !important;
  height: 14px !important;
}

:deep(.el-slider__button:hover) {
  background-color: #2563eb !important; /* blue-600 */
  border-color: rgba(37, 99, 235, 0.5) !important;
  transform: scale(1.1) !important;
}

:deep(#waveform ::part(region)) {
  top: 15%; /* push down from the top */
  height: 80%; /* region overlay height */
}

/* 滚动条样式定制 Chromium */
#waveform ::part(scroll)::-webkit-scrollbar {
  height: 8px;
}
#waveform ::part(scroll)::-webkit-scrollbar-track {
  background: rgba(2, 6, 23, 0.2);
}
#waveform ::part(scroll)::-webkit-scrollbar-thumb {
  border-radius: 9999px;
  background: rgba(148, 163, 184, 0.6);
}

/* Firefox */
#waveform ::part(scroll) {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}

:deep(#waveform ::part(scroll))::-webkit-scrollbar {
  height: 800px !important;
}
:deep(#waveform ::part(scroll)) {
  scrollbar-width: thin;
  scrollbar-color: green transparent;
}
</style>
