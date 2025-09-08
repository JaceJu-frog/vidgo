<template>
  <div class="mindmap-editor h-full flex flex-col">
    <!-- 简化的导航栏 -->
    <div class="flex justify-between items-center mb-4 p-3 bg-slate-700/50 rounded">
      <span class="text-sm text-slate-300">思维导图编辑器</span>
      <div class="flex items-center gap-2">
        <el-button size="small" @click="saveContent" type="primary">
          保存
        </el-button>
        <el-button size="small" @click="toggleDisplayMode">
          {{ displayMode === 'list' ? '思维导图' : '列表' }}
        </el-button>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-if="displayMode === 'list'" class="flex-1 rounded border border-blue-700/50 p-4 overflow-y-auto mindmap-bg">
      <div class="mindmap-nodes">
        <MindmapNode 
          v-for="node in nodes"
          :key="node.id"
          :node="node"
          :level="0"
          @update="updateNode"
          @add-child="addChildNode"
          @add-sibling="addSiblingNode"
          @delete="deleteNode"
          @focus="focusNode"
          @focus-with-cursor-at-end="focusNodeWithCursorAtEnd"
          @indent-in="indentNodeIn"
          @indent-out="indentNodeOut"
          @navigate="handleNavigation"
        />
        
        <!-- 添加根节点按钮 -->
        <div v-if="nodes.length === 0" class="flex items-center text-slate-400 cursor-pointer hover:text-slate-300" @click="addRootNode">
          <div class="w-2 h-2 bg-slate-400 rounded-full mr-3"></div>
          <span class="text-sm text-slate-300">点击开始创建思维导图...</span>
        </div>
      </div>
    </div>

    <!-- 思维导图预览模式 -->
    <div v-else class="flex-1">
      <div class="h-full border border-blue-700/50 rounded mindmap-bg" ref="mindmapContainer">
        <svg ref="svgElement" class="w-full h-full"></svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Markmap } from 'markmap-view'
import { Transformer } from 'markmap-lib'
import MindmapNode from './MindmapNode.vue'

const props = defineProps<{
  initialContent?: any
}>()

const emit = defineEmits<{
  contentChange: [content: any]
  save: [content: any]
}>()

// 显示模式：list(列表编辑) 或 mindmap(思维导图预览)
const displayMode = ref<'list' | 'mindmap'>('list')

// 节点数据结构
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

const nodes = ref<NodeData[]>([])
const svgElement = ref<SVGElement>()
const mindmapContainer = ref<HTMLElement>()
let markmap: Markmap | null = null
const transformer = new Transformer()

// 生成唯一ID
const generateId = () => `node_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`

// 添加根节点
const addRootNode = () => {
  const newNode: NodeData = {
    id: generateId(),
    content: '',
    children: [],
    isEditing: true,
    type: 'text'
  }
  nodes.value.push(newNode)
}

// 查找节点
const findNode = (nodeId: string, nodeList: NodeData[] = nodes.value): NodeData | null => {
  for (const node of nodeList) {
    if (node.id === nodeId) return node
    const found = findNode(nodeId, node.children)
    if (found) return found
  }
  return null
}

// 查找节点的父节点和索引
const findNodeParent = (nodeId: string, nodeList: NodeData[] = nodes.value, parent: NodeData | null = null): { parent: NodeData | null, index: number } | null => {
  for (let i = 0; i < nodeList.length; i++) {
    if (nodeList[i].id === nodeId) {
      return { parent, index: i }
    }
    const found = findNodeParent(nodeId, nodeList[i].children, nodeList[i])
    if (found) return found
  }
  return null
}

// 更新节点内容
const updateNode = (data: { nodeId: string; content: string; type?: 'text' | 'code'; codeLanguage?: string; exitEditing?: boolean }) => {
  const node = findNode(data.nodeId)
  if (node) {
    node.content = data.content
    node.type = data.type || 'text'
    if (data.codeLanguage) node.codeLanguage = data.codeLanguage
    
    // 只有明确指定时才退出编辑模式
    if (data.exitEditing !== false) {
      node.isEditing = false
    }
    
    emitContentChange()
  }
}

// 添加子节点
const addChildNode = (parentId: string) => {
  const parent = findNode(parentId)
  if (parent) {
    const newNode: NodeData = {
      id: generateId(),
      content: '',
      children: [],
      isEditing: true,
      type: 'text'
    }
    parent.children.push(newNode)
  }
}

// 添加兄弟节点
const addSiblingNode = (nodeId: string) => {
  const result = findNodeParent(nodeId)
  if (result) {
    const { parent, index } = result
    const newNode: NodeData = {
      id: generateId(),
      content: '',
      children: [],
      isEditing: true,
      type: 'text'
    }
    
    if (parent) {
      parent.children.splice(index + 1, 0, newNode)
    } else {
      nodes.value.splice(index + 1, 0, newNode)
    }
  }
}

// 删除节点
const deleteNode = (nodeId: string) => {
  const result = findNodeParent(nodeId)
  if (result) {
    const { parent, index } = result
    const nodeList = parent ? parent.children : nodes.value
    
    // 找到要聚焦的上一个节点
    let targetNode: NodeData | null = null
    
    if (index > 0) {
      // 如果不是第一个节点，聚焦到前一个节点
      targetNode = nodeList[index - 1]
    } else if (nodeList.length > 1) {
      // 如果是第一个节点但还有其他节点，聚焦到下一个节点
      targetNode = nodeList[index + 1]
    } else if (parent) {
      // 如果是唯一的子节点，聚焦到父节点
      targetNode = parent
    }
    
    // 删除节点
    if (parent) {
      parent.children.splice(index, 1)
    } else {
      nodes.value.splice(index, 1)
    }
    
    // 聚焦到目标节点并将光标移到末尾
    if (targetNode) {
      nextTick(() => {
        focusNodeWithCursorAtEnd(targetNode!.id)
      })
    }
    
    emitContentChange()
  }
}

// 聚焦节点
const focusNode = (nodeId: string) => {
  // 先关闭所有其他节点的编辑状态
  setAllNodesEditing(false)
  
  const node = findNode(nodeId)
  if (node) {
    node.isEditing = true
    // 标记不需要特殊光标定位
    node.cursorPosition = undefined
  }
}

// 聚焦节点并将光标移到末尾
const focusNodeWithCursorAtEnd = (nodeId: string) => {
  // 先关闭所有其他节点的编辑状态
  setAllNodesEditing(false)
  
  const node = findNode(nodeId)
  if (node) {
    node.isEditing = true
    // 标记需要将光标移到末尾
    node.cursorPosition = 'end'
  }
}

// 设置所有节点的编辑状态
const setAllNodesEditing = (isEditing: boolean, nodeList: NodeData[] = nodes.value) => {
  for (const node of nodeList) {
    node.isEditing = isEditing
    setAllNodesEditing(isEditing, node.children)
  }
}

// 获取所有节点的平面数组（按顺序排列）
const getAllNodesFlat = (nodeList: NodeData[] = nodes.value): NodeData[] => {
  const flatNodes: NodeData[] = []
  
  const collectNodes = (nodes: NodeData[]) => {
    for (const node of nodes) {
      flatNodes.push(node)
      if (node.children.length > 0) {
        collectNodes(node.children)
      }
    }
  }
  
  collectNodes(nodeList)
  return flatNodes
}

// 处理节点导航
const handleNavigation = (data: { nodeId: string; direction: 'up' | 'down' }) => {
  const flatNodes = getAllNodesFlat()
  const currentIndex = flatNodes.findIndex(node => node.id === data.nodeId)
  
  if (currentIndex === -1) return
  
  let targetIndex: number
  if (data.direction === 'up') {
    targetIndex = Math.max(0, currentIndex - 1)
  } else {
    targetIndex = Math.min(flatNodes.length - 1, currentIndex + 1)
  }
  
  if (targetIndex !== currentIndex) {
    focusNode(flatNodes[targetIndex].id)
  }
}

// 增加缩进（向右移动一层）
const indentNodeIn = (nodeId: string) => {
  const result = findNodeParent(nodeId)
  if (!result) return
  
  const { parent, index } = result
  const nodeList = parent ? parent.children : nodes.value
  
  // 如果是第一个节点，无法缩进
  if (index === 0) return
  
  // 获取前一个兄弟节点
  const previousSibling = nodeList[index - 1]
  const currentNode = nodeList[index]
  
  // 保存当前节点的编辑状态
  const wasEditing = currentNode.isEditing
  
  // 将当前节点从原位置移除
  nodeList.splice(index, 1)
  
  // 将当前节点添加为前一个兄弟节点的子节点
  previousSibling.children.push(currentNode)
  
  // 恢复编辑状态
  if (wasEditing) {
    nextTick(() => {
      focusNode(nodeId)
    })
  }
  
  emitContentChange()
}

// 减少缩进（向左移动一层）
const indentNodeOut = (nodeId: string) => {
  const result = findNodeParent(nodeId)
  if (!result) return
  
  const { parent, index } = result
  
  // 如果已经是根节点，无法减少缩进
  if (!parent) return
  
  const currentNode = parent.children[index]
  
  // 保存当前节点的编辑状态
  const wasEditing = currentNode.isEditing
  
  // 从当前父节点中移除
  parent.children.splice(index, 1)
  
  // 找到父节点的父节点
  const grandParentResult = findNodeParent(parent.id)
  
  if (grandParentResult) {
    // 有祖父节点，插入到父节点之后
    const { parent: grandParent, index: parentIndex } = grandParentResult
    const grandParentList = grandParent ? grandParent.children : nodes.value
    grandParentList.splice(parentIndex + 1, 0, currentNode)
  } else {
    // 父节点是根节点，插入到根节点列表末尾
    nodes.value.push(currentNode)
  }
  
  // 恢复编辑状态
  if (wasEditing) {
    nextTick(() => {
      focusNode(nodeId)
    })
  }
  
  emitContentChange()
}

// 将节点转换为Markdown
const nodesToMarkdown = (nodeList: NodeData[], level: number = 1): string => {
  let markdown = ''
  
  for (const node of nodeList) {
    if (node.content.trim()) {
      const prefix = '#'.repeat(Math.min(level, 4)) + ' '
      
      if (node.type === 'code' && node.codeLanguage) {
        markdown += `${prefix}${node.content}\n\`\`\`${node.codeLanguage}\n\`\`\`\n\n`
      } else {
        markdown += `${prefix}${node.content}\n\n`
      }
      
      if (node.children.length > 0) {
        markdown += nodesToMarkdown(node.children, level + 1)
      }
    }
  }
  
  return markdown
}

// 从JSON数据解析节点
const parseJsonToNodes = (content: any): NodeData[] => {
  console.log('parseJsonToNodes: input content:', content)
  
  if (!content) {
    console.log('parseJsonToNodes: content is null/undefined')
    return [] // Return empty array instead of default node
  }
  
  if (!content.nodes) {
    console.log('parseJsonToNodes: content.nodes is missing')
    return []
  }
  
  if (!Array.isArray(content.nodes)) {
    console.log('parseJsonToNodes: content.nodes is not an array')
    return []
  }
  
  console.log('parseJsonToNodes: returning nodes:', JSON.parse(JSON.stringify(content.nodes)))
  return content.nodes // Return the actual nodes, even if empty
}

// 发出内容变化事件
const emitContentChange = () => {
  const mindmapData = {
    nodes: nodes.value,
    displayMode: displayMode.value,
    lastModified: new Date().toISOString()
  }
  emit('contentChange', mindmapData)
}

// 保存内容
const saveContent = () => {
  const mindmapData = {
    nodes: nodes.value,
    displayMode: displayMode.value,
    lastModified: new Date().toISOString()
  }
  emit('save', mindmapData)
}

// 切换显示模式
const toggleDisplayMode = async () => {
  if (displayMode.value === 'list') {
    displayMode.value = 'mindmap'
    await nextTick()
    renderMindmap()
  } else {
    displayMode.value = 'list'
    // 清理markmap实例以避免SVG尺寸错误
    if (markmap) {
      markmap.destroy()
      markmap = null
    }
  }
}

// 渲染思维导图
const renderMindmap = async () => {
  if (!svgElement.value || !mindmapContainer.value) return

  try {
    const markdown = nodesToMarkdown(nodes.value)
    if (!markdown.trim()) {
      // 如果没有内容，显示提示
      if (svgElement.value) {
        svgElement.value.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#94a3b8" font-size="16">暂无内容，请先添加节点</text>'
      }
      return
    }
    
    const { root } = transformer.transform(markdown)
    
    // 确保SVG元素有正确的尺寸
    const containerRect = mindmapContainer.value.getBoundingClientRect()
    if (containerRect.width === 0 || containerRect.height === 0) {
      console.warn('Mindmap container has zero dimensions, waiting...')
      setTimeout(() => renderMindmap(), 100)
      return
    }
    
    // 设置SVG尺寸
    svgElement.value.setAttribute('width', containerRect.width.toString())
    svgElement.value.setAttribute('height', containerRect.height.toString())
    
    // 清理现有内容
    svgElement.value.innerHTML = ''
    
    // 重新创建markmap实例
    if (markmap) {
      markmap.destroy()
    }
    
    markmap = Markmap.create(svgElement.value, {
      maxWidth: Math.min(300, containerRect.width * 0.8),
      spacingHorizontal: 80,
      spacingVertical: 10,
    })

    // Force dark theme styles after creation
    setTimeout(() => {
      if (svgElement.value) {
        // Add markmap class to ensure CSS variables are applied
        svgElement.value.classList.add('markmap')
        
        // Force update all text elements
        const textElements = svgElement.value.querySelectorAll('text, foreignObject div')
        textElements.forEach(el => {
          (el as HTMLElement).style.color = '#e2e8f0'
          if (el.tagName === 'text') {
            (el as SVGTextElement).setAttribute('fill', '#e2e8f0')
          }
        })
      }
    }, 10)

    markmap.setData(root)
    
    // 延迟执行fit以确保SVG已正确初始化
    setTimeout(() => {
      if (markmap) {
        markmap.fit()
        
        // Apply dark theme styles after fit
        if (svgElement.value) {
          // Force text color for all text elements
          const allTextElements = svgElement.value.querySelectorAll('text, foreignObject div, foreignObject div div')
          allTextElements.forEach(el => {
            (el as HTMLElement).style.color = '#e2e8f0'
            if (el.tagName === 'text') {
              (el as SVGTextElement).setAttribute('fill', '#e2e8f0')
            }
          })
          
          // Apply CSS variable override directly to the SVG
          svgElement.value.style.setProperty('--markmap-text-color', '#e2e8f0')
        }
      }
    }, 100)
    
  } catch (error) {
    console.error('渲染思维导图失败:', error)
    if (svgElement.value) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      svgElement.value.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#ef4444" font-size="14">渲染失败: ${errorMessage}</text>`
    }
  }
}

// 初始化
const isInitialized = ref(false)
watch(() => props.initialContent, (newContent, oldContent) => {
  // Avoid processing the same content multiple times
  if (newContent === oldContent && isInitialized.value) {
    return
  }
  
  console.log('MindmapEditor: initialContent changed:', newContent)
  if (newContent !== undefined && newContent !== null) {
    // 如果是字符串，尝试解析为JSON；如果是对象，直接使用
    let parsedContent
    if (typeof newContent === 'string') {
      try {
        parsedContent = JSON.parse(newContent)
        console.log('MindmapEditor: Parsed JSON content:', parsedContent)
      } catch {
        parsedContent = null
        console.log('MindmapEditor: Failed to parse JSON')
      }
    } else {
      parsedContent = newContent
      console.log('MindmapEditor: Using object content directly:', parsedContent)
    }
    
    const parsedNodes = parseJsonToNodes(parsedContent)
    console.log('MindmapEditor: Parsed nodes:', parsedNodes)
    
    // Only update if nodes are actually different
    if (JSON.stringify(nodes.value) !== JSON.stringify(parsedNodes)) {
      nodes.value = parsedNodes
      console.log('MindmapEditor: Set nodes.value to:', JSON.parse(JSON.stringify(nodes.value)))
      
      // Don't emit content change on initial load
      if (isInitialized.value) {
        emitContentChange()
      }
    }
    
    // 如果解析后仍然没有节点，才添加根节点
    if (parsedNodes.length === 0) {
      console.log('MindmapEditor: No nodes found, adding root node')
      addRootNode()
    } else {
      console.log('MindmapEditor: Found', parsedNodes.length, 'nodes, not adding root node')
    }
    
    isInitialized.value = true
  }
}, { immediate: true })

onMounted(() => {
  // 只有在没有初始内容且没有节点时才添加根节点
  if (props.initialContent === undefined && !nodes.value.length) {
    addRootNode()
  }
})

// 组件卸载前清理资源
onBeforeUnmount(() => {
  if (markmap) {
    markmap.destroy()
    markmap = null
  }
})
</script>

<style scoped>
.mindmap-editor {
  min-height: 500px;
}

.mindmap-nodes {
  min-height: 400px;
}

/* Custom background color: RGB(34, 47, 68) */
.mindmap-bg {
  background-color: rgb(34, 47, 68) !important;
}

.mindmap-editor svg {
  background: rgb(34, 47, 68) !important;
}

/* Override markmap CSS variables for dark theme */
.mindmap-editor .markmap {
  --markmap-text-color: #e2e8f0 !important; /* Light text for dark background */
  --markmap-code-bg: #1e293b !important; /* Dark code background */
  --markmap-code-color: #e2e8f0 !important; /* Light code text */
  --markmap-circle-open-bg: #334155 !important; /* Dark circle background */
  --markmap-font: 500 14px/20px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  color: #e2e8f0 !important;
}

/* Ensure SVG content is visible on dark background */
.mindmap-editor svg text {
  fill: #e2e8f0 !important; /* Light gray instead of pure white */
  font-size: 14px !important;
  font-weight: 500 !important;
}

.mindmap-editor svg path {
  stroke: #94a3b8 !important; /* Lighter stroke color */
  stroke-width: 2px !important;
}

.mindmap-editor svg circle {
  fill: #3b82f6 !important;
  stroke: #e2e8f0 !important;
  stroke-width: 2px !important;
}

/* Fix for markmap node styling */
.mindmap-editor svg .markmap-node circle {
  fill: #3b82f6 !important;
  stroke: #e2e8f0 !important;
}

/* Force text color in markmap foreign objects */
.mindmap-editor svg .markmap-foreign {
  color: #e2e8f0 !important;
}

.mindmap-editor svg .markmap-foreign div {
  color: #e2e8f0 !important;
  font-weight: 500 !important;
}

/* Override any nested div text color */
.mindmap-editor svg foreignObject div div {
  color: #e2e8f0 !important;
}
</style>