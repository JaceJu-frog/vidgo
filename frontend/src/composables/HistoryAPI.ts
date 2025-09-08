import type { Video } from '@/types/media'
import { getCSRFToken } from '@/composables/GetCSRFToken'
import { useHiddenCategories } from '@/composables/useHiddenCategories'

import { BACKEND } from '@/composables/ConfigAPI'

export const HistoryAPI = {
  // 获取最近访问的50个视频，按时间排序
  async getRecentVideos(): Promise<Video[]> {
    try {
      const csrfToken = await getCSRFToken()

      // 获取隐藏的分类ID列表
      const { hiddenCategoryIds } = useHiddenCategories()
      const hiddenCategoriesParam =
        hiddenCategoryIds.value.length > 0
          ? `?hidden_categories=${hiddenCategoryIds.value.join(',')}`
          : ''

      const response = await fetch(`${BACKEND}/api/videos/last${hiddenCategoriesParam}`, {
        credentials: 'include',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch recent videos: ${response.status}`)
      }

      const data = await response.json()
      if (data.success && data.videos) {
        // 映射后端格式到前端格式
        return data.videos.map((video: any) => ({
          id: video.id,
          name: video.name,
          url: video.url,
          thumbnail: video.thumbnail,
          length: video.length,
          last_modified: video.last_modified,
          description: video.description,
          type: 'video',
        }))
      }
      return []
    } catch (error) {
      console.error('Error fetching recent videos:', error)
      return []
    }
  },
}
