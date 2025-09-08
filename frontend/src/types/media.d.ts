// src/types/media.d.ts

export interface Category {
  id: number
  name: string
  items: MediaItem[] | Null
}

export interface Video {
  id: number
  name: string
  thumbnail: string
  url: string
  length: string
  last_modified: string
  description: string
  type: 'video' // ★ 兼容联合类型
}

export interface Collection {
  id: number
  name: string
  videos: Video[]
  type: 'collection' // ★
  thumbnail: string
  cover?: string
  last_modified: string
}

export type MediaItem = Video | Collection // 用于Folder中展示

export interface VideoInfoData {
  id: number
  name: string
  url: string
  description: string
  thumbnailUrl: string
  videoLength: string
  lastModified: string
  rawLang?: string // raw_lang from backend ('en', 'zh', 'jp')
}

// Task Items
export interface SubtitleTaskRow {
  videoName: string
  status: 'Processing' | 'Completed' | 'Waiting' | 'Error'
  progress: number
  result: string
}

export interface DownloadTaskRow {
  videoName: string
  status: 'Processing' | 'Completed' | 'Waiting' | 'Error'
  progress: number
  result: string
}

// Task row items
export interface RequestVideo {
  bvid: string
  url: string
  title: string
  thumbnail: string
  collectionCount: number
  duration: number
  owner: string
  /** 新增：所有分 P 列表 */
  video_data: VideoPart[]
}

/** 单个分 P 的信息 */
export interface VideoPart {
  cid: number
  page: number
  part: string
  duration: number
  // 如果还需要 first_frame / dimension 等字段，按需再补
}
