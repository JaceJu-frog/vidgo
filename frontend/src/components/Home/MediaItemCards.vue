<!-- src/components/VideoCards.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import VideoCard from '@/components/Home/VideoCard.vue'
import CollectionCard from '@/components/Home/CollectionCard.vue'
import type { MediaItem, Video, Collection } from '@/types/media'

function toggle(id: number, checked: boolean) {
  const set = new Set(props.selectedIds)
  checked ? set.add(id) : set.delete(id)
  emit('update:selectedIds', [...set])
}

function handleCollectionMoved(collection: Collection) {
  emit('collection-moved', collection)
}

const props = defineProps<{
  category: { id: number | null; name: string; items: MediaItem[] }
  view: 'grid' | 'list'
  batchMode?: boolean
  selectedIds?: number[]
}>()

const emit = defineEmits<{
  (e: 'generate-subtitle', video: Video): void
  (e: 'delete', video: Video): void
  (e: 'thumbnail-updated', video: Video): void
  (e: 'category-moved', p: { videoId: number; categoryId: number | null }): void
  (e: 'update:selectedIds', v: number[]): void
  (e: 'open-collection', c: number): void
  (e: 'edit-thumbnail', target: Video | Collection): void
  (e: 'collection-moved', collection: Collection): void
}>()

// Sort items with CollectionCard before VideoCard, using same logic as PlayList
const sortedItems = computed(() => {
  if (!props.category?.items) return []
  
  // Separate collections and videos
  const collections = props.category.items.filter(item => item.type === 'collection')
  const videos = props.category.items.filter(item => item.type === 'video')
  
  // Sort collections by name using natural sorting
  const sortedCollections = collections.sort((a, b) => {
    return a.name.localeCompare(b.name, undefined, { 
      numeric: true, 
      sensitivity: 'base' 
    })
  })
  
  // Sort videos by name using natural sorting  
  const sortedVideos = videos.sort((a, b) => {
    return a.name.localeCompare(b.name, undefined, { 
      numeric: true, 
      sensitivity: 'base' 
    })
  })
  
  // Return collections first, then videos
  return [...sortedCollections, ...sortedVideos]
})
</script>

<template>
  <!-- grid or list of cards -->
  <div v-if="view === 'grid'" class="grid gap-5 grid-cols-[repeat(auto-fit,minmax(240px,300px))]">
    <template v-for="item in sortedItems" :key="item.id">
      <!-- Collection -->
      <!-- 直接把 $event（也就是 col.id）原封不动传出去。 -->
      <CollectionCard
        v-if="item.type === 'collection'"
        :col="item"
        :view="view"
        @edit-thumbnail="emit('edit-thumbnail', $event)"
        @open-collection="emit('open-collection', $event)"
        @collection-moved="handleCollectionMoved"
      />

      <!-- Video -->
      <VideoCard
        v-else
        :video="item"
        :view="view"
        :batch-mode="props.batchMode"
        :checked="props.selectedIds?.includes(item.id) ?? false"
        @edit-thumbnail="emit('edit-thumbnail', $event)"
        @update:checked="toggle(item.id, $event)"
        @generate-subtitle="emit('generate-subtitle', item)"
        @delete="emit('delete', item)"
      />
    </template>
  </div>
</template>
