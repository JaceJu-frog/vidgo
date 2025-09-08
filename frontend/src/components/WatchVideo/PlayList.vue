<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CollectionAPI } from '@/composables/CollectionAPI'
import type { Video, Collection } from '@/types/media'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  currentVideoId: number
  currentVideoFilename?: string
}>()

// i18n functionality
const { t } = useI18n()

const router = useRouter()

const collection = ref<Collection | null>(null)
const collectionVideos = ref<Video[]>([])
const isLoading = ref(false)

import { BACKEND } from '@/composables/ConfigAPI'

// Load collection data when component mounts or currentVideoId changes
const loadCollectionData = async () => {
  if (!props.currentVideoId || props.currentVideoId === -1) {
    return
  }

  isLoading.value = true
  try {
    // First, get the collection that contains this video
    const videoCollection = await CollectionAPI.getVideoCollection(props.currentVideoId)

    if (videoCollection) {
      collection.value = videoCollection
      // Then get all videos in this collection
      const videos = await CollectionAPI.getCollectionVideos(videoCollection.id)
      // Sort videos by display name (not filename) with natural number sorting
      collectionVideos.value = videos.sort((a, b) => {
        // Use natural sorting that handles numbers correctly
        return a.name.localeCompare(b.name, undefined, {
          numeric: true,
          sensitivity: 'base',
        })
      })
    } else {
      // Video is not in any collection
      collection.value = null
      collectionVideos.value = []
    }
  } catch (error) {
    console.error('Failed to load collection data:', error)
    collection.value = null
    collectionVideos.value = []
  } finally {
    isLoading.value = false
  }
}

// Switch to a different video
const switchVideo = (video: Video): void => {
  if (video.id === props.currentVideoId) {
    return // Already viewing this video
  }

  // Navigate to the new video using the filename
  // Extract filename from video.url (assuming it's the last part)
  const filename = video.url.split('/').pop() || video.url
  router.push(`/watch/${encodeURIComponent(filename)}`)
}

// Get thumbnail URL for a video
const getThumbnailUrl = (video: Video): string => {
  if (!video.thumbnail) {
    return ''
  }

  // If it's already a full URL, return as is
  if (video.thumbnail.startsWith('http')) {
    return video.thumbnail
  }

  // If it starts with '/', it's a relative path from backend
  if (video.thumbnail.startsWith('/')) {
    return `${BACKEND}${video.thumbnail}`
  }

  // Otherwise, assume it's a relative path that needs '/media/' prefix
  return `${BACKEND}/media/${video.thumbnail}`
}

// Format video length display
const formatDuration = (length: string): string => {
  // If length is already in HH:MM:SS or MM:SS format, return as is
  if (length.includes(':')) {
    return length
  }
  // If it's in seconds, convert to MM:SS format
  const totalSeconds = parseInt(length, 10)
  if (isNaN(totalSeconds)) {
    return length
  }

  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }
}

// Check if a video is the currently playing video
const isCurrentVideo = (video: Video): boolean => {
  // Primary check: filename comparison (most reliable)
  if (props.currentVideoFilename) {
    const videoFilename = video.url.split('/').pop() || video.url
    const isCurrentByFilename = videoFilename === props.currentVideoFilename
    if (isCurrentByFilename) {
      return true
    }
  }

  // Secondary check: ID comparison (if available and valid)
  if (props.currentVideoId && video.id && props.currentVideoId !== -1) {
    return video.id === props.currentVideoId
  }

  return false
}

// Get the next video in the collection for autoplay
const getNextVideo = (): Video | null => {
  if (collectionVideos.value.length === 0) {
    return null
  }

  // Find current video index
  let currentIndex = -1

  // Try to find by filename first (most reliable)
  if (props.currentVideoFilename) {
    currentIndex = collectionVideos.value.findIndex((video) => {
      const videoFilename = video.url.split('/').pop() || video.url
      return videoFilename === props.currentVideoFilename
    })
  }

  // Fallback to ID comparison if filename search failed
  if (currentIndex === -1 && props.currentVideoId && props.currentVideoId !== -1) {
    currentIndex = collectionVideos.value.findIndex((video) => video.id === props.currentVideoId)
  }

  // If current video not found or is the last video, return null
  if (currentIndex === -1 || currentIndex >= collectionVideos.value.length - 1) {
    console.log('[PlayList] No next video available or current video not found in collection')
    return null
  }

  // Return next video
  const nextVideo = collectionVideos.value[currentIndex + 1]
  console.log(`[PlayList] Next video found: ${nextVideo.name} (index ${currentIndex + 1})`)
  return nextVideo
}

// Expose getNextVideo to parent component
defineExpose({
  getNextVideo,
})

// Watch for currentVideoId changes, but only reload if it's a different collection
watch(
  () => props.currentVideoId,
  async (newVideoId) => {
    if (!newVideoId || newVideoId === -1) return

    // If we already have videos loaded, check if the new video is in the same collection
    if (collectionVideos.value.length > 0) {
      const isInCurrentCollection = collectionVideos.value.some((video) => video.id === newVideoId)
      if (isInCurrentCollection) {
        // Video is in the same collection, no need to reload - just update highlighting
        console.log('Video is in same collection, skipping reload')
        return
      }
    }

    // New video is not in current collection, or we have no collection loaded yet
    console.log('Loading new collection for video ID:', newVideoId)
    await loadCollectionData()
  },
  { immediate: true },
)

// Watch for filename changes to ensure highlighting updates
watch(
  () => props.currentVideoFilename,
  () => {
    // Force reactivity update for highlighting
    // No need to reload collection data, just trigger re-render
  },
  { immediate: true },
)

onMounted(() => {
  loadCollectionData()
})
</script>
<template>
  <!-- 合集/播放列表 -->
  <div class="bg-slate-800/30 rounded-2xl p-6 backdrop-blur-lg border border-slate-600/30">
    <h2 class="text-xl font-semibold text-white mb-6">
      {{ collection ? collection.name : t('collectionPlaylist') }}
    </h2>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-8">
      <div
        class="animate-spin w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full mr-3"
      ></div>
      <span class="text-slate-400">{{ t('loadingCollection') }}</span>
    </div>

    <!-- No Collection State -->
    <div v-else-if="!collection || collectionVideos.length === 0" class="text-center py-8">
      <div class="text-slate-400 mb-2">
        <svg
          class="w-12 h-12 mx-auto mb-3 opacity-50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          ></path>
        </svg>
        <p class="text-sm">该视频不属于任何合集</p>
      </div>
    </div>

    <!-- Collection Videos List -->
    <div v-else class="space-y-3 max-h-96 overflow-y-auto custom-scrollbar">
      <el-tooltip
        v-for="video in collectionVideos"
        :key="video.id"
        :content="video.name"
        placement="left"
        :show-after="500"
      >
        <div
          @click="switchVideo(video)"
          class="flex items-center p-4 rounded-xl cursor-pointer hover:bg-slate-700/30 transition-all duration-200 border-l-4"
          :class="{
            'bg-blue-900/30 border-blue-500 shadow-lg': isCurrentVideo(video),
            'border-slate-600/30 hover:border-slate-500/50': !isCurrentVideo(video),
          }"
        >
          <!-- Thumbnail -->
          <div
            class="w-20 h-12 bg-slate-700/50 rounded-lg mr-4 flex-shrink-0 border border-slate-600/30 overflow-hidden relative"
          >
            <img
              v-if="getThumbnailUrl(video)"
              :src="getThumbnailUrl(video)"
              :alt="video.name"
              class="w-full h-full object-cover"
              @error="
                (e) => {
                  const target = e.target as HTMLImageElement
                  if (target) {
                    target.style.display = 'none'
                    // Show fallback icon when image fails
                    const fallback = target.nextElementSibling as HTMLElement
                    if (fallback) fallback.style.display = 'flex'
                  }
                }
              "
            />
            <!-- Fallback icon when no thumbnail or thumbnail fails to load -->
            <div
              class="w-full h-full absolute top-0 left-0 flex items-center justify-center text-slate-400 text-lg"
              :style="{ display: getThumbnailUrl(video) ? 'none' : 'flex' }"
            >
              🎬
            </div>
          </div>

          <!-- Video Info -->
          <div class="flex-1 min-w-0">
            <p class="font-medium text-sm text-white truncate mb-1">{{ video.name }}</p>
            <p class="text-xs text-slate-400">{{ formatDuration(video.length) }}</p>
          </div>

          <!-- Current Video Indicator -->
          <div v-if="isCurrentVideo(video)" class="flex-shrink-0 ml-3">
            <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      </el-tooltip>
    </div>
  </div>
</template>

<style scoped>
/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(71, 85, 105, 0.3);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.5);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.8);
}
</style>
