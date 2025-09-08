<script setup lang="ts">
import { defineProps, defineEmits, toRefs } from 'vue'
import { Grid, List } from '@element-plus/icons-vue'

type Tab = 'all' | 'video' | 'audio'
type View = 'grid' | 'list'

const props = defineProps<{
  activeTab: Tab
  viewType: View
}>()

const emit = defineEmits<{
  (e: 'update:activeTab', tab: Tab): void
  (e: 'update:viewType', view: View): void
}>()

const { activeTab, viewType } = toRefs(props)

function setView(view: View) {
  emit('update:viewType', view)
}
</script>

<template>
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
    <!-- el tab for video/audio toggler in display -->
    <el-tabs v-model:activeTab="activeTab" class="flex-grow">
      <el-tab-pane label="全部媒体" name="all" />
      <el-tab-pane label="视频文件" name="video" />
      <el-tab-pane label="音频文件" name="audio" />
    </el-tabs>

    <!-- Grid/List toggler (emit update:viewType) -->
    <div class="flex gap-1 bg-gray-100 p-1 rounded-lg">
      <el-button
        :class="
          viewType === 'grid'
            ? '!bg-white !text-primary !shadow-sm'
            : '!bg-transparent !text-gray-500'
        "
        @click="setView('grid')"
      >
        <el-icon><Grid /></el-icon>
      </el-button>

      <el-button
        :class="
          viewType === 'list'
            ? '!bg-white !text-primary !shadow-sm'
            : '!bg-transparent !text-gray-500'
        "
        @click="setView('list')"
      >
        <el-icon><List /></el-icon>
      </el-button>
    </div>
  </div>
</template>
