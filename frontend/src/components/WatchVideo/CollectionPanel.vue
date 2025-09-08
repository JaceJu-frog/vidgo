<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { CollectionAPI } from '@/composables/CollectionAPI'
import type { Video, Collection } from '@/types/media'

const props = defineProps<{
  currentVideoId: number
  currentVideoFilename: string
}>()

const collection = ref<Collection | null>(null)
const videos = ref<Video[]>([])
const loading = ref(true)

async function loadCollection() {
  if (!props.currentVideoId) return
  
  loading.value = true
  try {
    // Get the collection that contains the current video
    const videoCollection = await CollectionAPI.getVideoCollection(props.currentVideoId)
    
    if (videoCollection) {
      collection.value = videoCollection
      // Load all videos in this collection
      const collectionVideos = await CollectionAPI.getCollectionVideos(videoCollection.id)
      videos.value = collectionVideos
    } else {
      // Video is not in any collection
      collection.value = null
      videos.value = []
    }
  } catch (error) {
    console.error('Error loading collection:', error)
    collection.value = null
    videos.value = []
  } finally {
    loading.value = false
  }
}

function getVideoFilename(video: Video): string {
  // Extract filename from URL (assuming URL pattern like "/media/video/filename.mp4")
  const urlParts = video.url.split('/')
  return urlParts[urlParts.length - 1]
}

function formatDuration(duration: string): string {
  // Duration might be in various formats, handle gracefully
  if (!duration) return '00:00'
  return duration
}

onMounted(() => {
  loadCollection()
})

// Reload collection when current video changes
watch(() => props.currentVideoId, () => {
  if (props.currentVideoId) {
    loadCollection()
  }
})
</script>

<template>
  <div class="collection-panel">
    <!-- Loading State -->
    <div v-if="loading" class="text-slate-400 text-center py-8">
      <i class="loading-icon animate-spin"></i>
      加载集合中...
    </div>
    
    <!-- No Collection State -->
    <div v-else-if="!collection" class="text-slate-400 text-center py-8">
      <div class="text-sm">此视频不属于任何集合</div>
    </div>
    
    <!-- Collection Content -->
    <div v-else class="p-4">
      <!-- Collection Header -->
      <div class="mb-4">
        <h3 class="text-white font-semibold text-lg mb-1">{{ collection.name }}</h3>
        <div class="text-slate-400 text-sm">{{ videos.length }} 个视频</div>
      </div>
      
      <!-- Videos List -->
      <div class="space-y-2 max-h-96 overflow-y-auto">
        <router-link
          v-for="video in videos"
          :key="video.id"
          :to="`/watch/${getVideoFilename(video)}`"
          :class="[
            'flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-all duration-200 block',
            video.id === currentVideoId
              ? 'bg-blue-600/20 border-blue-500/50 ring-1 ring-blue-500/30'
              : 'bg-slate-700/30 border-slate-600/30 hover:bg-slate-600/40 hover:border-slate-500/50'
          ]"
        >
          <!-- Thumbnail -->
          <div class="flex-shrink-0">
            <img
              :src="video.thumbnail"
              :alt="video.name"
              class="w-16 h-12 object-cover rounded-md bg-slate-600"
              loading="lazy"
              @error="(e) => { const target = e.target as HTMLImageElement; if (target) target.style.display = 'none' }"
            />
            <!-- Fallback placeholder if image fails -->
            <div 
              v-if="!video.thumbnail" 
              class="w-16 h-12 bg-slate-600 rounded-md flex items-center justify-center"
            >
              <i class="text-slate-400 text-xs">📹</i>
            </div>
          </div>
          
          <!-- Video Info -->
          <div class="flex-1 min-w-0">
            <h4 
              :class="[
                'font-medium text-sm leading-tight mb-1 line-clamp-2',
                video.id === currentVideoId ? 'text-blue-200' : 'text-white'
              ]"
              :title="video.name"
            >
              {{ video.name }}
            </h4>
            
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span>{{ formatDuration(video.length) }}</span>
              <span v-if="video.id === currentVideoId" class="text-blue-400 font-medium">
                正在播放
              </span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-icon::before {
  content: "⟳";
  font-size: 1.2em;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Custom scrollbar for the videos list */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(71, 85, 105, 0.3);
  border-radius: 2px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.5);
  border-radius: 2px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.7);
}
</style>