import type { VideoInfoData } from '@/types/media'
import { BACKEND } from '@/composables/ConfigAPI'

export async function getVideoInfo(filename: string): Promise<VideoInfoData> {
  const res = await fetch(
    `${BACKEND}/api/videos/info/${encodeURIComponent(filename)}`, // note the `/`
    { credentials: 'include' },
  )
  if (!res.ok) {
    console.error('VideoInfo load failed:', res.status, await res.text())
    throw new Error(`HTTP ${res.status}`)
  }
  return (await res.json()) as VideoInfoData
}
