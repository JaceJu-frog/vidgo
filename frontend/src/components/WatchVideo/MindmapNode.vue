<template>
  <div class="mindmap-node" :style="{ marginLeft: `${level * 24}px` }">
    <!-- 节点主体 -->
    <div class="node-content flex items-start mb-2">
      <!-- 节点圆点 -->
      <div 
        class="node-dot w-2 h-2 bg-blue-400 rounded-full mr-3 mt-2 cursor-pointer hover:bg-blue-300 flex-shrink-0"
        @click="focusNode"
      ></div>
      
      <!-- 节点内容 -->
      <div class="flex-1">
        <!-- 编辑模式 -->
        <div v-if="node.isEditing" class="edit-mode">
          <textarea
            ref="textareaRef"
            v-model="editContent"
            @input="handleInput"
            @keydown="handleKeyDown"
            @blur="handleBlur"
            class="w-full p-2 border border-blue-700/50 bg-slate-700/30 text-white rounded resize-none font-sans text-sm leading-relaxed min-h-[32px] placeholder-slate-400"
            placeholder="输入内容... (```<语言> 创建代码块)"
            rows="1"
          />
        </div>
        
        <!-- 显示模式 -->
        <div v-else class="display-mode">
          <div 
            v-if="node.type === 'text'"
            class="text-content p-2 cursor-pointer hover:bg-slate-700/50 rounded min-h-[32px] text-sm leading-relaxed text-white"
            @click="startEdit"
            v-html="formatContent(node.content)"
          ></div>
          
          <div v-else-if="node.type === 'code'" class="code-content">
            <div 
              class="p-2 cursor-pointer hover:bg-slate-700/50 rounded text-sm leading-relaxed text-white"
              @click="startEdit"
            >
              {{ node.content }}
            </div>
            <div class="code-block mt-1 p-3 bg-slate-700/50 rounded border-l-4 border-blue-400">
              <div class="text-xs text-blue-400 mb-1">{{ node.codeLanguage || 'code' }}</div>
              <pre class="text-sm font-mono bg-slate-800/50 text-slate-200 p-2 rounded border border-slate-600"><code></code></pre>
            </div>
          </div>
          
          <div v-else-if="node.type === 'image'" class="image-content">
            <div 
              class="p-2 cursor-pointer hover:bg-slate-700/50 rounded text-sm leading-relaxed text-white"
              @click="startEdit"
            >
              {{ node.content || '图片节点' }}
            </div>
            <div v-if="node.imageUrl" class="image-block mt-1 p-2 bg-slate-700/30 rounded border border-slate-600">
              <img 
                :src="node.imageUrl" 
                :alt="node.imageAlt || '图片'"
                class="max-w-full max-h-48 rounded cursor-pointer"
                @click="previewImage(node.imageUrl, node.imageAlt)"
                @error="handleImageError"
              />
              <div class="text-xs text-slate-400 mt-1">{{ node.imageAlt || '图片' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 子节点 -->
    <div v-if="node.children.length > 0" class="children">
      <MindmapNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
        @update="$emit('update', $event)"
        @add-child="$emit('add-child', $event)"
        @add-sibling="$emit('add-sibling', $event)"
        @delete="$emit('delete', $event)"
        @focus="$emit('focus', $event)"
        @focus-with-cursor-at-end="$emit('focus-with-cursor-at-end', $event)"
        @indent-in="$emit('indent-in', $event)"
        @indent-out="$emit('indent-out', $event)"
        @navigate="$emit('navigate', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'

interface NodeData {
  id: string
  content: string
  children: NodeData[]
  isEditing: boolean
  type: 'text' | 'code' | 'image'
  codeLanguage?: string
  // New image support
  attachmentId?: number
  imageUrl?: string
  imageAlt?: string
  // Cursor positioning support
  cursorPosition?: 'end'
}

const props = defineProps<{
  node: NodeData
  level: number
}>()

const emit = defineEmits<{
  update: [data: { nodeId: string; content: string; type?: 'text' | 'code'; codeLanguage?: string; exitEditing?: boolean }]
  'add-child': [nodeId: string]
  'add-sibling': [nodeId: string]
  delete: [nodeId: string]
  focus: [nodeId: string]
  'focus-with-cursor-at-end': [nodeId: string]
  'indent-in': [nodeId: string]
  'indent-out': [nodeId: string]
  navigate: [data: { nodeId: string; direction: 'up' | 'down' }]
}>()

const textareaRef = ref<HTMLTextAreaElement>()
const editContent = ref('')

// 开始编辑
const startEdit = () => {
  editContent.value = props.node.content
  emit('focus', props.node.id)
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.focus()
      autoResizeTextarea()
    }
  })
}

// 聚焦节点
const focusNode = () => {
  if (!props.node.isEditing) {
    startEdit()
  }
}

// 自动调整textarea高度
const autoResizeTextarea = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.max(32, textareaRef.value.scrollHeight) + 'px'
  }
}

// 处理输入事件
const handleInput = () => {
  // 自动调整高度
  nextTick(() => autoResizeTextarea())
  // 实时保存内容
  saveContentRealtime()
}

// 实时保存内容（不退出编辑模式）
const saveContentRealtime = () => {
  const content = editContent.value
  
  // 检测是否是代码块
  const codeBlockMatch = content.match(/^```(\w+)?\s*$/)
  if (codeBlockMatch) {
    const language = codeBlockMatch[1] || 'text'
    emit('update', {
      nodeId: props.node.id,
      content: content.replace(/^```\w*\s*/, ''),
      type: 'code',
      codeLanguage: language,
      exitEditing: false
    })
  } else {
    emit('update', {
      nodeId: props.node.id,
      content: content,
      type: 'text',
      exitEditing: false
    })
  }
}

// 保存内容但不退出编辑模式
const saveContentWithoutExit = () => {
  const content = editContent.value
  
  // 检测是否是代码块
  const codeBlockMatch = content.match(/^```(\w+)?\s*$/)
  if (codeBlockMatch) {
    const language = codeBlockMatch[1] || 'text'
    emit('update', {
      nodeId: props.node.id,
      content: content.replace(/^```\w*\s*/, ''),
      type: 'code',
      codeLanguage: language,
      exitEditing: false
    })
  } else {
    emit('update', {
      nodeId: props.node.id,
      content: content,
      type: 'text',
      exitEditing: false
    })
  }
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  const textarea = textareaRef.value
  if (!textarea) return

  // 自动调整高度
  nextTick(() => autoResizeTextarea())

  // Enter - 添加兄弟节点
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    saveContentWithoutExit()
    emit('add-sibling', props.node.id)
    return
  }

  // Shift+Enter - 换行
  if (event.key === 'Enter' && event.shiftKey) {
    // 让默认行为发生（换行）
    nextTick(() => autoResizeTextarea())
    return
  }

  // ArrowUp - 导航到上一个节点
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    saveContentWithoutExit()
    emit('navigate', { nodeId: props.node.id, direction: 'up' })
    return
  }

  // ArrowDown - 导航到下一个节点
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    saveContentWithoutExit()
    emit('navigate', { nodeId: props.node.id, direction: 'down' })
    return
  }

  // Tab - 增加缩进（向右移动一层）并保持编辑状态
  if (event.key === 'Tab' && !event.shiftKey) {
    event.preventDefault()
    saveContentWithoutExit()
    emit('indent-in', props.node.id)
    return
  }

  // Shift+Tab - 减少缩进（向左移动一层）并保持编辑状态
  if (event.key === 'Tab' && event.shiftKey) {
    event.preventDefault()
    saveContentWithoutExit()
    emit('indent-out', props.node.id)
    return
  }

  // Backspace - 删除空节点
  if (event.key === 'Backspace' && editContent.value === '') {
    event.preventDefault()
    emit('delete', props.node.id)
    return
  }
}

// 处理失焦
const handleBlur = () => {
  saveContent()
}

// 保存内容
const saveContent = () => {
  const content = editContent.value.trim()
  
  // 检测是否是代码块
  const codeBlockMatch = content.match(/^```(\w+)?\s*$/)
  if (codeBlockMatch) {
    const language = codeBlockMatch[1] || 'text'
    emit('update', {
      nodeId: props.node.id,
      content: content.replace(/^```\w*\s*/, ''),
      type: 'code',
      codeLanguage: language,
      exitEditing: true
    })
  } else {
    emit('update', {
      nodeId: props.node.id,
      content: content,
      type: 'text',
      exitEditing: true
    })
  }
}

// Image preview functionality
const previewImage = (url?: string, alt?: string) => {
  if (!url) return
  
  // Create a modal/overlay for image preview
  const overlay = document.createElement('div')
  overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm'
  overlay.style.cursor = 'pointer'
  
  const img = document.createElement('img')
  img.src = url
  img.alt = alt || '图片'
  img.className = 'max-w-[90vw] max-h-[90vh] rounded-lg shadow-2xl'
  
  const closeBtn = document.createElement('button')
  closeBtn.innerHTML = '✕'
  closeBtn.className = 'absolute top-4 right-4 text-white text-2xl font-bold bg-black/50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-black/70 transition-colors'
  
  overlay.appendChild(img)
  overlay.appendChild(closeBtn)
  document.body.appendChild(overlay)
  
  const closeModal = () => {
    document.body.removeChild(overlay)
  }
  
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal()
  })
  
  closeBtn.addEventListener('click', closeModal)
  
  // Close on Escape key
  const handleKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      closeModal()
      document.removeEventListener('keydown', handleKeydown)
    }
  }
  document.addEventListener('keydown', handleKeydown)
}

// Handle image loading errors
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  console.error('Failed to load image:', img.src)
  // You could replace with a placeholder image here
}

// 格式化显示内容
const formatContent = (content: string) => {
  if (!content) return '<span class="text-gray-400">点击编辑...</span>'
  
  // 简单的格式化：将换行转为<br>
  return content.replace(/\n/g, '<br>')
}

// 监听编辑状态变化
watch(() => props.node.isEditing, (isEditing) => {
  if (isEditing) {
    editContent.value = props.node.content
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.focus()
        
        // 检查是否需要将光标移到末尾
        const cursorPos = props.node.cursorPosition
        if (cursorPos === 'end') {
          // 将光标移到文本末尾
          const textLength = textareaRef.value.value.length
          textareaRef.value.setSelectionRange(textLength, textLength)
          // 清除标记
          props.node.cursorPosition = undefined
        } else {
          // 默认将光标移到文本末尾
          const textLength = textareaRef.value.value.length
          textareaRef.value.setSelectionRange(textLength, textLength)
        }
        
        autoResizeTextarea()
      }
    })
  }
})

onMounted(() => {
  if (props.node.isEditing) {
    editContent.value = props.node.content
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.focus()
        autoResizeTextarea()
      }
    })
  }
})
</script>

<style scoped>
.mindmap-node {
  position: relative;
}

.node-dot {
  transition: background-color 0.2s;
}

.edit-mode textarea {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.display-mode {
  min-height: 32px;
}

.text-content {
  word-break: break-word;
}

.code-block {
  font-family: 'Courier New', monospace;
}

.code-block pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>