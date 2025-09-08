<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { markdownToHtml, processMarkdownContent } from '@/composables/ConvertMarkdown'
import { NotesAPI } from '@/composables/NotesAPI'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { BACKEND } from '@/composables/ConfigAPI'

// i18n functionality
const { t } = useI18n()

const props = defineProps<{
  videoId: number
}>()

const notesContent = ref('')
const editMode = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()
const fileInputRef = ref<HTMLInputElement>()

// Image display configuration (keeping for potential future use)
const maxVisibleImages = ref(3)

// Character count and limit
const characterCount = computed(() => notesContent.value.length)
const characterLimit = 8000
const isOverLimit = computed(() => characterCount.value > characterLimit)

// Separate pure content from attachments
const parsedContent = computed(() => {
  const content = notesContent.value
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g
  const attachments: Array<{ alt: string; url: string; markdown: string }> = []

  // Extract images
  let match
  while ((match = imageRegex.exec(content)) !== null) {
    let imageUrl = match[2]

    // If the URL is a relative path starting with /media/, prepend backend URL
    if (imageUrl.startsWith('/media/')) {
      imageUrl = `${BACKEND}${imageUrl}`
    }

    attachments.push({
      alt: match[1] || 'Image',
      url: imageUrl,
      markdown: match[0],
    })
  }

  // Remove image markdown from content, leaving pure text and code blocks
  const pureContent = content.replace(imageRegex, '').replace(/\n\n+/g, '\n\n').trim()

  return {
    pureContent,
    attachments,
  }
})

const renderedNotes = ref('')
const notesContentRef = ref<HTMLElement>()

// Render markdown content asynchronously
const renderMarkdown = async () => {
  if (!parsedContent.value.pureContent.trim()) {
    renderedNotes.value = ''
    return
  }

  try {
    const html = await markdownToHtml(parsedContent.value.pureContent)
    renderedNotes.value = html

    // Process mermaid diagrams after DOM update
    await nextTick()
    if (notesContentRef.value) {
      await processMarkdownContent(notesContentRef.value)
    }
  } catch (error) {
    console.error('Failed to render markdown:', error)
    renderedNotes.value = `<p>${parsedContent.value.pureContent}</p>`
  }
}

// Load notes when component mounts or videoId changes
const loadNotes = async () => {
  if (!props.videoId || props.videoId <= 0) {
    notesContent.value = ''
    return
  }

  isLoading.value = true
  try {
    const notes = await NotesAPI.loadNotes(props.videoId)
    notesContent.value = notes || ''
  } catch (error) {
    console.error('Failed to load notes:', error)
    ElMessage.error(t('loadNotesFailed'))
  } finally {
    isLoading.value = false
  }
}

const saveNotes = async () => {
  if (!props.videoId || props.videoId <= 0) {
    ElMessage.error('Invalid video ID')
    return
  }

  if (isOverLimit.value) {
    ElMessage.error(
      t('noteContentExceedsLimit', { current: characterCount.value, limit: characterLimit }),
    )
    return
  }

  isSaving.value = true
  try {
    await NotesAPI.saveNotes(props.videoId, notesContent.value)
    ElMessage.success(t('notesSavedSuccess'))
    editMode.value = false
  } catch (error: any) {
    console.error('Failed to save notes:', error)
    ElMessage.error(error.message || t('saveNotesFailed'))
  } finally {
    isSaving.value = false
  }
}

const toggleEdit = () => {
  if (editMode.value && characterCount.value > 0) {
    // Auto-save when exiting edit mode
    saveNotes()
  } else {
    editMode.value = !editMode.value
    if (editMode.value) {
      nextTick(() => {
        textareaRef.value?.focus()
      })
    }
  }
}

// Handle image paste
const handlePaste = async (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault()
      const file = item.getAsFile()
      if (!file) continue
      await uploadImage(file, 'Pasted Image')
      break
    }
  }
}

// Unified image upload function
const uploadImage = async (file: File, defaultAlt: string = 'Uploaded Image') => {
  try {
    ElMessage.info('正在上传图片...')
    const imageUrl = await NotesAPI.uploadNoteImage(props.videoId, file)

    // Insert markdown image syntax at cursor position
    const textarea = textareaRef.value
    const imageMarkdown = `![${defaultAlt}](${imageUrl})`

    if (textarea && editMode.value) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd

      notesContent.value =
        notesContent.value.substring(0, start) + imageMarkdown + notesContent.value.substring(end)

      // Set cursor position after the inserted image
      nextTick(() => {
        const newPosition = start + imageMarkdown.length
        textarea.setSelectionRange(newPosition, newPosition)
        textarea.focus()
      })
    } else {
      // If not in edit mode or no textarea, append to end
      notesContent.value += (notesContent.value ? '\n\n' : '') + imageMarkdown
    }

    ElMessage.success('Image uploaded successfully')
  } catch (error: any) {
    console.error('Failed to upload image:', error)
    ElMessage.error(error.message || 'Image upload failed')
  }
}

// Handle file upload from toolbar
const handleFileUpload = () => {
  fileInputRef.value?.click()
}

const onFileSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (file.type.startsWith('image/')) {
      await uploadImage(file, file.name.split('.')[0])
    }
  }

  // Reset file input
  target.value = ''
}

// Image preview functionality
const openImagePreview = (initialIndex: number) => {
  const images = parsedContent.value.attachments
  if (!images.length) return

  let currentIndex = initialIndex

  // Create a modal/overlay for image preview
  const overlay = document.createElement('div')
  overlay.className =
    'fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm'

  const container = document.createElement('div')
  container.className = 'relative flex items-center justify-center w-full h-full'

  const img = document.createElement('img')
  img.className = 'max-w-[90vw] max-h-[90vh] rounded-lg shadow-2xl transition-opacity duration-300'

  const closeBtn = document.createElement('button')
  closeBtn.innerHTML = '✕'
  closeBtn.className =
    'absolute top-4 right-4 text-white text-2xl font-bold bg-black/50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-black/70 transition-colors z-10'

  // Navigation arrows
  const leftArrow = document.createElement('button')
  leftArrow.innerHTML = '❮'
  leftArrow.className =
    'absolute left-4 top-1/2 transform -translate-y-1/2 text-white text-3xl font-bold bg-black/50 rounded-full w-12 h-12 flex items-center justify-center hover:bg-black/70 transition-colors z-10'

  const rightArrow = document.createElement('button')
  rightArrow.innerHTML = '❯'
  rightArrow.className =
    'absolute right-4 top-1/2 transform -translate-y-1/2 text-white text-3xl font-bold bg-black/50 rounded-full w-12 h-12 flex items-center justify-center hover:bg-black/70 transition-colors z-10'

  // Image counter
  const counter = document.createElement('div')
  counter.className =
    'absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white bg-black/50 rounded-lg px-3 py-1 text-sm'

  const updateImage = () => {
    const currentImage = images[currentIndex]
    img.src = currentImage.url
    img.alt = currentImage.alt
    counter.textContent = `${currentIndex + 1} / ${images.length}`

    // Update arrow visibility
    leftArrow.style.display = images.length > 1 ? 'flex' : 'none'
    rightArrow.style.display = images.length > 1 ? 'flex' : 'none'
    leftArrow.style.opacity = currentIndex > 0 ? '1' : '0.5'
    rightArrow.style.opacity = currentIndex < images.length - 1 ? '1' : '0.5'
  }

  const goToPrevious = () => {
    if (currentIndex > 0) {
      currentIndex--
      updateImage()
    }
  }

  const goToNext = () => {
    if (currentIndex < images.length - 1) {
      currentIndex++
      updateImage()
    }
  }

  container.appendChild(img)
  container.appendChild(closeBtn)
  container.appendChild(leftArrow)
  container.appendChild(rightArrow)
  container.appendChild(counter)
  overlay.appendChild(container)
  document.body.appendChild(overlay)

  // Initialize with current image
  updateImage()

  const closeModal = () => {
    document.body.removeChild(overlay)
    document.removeEventListener('keydown', handleKeydown)
  }

  // Event listeners
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal()
  })

  closeBtn.addEventListener('click', closeModal)
  leftArrow.addEventListener('click', goToPrevious)
  rightArrow.addEventListener('click', goToNext)

  // Keyboard navigation
  const handleKeydown = (e: KeyboardEvent) => {
    e.preventDefault()
    switch (e.key) {
      case 'Escape':
        closeModal()
        break
      case 'ArrowLeft':
        goToPrevious()
        break
      case 'ArrowRight':
        goToNext()
        break
    }
  }
  document.addEventListener('keydown', handleKeydown)
}

// Auto-save functionality
let saveTimeout: ReturnType<typeof setTimeout>
const autoSave = () => {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    if (editMode.value && notesContent.value.trim() && !isOverLimit.value) {
      saveNotes()
    }
  }, 30000) // Auto-save after 30 seconds of no typing
}

// Watch for content changes to re-render markdown
watch(() => parsedContent.value.pureContent, renderMarkdown)

watch(() => notesContent.value, autoSave)

onMounted(async () => {
  await loadNotes()
  await renderMarkdown()
})

// Watch for videoId changes
watch(
  () => props.videoId,
  async () => {
    await loadNotes()
    await renderMarkdown()
  },
  { immediate: false },
)
</script>

<template>
  <div class="p-6 pb-20 relative">
    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      @change="onFileSelected"
      class="hidden"
    />

    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center space-x-2">
        <div
          v-if="isLoading"
          class="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"
        ></div>
      </div>

      <div class="flex items-center space-x-4">
        <!-- Character count -->
        <div
          class="text-sm px-3 py-1 rounded-lg bg-slate-700/50 border border-slate-600/30"
          :class="isOverLimit ? 'text-red-400 border-red-500/50' : 'text-slate-300'"
        >
          {{ characterCount }} / {{ characterLimit }}
        </div>

        <!-- Edit/Save button -->
        <button
          @click="toggleEdit"
          :disabled="isSaving || isLoading"
          class="px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium"
          :class="
            editMode
              ? 'bg-blue-600/80 hover:bg-blue-600 text-white border border-blue-500/30 disabled:opacity-50'
              : 'bg-slate-700/50 hover:bg-slate-600/70 text-slate-300 border border-slate-600/30'
          "
        >
          <span v-if="isSaving" class="flex items-center">
            <svg
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            保存中...
          </span>
          <span v-else>{{ editMode ? '保存' : '编辑' }}</span>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div>
      <div v-if="isLoading" class="flex items-center justify-center py-12 text-slate-400">
        <div
          class="animate-spin w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full mr-3"
        ></div>
        {{ t('loadingNotes') }}
      </div>

      <!-- Edit Mode -->
      <div v-else-if="editMode" class="space-y-4">
        <div class="relative">
          <textarea
            ref="textareaRef"
            v-model="notesContent"
            @paste="handlePaste"
            class="w-full h-80 p-4 bg-slate-700/30 border rounded-xl resize-none focus:outline-none focus:ring-2 text-white placeholder-slate-400 backdrop-blur-sm transition-all notes-textarea"
            :class="
              isOverLimit
                ? 'border-red-500/50 focus:ring-red-500/50'
                : 'border-slate-600/50 focus:ring-blue-500/50'
            "
            :placeholder="t('notePlaceholder')"
          ></textarea>
        </div>

        <!-- Help text -->
        <div
          class="text-xs text-slate-300 bg-slate-700/30 p-3 rounded-lg border border-slate-600/30"
        >
          <strong class="text-blue-400">快速帮助：</strong>
          支持完整 Markdown 语法 | 直接粘贴图片自动上传 | 自动保存（2秒后）
        </div>

        <!-- Warning for character limit -->
        <div
          v-if="isOverLimit"
          class="text-sm text-red-300 bg-red-900/20 p-3 rounded-lg border border-red-500/30"
        >
          ⚠️ 内容超出字符限制，请删减至 {{ characterLimit }} 字符以内
        </div>
      </div>

      <!-- View Mode -->
      <div v-else>
        <div v-if="notesContent.trim()" class="space-y-6">
          <!-- Pure Notes Content -->
          <div
            v-if="renderedNotes.trim()"
            ref="notesContentRef"
            class="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-slate-200 prose-strong:text-white prose-code:text-blue-400 prose-code:bg-slate-700/50 prose-pre:bg-slate-700/50 prose-blockquote:border-blue-500/50 prose-a:text-blue-400 notes-content bg-slate-800/30 rounded-xl p-4 backdrop-blur-lg border border-slate-600/30"
            v-html="renderedNotes"
          ></div>

          <!-- Attachments Section -->
          <div v-if="parsedContent.attachments.length > 0" class="space-y-4">
            <div class="flex items-center space-x-2">
              <div class="h-px flex-1 bg-slate-600/30"></div>
              <span class="text-sm text-slate-400 font-medium">附件</span>
              <div class="h-px flex-1 bg-slate-600/30"></div>
            </div>

            <!-- Horizontal scrolling image grid -->
            <div
              class="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800"
            >
              <div
                v-for="(attachment, index) in parsedContent.attachments"
                :key="index"
                class="relative group bg-slate-700/30 rounded-xl border border-slate-600/30 flex-shrink-0"
              >
                <img
                  :src="attachment.url"
                  :alt="attachment.alt"
                  class="w-[300px] h-[200px] object-cover rounded-xl cursor-pointer transition-transform duration-200 hover:scale-[1.02]"
                  @error="() => console.error('Image failed to load:', attachment.url)"
                  @click="openImagePreview(index)"
                />
                <div
                  class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                >
                  <div class="bg-black/50 rounded-lg px-2 py-1 text-xs text-white">
                    {{ attachment.alt }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-16 text-slate-400">
          <svg
            class="mx-auto h-16 w-16 text-slate-500 mb-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            ></path>
          </svg>
          <p class="text-xl font-medium text-slate-300 mb-2">{{ t('noNotes') }}</p>
          <p class="text-sm text-slate-500">{{ t('clickEditToStartNotes') }}</p>
        </div>
      </div>
    </div>

    <!-- Fixed Bottom Toolbar -->
    <div
      class="fixed bottom-0 left-0 right-0 bg-slate-800/80 backdrop-blur-md border-t border-slate-600/30 p-4"
    >
      <div class="flex justify-center">
        <button
          @click="handleFileUpload"
          :disabled="isLoading || isSaving"
          class="flex items-center space-x-2 px-6 py-2 bg-blue-600/80 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-all duration-200 font-medium border border-blue-500/30"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            ></path>
          </svg>
          <span>上传附件</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notes-textarea {
  color: white !important;
}

/* 确保笔记内容中的所有文本都是白色 */
.notes-content {
  color: white !important;
  background-color: rgba(30, 41, 59, 0.3) !important; /* bg-slate-800/30 */
}

.notes-content * {
  color: inherit !important;
}

/* 特殊元素保持其指定颜色 */
.notes-content h1,
.notes-content h2,
.notes-content h3,
.notes-content h4,
.notes-content h5,
.notes-content h6 {
  color: white !important;
}

.notes-content p {
  color: rgb(226 232 240) !important; /* slate-200 */
}

.notes-content strong,
.notes-content b {
  color: white !important;
}

.notes-content code {
  color: rgb(96 165 250) !important; /* blue-400 */
}

.notes-content a {
  color: rgb(96 165 250) !important; /* blue-400 */
}

/* Override prose backgrounds to match panel background */
.notes-content *,
.notes-content *::before,
.notes-content *::after {
  background-color: transparent !important;
}

.notes-content pre {
  background-color: rgba(51, 65, 85, 0.5) !important; /* bg-slate-700/50 */
}

.notes-content code {
  background-color: rgba(51, 65, 85, 0.5) !important; /* bg-slate-700/50 */
}

.notes-content blockquote {
  background-color: transparent !important;
}

/* Ensure the main content area background is visible */
.notes-content {
  background-color: rgba(30, 41, 59, 0.3) !important; /* bg-slate-800/30 */
}
</style>
