/** an array of up to 3 URLs (string or null) */
import { ref, computed, watch } from 'vue'
import type { Ref } from 'vue'
import type { Subtitle } from '@/types/subtitle'

export const blobUrls = ref<Array<string | undefined>>([undefined, undefined, undefined])

export type VttMode = 'primary' | 'translation' | 'both'
export type SubtitleSource = Ref<Subtitle[]> | Subtitle[]

/**
 * mode:
 *   'primary'     → uses only the 1st list (raw text)
 *   'translation' → uses only the 1st list (foreign text)
 *   'both'        → uses the 1st list as raw, 2nd list as translation
 *
 * subsLists must be:
 *   [ raw ]                         (for 'primary')
 *   [ translated ]                 (for 'translation')
 *   [ raw, translated ]            (for 'both')
 **/
export function generateVTT(mode: VttMode = 'primary', subsLists: SubtitleSource[]): string {
  // helper to format seconds → “HH:MM:SS.mmm”
  const fmt = (t: number) => new Date(t * 1000).toISOString().substring(11, 23)

  // turn every entry into a Subtitle[] array
  const arrays: Subtitle[][] = subsLists.map((list) => (Array.isArray(list) ? list : list.value))

  // pick the two arrays we care about
  const rawList = arrays[0] || []
  const transList = arrays[1] || []

  // build the VTT
  let vtt = 'WEBVTT\n\n'
  rawList.forEach((rawSub: Subtitle, i: number) => {
    let textBlock: string
    switch (mode) {
      case 'translation':
        // in translation mode we only care about the first list,
        // which callers will pass as the “translated” array
        textBlock = rawSub.text
        break

      case 'both':
        textBlock = [rawSub.text, transList[i]?.text ?? ''].join('\n')
        break

      case 'primary':
      default:
        textBlock = rawSub.text
    }

    vtt += `${fmt(rawSub.start)} --> ${fmt(rawSub.end)}\n` + `${textBlock}\n\n`
  })

  return URL.createObjectURL(new Blob([vtt], { type: 'text/vtt' }))
}
