<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const props = defineProps<{
  modelValue: boolean
  visible: boolean
  tasks: any[]
}>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:modelValue': [value: boolean]
}>()
const { t } = useI18n()
</script>

<template>
  <el-dialog
    :model-value="props.modelValue"
    width="700px"
    :title="t('tasks')"
    @close="emit('update:visible', false)"
  >
    <el-table :data="tasks" style="width: 100%">
      <el-table-column prop="videoName" label="Video" width="180" />
      <el-table-column prop="status" label="Status" width="120">
        <template #default="{ row }">
          <el-tag
            :type="
              row.status === 'Completed'
                ? 'success'
                : row.status.includes('Error')
                  ? 'danger'
                  : 'warning'
            "
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="Progress">
        <template #default="{ row }">
          <el-progress
            :percentage="row.progress"
            :status="
              row.status === 'Completed'
                ? 'success'
                : row.status.includes('Error')
                  ? 'exception'
                  : undefined
            "
          />
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="emit('update:visible', false)">
        {{ t('confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>
