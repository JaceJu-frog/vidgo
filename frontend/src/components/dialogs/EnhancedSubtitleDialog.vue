<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getCookie } from '@/composables/GetCSRFToken'

import { BACKEND } from '@/composables/ConfigAPI'

// —— Props ——
const props = defineProps<{
  /** v-model 控制弹窗显隐 */
  modelValue: boolean
  /** 待处理视频 ID 列表  */
  videoIdList: number[]
  /** 与 videoIdList 一一对应的标题，用于后端记录 */
  videoNameList: string[]
  /** 当前视频的原始语言（用于预选择下拉框） */
  currentRawLang?: string
}>()

// —— Emits ——
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  /** 后端提交成功后可通知父组件刷新 */
  (e: 'submitted'): void
}>()

// —— Dialog v-model 代理 ——
const visible = computed<boolean>({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

// —— 表单状态 ——
// 优先使用当前视频的rawLang，如果没有则保持之前的选择（默认'zh'）
const srcLang = ref<'zh' | 'en' | 'jp' | 'system_define'>(
  (props.currentRawLang as 'zh' | 'en' | 'jp' | 'system_define') || 'zh',
)
const transLang = ref<'none' | 'zh' | 'en' | 'jp'>('none')
const emphasizeSrc = ref('')
const emphasizeDst = ref('')
const loading = ref(false)

// 新增状态
const actionType = ref<'set_language' | 'generate_bilingual' | 'generate_translation'>(
  'generate_bilingual',
)

// —— API调用函数 ——
async function setVideoLanguage() {
  if (!srcLang.value) {
    ElMessage.warning('请选择视频语言')
    return
  }

  loading.value = true
  const csrfToken = getCookie('csrftoken')

  try {
    // 为每个视频设置语言
    for (const videoId of props.videoIdList) {
      const res = await fetch(`${BACKEND}/api/videos/${videoId}/update_raw_lang`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          raw_lang: srcLang.value,
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    }

    ElMessage.success('视频语言设置成功')
    emit('submitted')
    emit('update:modelValue', false)
  } catch (err: any) {
    console.error(err)
    ElMessage.error(`设置失败：${err.message}`)
  } finally {
    loading.value = false
  }
}

async function generateBilingualSubtitles() {
  if (!srcLang.value) {
    ElMessage.warning('请选择原文语言')
    return
  }

  loading.value = true
  const csrfToken = getCookie('csrftoken')

  try {
    const res = await fetch(`${BACKEND}/api/tasks/subtitle_generate/add`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        video_id_list: props.videoIdList,
        video_name_list: props.videoNameList,
        src_lang: srcLang.value,
        trans_lang: transLang.value === 'none' ? '' : transLang.value,
        emphasize_src: emphasizeSrc.value,
        emphasize_dst: emphasizeDst.value,
      }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    ElMessage.success('已提交双语字幕生成任务')
    emit('submitted')
    emit('update:modelValue', false)
  } catch (err: any) {
    console.error(err)
    ElMessage.error(`提交失败：${err.message}`)
  } finally {
    loading.value = false
  }
}

async function generateTranslationOnly() {
  if (!transLang.value || transLang.value === 'none') {
    ElMessage.warning('请选择翻译语言')
    return
  }

  loading.value = true
  const csrfToken = getCookie('csrftoken')

  try {
    const res = await fetch(`${BACKEND}/api/tasks/subtitle_translation/add`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        video_id_list: props.videoIdList,
        video_name_list: props.videoNameList,
        target_lang: transLang.value,
        emphasize_dst: emphasizeDst.value,
      }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    ElMessage.success('已提交翻译字幕生成任务')
    emit('submitted')
    emit('update:modelValue', false)
  } catch (err: any) {
    console.error(err)
    ElMessage.error(`提交失败：${err.message}`)
  } finally {
    loading.value = false
  }
}

// —— 主确认函数 ——
async function confirm() {
  switch (actionType.value) {
    case 'set_language':
      await setVideoLanguage()
      break
    case 'generate_bilingual':
      await generateBilingualSubtitles()
      break
    case 'generate_translation':
      await generateTranslationOnly()
      break
  }
}

// 计算标题
const dialogTitle = computed(() => {
  switch (actionType.value) {
    case 'set_language':
      return '设置视频语言'
    case 'generate_bilingual':
      return '生成双语字幕'
    case 'generate_translation':
      return '生成翻译字幕'
    default:
      return '字幕操作'
  }
})

// 计算确认按钮文本
const confirmButtonText = computed(() => {
  switch (actionType.value) {
    case 'set_language':
      return '设置语言'
    case 'generate_bilingual':
      return '生成双语字幕'
    case 'generate_translation':
      return '生成翻译'
    default:
      return '确定'
  }
})
</script>

<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="480px">
    <!-- 操作类型选择 -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-slate-300 mb-3">操作类型</label>
      <el-radio-group v-model="actionType" class="w-full">
        <div class="space-y-2">
          <el-radio value="set_language" class="w-full !mr-0">
            <span class="text-slate-200">设置视频语言（用于正确展示字幕）</span>
          </el-radio>
          <el-radio value="generate_bilingual" class="w-full !mr-0">
            <span class="text-slate-200">生成双语字幕（原文+翻译）</span>
          </el-radio>
          <el-radio value="generate_translation" class="w-full !mr-0">
            <span class="text-slate-200">仅生成翻译字幕（基于已有原文）</span>
          </el-radio>
        </div>
      </el-radio-group>
    </div>

    <div class="space-y-4">
      <!-- 原文语言选择 -->
      <div v-if="actionType === 'set_language' || actionType === 'generate_bilingual'">
        <label class="block text-sm font-medium text-slate-300 mb-2">
          {{ actionType === 'set_language' ? '视频语言' : '原文语言' }}
        </label>
        <el-select v-model="srcLang" placeholder="选择语言" class="w-full">
          <el-option label="中文 (zh)" value="zh" />
          <el-option label="English (en)" value="en" />
          <el-option label="日本語 (jp)" value="jp" />
          <el-option
            v-if="actionType === 'generate_bilingual'"
            label="System Define"
            value="system_define"
          />
        </el-select>
      </div>

      <!-- 译文语言选择 -->
      <div v-if="actionType === 'generate_bilingual' || actionType === 'generate_translation'">
        <label class="block text-sm font-medium text-slate-300 mb-2">
          {{ actionType === 'generate_bilingual' ? '译文语言' : '翻译目标语言' }}
        </label>
        <el-select v-model="transLang" placeholder="选择译文语言" class="w-full">
          <el-option v-if="actionType === 'generate_bilingual'" label="无 (None)" value="none" />
          <el-option label="中文 (zh)" value="zh" />
          <el-option label="English (en)" value="en" />
          <el-option label="日本語 (jp)" value="jp" />
        </el-select>
      </div>

      <!-- 译文强调名词 -->
      <div v-if="actionType === 'generate_bilingual' || actionType === 'generate_translation'">
        <label class="block text-sm font-medium text-slate-300 mb-2">译文强调名词</label>
        <el-input
          v-model="emphasizeDst"
          type="textarea"
          :rows="2"
          placeholder="译文中需强调的名词（仅本地记录，可留空）"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="confirm">{{
        confirmButtonText
      }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
:deep(.el-radio) {
  height: auto;
  align-items: flex-start;
}

:deep(.el-radio__input) {
  margin-top: 2px;
}

:deep(.el-radio__label) {
  white-space: normal;
  line-height: 1.5;
}
</style>
