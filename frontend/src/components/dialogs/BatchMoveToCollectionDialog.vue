<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useHiddenCategories } from '@/composables/useHiddenCategories'

import { BACKEND } from '@/composables/ConfigAPI'

const props = defineProps<{
  modelValue: boolean
  selectedIds: number[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'moved'): void // 通知父组件刷新
}>()

// 定义合集类型
interface Collection {
  id: number
  name: string
  category_id: number
  category_name: string
  thumbnail_url: string
  created_time: string
  last_modified: string
  video_count: number
}

const collections = ref<Collection[]>([])
const targetId = ref<number | null>(null)

// 获取所有合集
async function fetchCollections() {
  try {
    // 获取隐藏的分类ID列表
    const { hiddenCategoryIds } = useHiddenCategories()
    const hiddenCategoriesParam =
      hiddenCategoryIds.value.length > 0
        ? `?hidden_categories=${hiddenCategoryIds.value.join(',')}`
        : ''
    console.log('Fetching collections with hidden categories:', hiddenCategoriesParam)
    const response = await axios.get(`${BACKEND}/api/collection/list${hiddenCategoriesParam}`)
    collections.value = response.data.collections
    console.log(collections.value)
  } catch (e: any) {
    console.error('获取合集列表失败:', e)
    ElMessage.error('获取合集列表失败')
  }
}

onMounted(() => {
  fetchCollections()
})

async function confirm() {
  if (targetId.value === null) {
    ElMessage.warning('请选择目标合集')
    return
  }

  try {
    // 使用批量操作API
    const response = await axios.post(
      `${BACKEND}/api/videos/batch_action`,
      {
        action: 'move_to_collection',
        videoIds: props.selectedIds,
        collectionId: targetId.value,
      },
      {
        headers: { 'Content-Type': 'application/json' },
        withCredentials: true,
      },
    )

    if (response.data.success) {
      ElMessage.success(response.data.message || `已移动 ${props.selectedIds.length} 个视频`)
      emit('moved')
      emit('update:modelValue', false)
    } else {
      ElMessage.error(response.data.error || '批量移动失败')
    }
  } catch (e: any) {
    console.error('批量移动失败:', e)
    ElMessage.error(e.response?.data?.error || '批量移动失败')
  }
}
</script>

<template>
  <el-dialog
    title="批量移动到合集"
    width="320px"
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <el-select v-model="targetId" placeholder="请选择目标合集" class="w-full mb-4">
      <el-option
        v-for="collection in collections"
        :key="collection.id"
        :label="collection.name"
        :value="collection.id"
      />
    </el-select>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="confirm">确定</el-button>
    </template>
  </el-dialog>
</template>
