import { ref, computed } from 'vue'
import { loadUserHiddenCategories, loadHiddenCategories } from './ConfigAPI'
import type { Category } from '@/types/media'

const hiddenCategoryIds = ref<number[]>([])
const systemHiddenCategoryIds = ref<number[]>([])
const userDefinedHiddenCategoryIds = ref<number[]>([])

// Combined hidden categories computed property
const combinedHiddenCategoryIds = computed(() => {
  const combined = [...systemHiddenCategoryIds.value, ...userDefinedHiddenCategoryIds.value]
  return [...new Set(combined)] // Remove duplicates
})

// Load hidden categories from API (with localStorage fallback)
const loadHiddenCategoriesData = async () => {
  try {
    const data = await loadUserHiddenCategories()
    systemHiddenCategoryIds.value = data.hidden_categories
    userDefinedHiddenCategoryIds.value = data.usr_def_hidden_categories
    hiddenCategoryIds.value = data.combined_hidden_categories
  } catch (error) {
    // Fallback to localStorage for unauthenticated users
    const localHidden = loadHiddenCategories()
    systemHiddenCategoryIds.value = []
    userDefinedHiddenCategoryIds.value = localHidden
    hiddenCategoryIds.value = localHidden
  }
}

// Load on first import
loadHiddenCategoriesData()

export function useHiddenCategories() {
  const updateHiddenCategories = (newHiddenIds: number[]) => {
    hiddenCategoryIds.value = newHiddenIds
    // Also update user-defined categories for consistency
    userDefinedHiddenCategoryIds.value = newHiddenIds
  }

  const refreshHiddenCategories = async () => {
    await loadHiddenCategoriesData()
  }

  const filterCategories = (categories: Category[]): Category[] => {
    return categories.filter((category) => !combinedHiddenCategoryIds.value.includes(category.id))
  }

  return {
    hiddenCategoryIds: computed(() => hiddenCategoryIds.value),
    systemHiddenCategoryIds: computed(() => systemHiddenCategoryIds.value),
    userDefinedHiddenCategoryIds: computed(() => userDefinedHiddenCategoryIds.value),
    combinedHiddenCategoryIds,
    updateHiddenCategories,
    refreshHiddenCategories,
    filterCategories,
  }
}
