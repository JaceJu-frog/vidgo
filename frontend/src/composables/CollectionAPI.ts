import type { Collection, Video } from '@/types/media'

import { BACKEND } from '@/composables/ConfigAPI'

export const CollectionAPI = {
  // Get collection that contains a specific video
  async getVideoCollection(videoId: number): Promise<Collection | null> {
    try {
      // Based on URL pattern: video/<str:action>/<int:video_id>
      const response = await fetch(`${BACKEND}/api/videos/${videoId}/collection`, {
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null // Video is not in any collection
        }
        throw new Error(`Failed to get video collection: ${response.status}`)
      }

      const data = await response.json()
      if (data.success) {
        // Map backend format to frontend format
        return {
          id: data.id,
          name: data.name,
          thumbnail: data.thumbnail,
          type: data.type,
          videos: [], // Will be populated separately
          last_modified: data.last_modified,
        }
      }
      return data
    } catch (error) {
      console.error('Error getting video collection:', error)
      return null
    }
  },

  // Get all videos in a collection
  async getCollectionVideos(collectionId: number): Promise<Video[]> {
    try {
      // Based on URL pattern: collection/<str:action>/<int:collection_id>
      const response = await fetch(`${BACKEND}/api/collection/videos/${collectionId}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to get collection videos: ${response.status}`)
      }

      const data = await response.json()
      if (data.success && data.videos) {
        // Map backend format to frontend format
        return data.videos.map((video: any) => ({
          id: video.id,
          name: video.name,
          url: video.url,
          thumbnail: video.thumbnail,
          length: video.length,
          last_modified: video.last_modified,
          type: video.type,
        }))
      }
      return []
    } catch (error) {
      console.error('Error getting collection videos:', error)
      return []
    }
  },

  // Get collection details by ID
  async getCollectionById(collectionId: number): Promise<Collection | null> {
    try {
      // Based on URL pattern: collection/<str:action>/<int:collection_id>
      const response = await fetch(`${BACKEND}/api/collection/details/${collectionId}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error(`Failed to get collection: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error getting collection:', error)
      return null
    }
  },
}
