// @/src/composables/useUiState.ts
// Uistate for Home.vue
import { ref, nextTick, onMounted } from 'vue'

export function useUiState() {
  const menuItems = ref([
    { name: '首页', icon: 'House' },
    { name: '媒体库', icon: 'VideoCamera' },
    { name: '笔记', icon: 'Notebook' },
    { name: '存档', icon: 'FolderDelete' },
    { name: '设置', icon: 'Setting' },
  ])

  const currentMenu = ref(0)
  const activeTab = ref<'all' | 'video' | 'audio'>('all')
  const viewType = ref<'grid' | 'list'>('grid')

  const showSearch = ref(false)
  const modalInput = ref<HTMLInputElement>()
  const openSearch = () => {
    showSearch.value = true
    nextTick(() => modalInput.value?.focus())
  }

  const handleMenuItemClick = (idx: number) => {
    // Handle route switch when click different tabs in currentMenu.
    currentMenu.value = idx
  }

  /* ---- global hot-key ---- */
  onMounted(() => {
    window.addEventListener('keydown', (e) => {
      // Ctrl+K for open global search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault()
        openSearch()
      }
    })
  })

  return {
    // state
    menuItems,
    currentMenu,
    activeTab,
    viewType,
    showSearch,
    modalInput,
    // actions
    openSearch,
    handleMenuItemClick,
  }
}
