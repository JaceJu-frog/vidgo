export interface Subtitle {
  start: number
  end: number
  text: string
}

export interface SubtitleBilingual extends Subtitle {
  translation?: string
  editing?: boolean
  translationEditing?: boolean
}
