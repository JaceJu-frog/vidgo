<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

import { BACKEND } from '@/composables/ConfigAPI'

const props = defineProps<{
  modelValue: boolean
  selectedIds: number[]
  categories: { id: number | null; name: string }[] // ← 允许 null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'moved'): void // 通知父组件刷新
}>()

const targetId = ref<number | null>(null)

async function confirm() {
  if (targetId.value === null) {
    ElMessage.warning('请选择目标分类')
    return
  }
  // 并发调用接口，全部成功才算成功
  try {
    await Promise.all(
      props.selectedIds.map((id) =>
        axios.post(
          `${BACKEND}/api/videos/${id}/move_category`,
          { categoryId: targetId.value },
          { headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )
    ElMessage.success(`已移动 ${props.selectedIds.length} 个视频`)
    emit('moved')
    emit('update:modelValue', false)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || '批量移动失败')
  }
}
</script>

<template>
  <el-dialog
    title="批量移动到分类"
    width="320px"
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <el-select v-model="targetId" placeholder="请选择目标分类" class="w-full mb-4">
      <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
    </el-select>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="confirm">确定</el-button>
    </template>
  </el-dialog>
</template>
