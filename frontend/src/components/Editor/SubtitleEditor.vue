<template>
  <!-- All elements for subtitle Editor,In card vision -->
  <div class="w-full h-full flex flex-col">
    <!-- Subtitle List -->
    <div class="h-full">
      <div class="h-full">
        <div class="p-6 h-full flex flex-col">
          <div class="flex items-center justify-between mb-6 flex-shrink-0">
            <!-- Subtitle List Dropdown -->
            <el-dropdown @command="handleSubtitleFilter" trigger="click">
              <button
                class="flex items-center space-x-2 px-3 py-2 bg-slate-700/50 hover:bg-slate-600/70 text-white rounded-lg transition-colors border border-slate-600/30"
              >
                <span class="text-xl font-semibold">{{ selectedFilterLabel }}</span>
                <el-icon class="ml-2">
                  <ArrowDown />
                </el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu
                  class="rounded-lg shadow-lg border border-slate-600/50 bg-slate-800"
                >
                  <el-dropdown-item
                    command="all"
                    :class="{
                      'bg-blue-600/20 text-blue-400': selectedFilter === 'all',
                      'hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300':
                        selectedFilter !== 'all',
                    }"
                  >
                    {{ t('subtitleList') }}
                  </el-dropdown-item>
                  <div v-if="chapters.length > 0" class="border-t border-slate-600/50 my-1"></div>
                  <el-dropdown-item
                    v-for="chapter in chapters"
                    :key="chapter.id"
                    :command="`chapter-${chapter.id}`"
                    :class="{
                      'bg-blue-600/20 text-blue-400': selectedFilter === `chapter-${chapter.id}`,
                      'hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300':
                        selectedFilter !== `chapter-${chapter.id}`,
                    }"
                  >
                    {{ chapter.title }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <div class="flex space-x-3">
              <!-- 添加字幕的按钮 -->
              <el-tooltip :content="t('addSubtitle')" placement="bottom">
                <button
                  @click="addSubtitle"
                  class="px-4 py-2 bg-blue-600/80 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors backdrop-blur-sm border border-blue-500/30"
                >
                  <el-icon><Plus /></el-icon>
                </button>
              </el-tooltip>

              <!-- 标记开始时间的按钮 -->
              <el-tooltip :content="t('markStartTime')" placement="bottom">
                <button
                  @click="markCurrentAsStart"
                  class="px-4 py-2 bg-green-600/80 hover:bg-green-600 text-white text-sm rounded-lg transition-colors backdrop-blur-sm border border-green-500/30"
                >
                  <FlagTriangleLeft class="w-3 h-3" />
                </button>
              </el-tooltip>

              <!-- 标记结束时间的按钮 -->
              <el-tooltip :content="t('markEndTime')" placement="bottom">
                <button
                  @click="markCurrentAsEnd"
                  class="px-4 py-2 bg-orange-600/80 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors backdrop-blur-sm border border-orange-500/30"
                >
                  <FlagTriangleRight class="w-3 h-3" />
                </button>
              </el-tooltip>

              <!-- 导出按钮 -->
              <el-dropdown @command="handleExport" trigger="click">
                <button
                  class="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 text-slate-300 text-sm rounded-lg transition-colors border border-slate-600/30"
                >
                  <el-icon><Upload /></el-icon> {{ t('export') }}
                </button>
                <template #dropdown>
                  <el-dropdown-menu
                    class="rounded-lg shadow-lg border border-slate-600/50 bg-slate-800"
                  >
                    <div
                      class="text-xs text-white px-4 py-2 bg-slate-700/50 uppercase tracking-wide font-semibold"
                    >
                      {{ t('textKind') }}
                    </div>
                    <el-dropdown-item
                      command="vtt"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      VTT
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="txt"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      TXT
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="srt"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      SRT
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="ass"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      ASS
                    </el-dropdown-item>
                    <div
                      class="text-xs text-white px-4 py-2 bg-slate-700/50 uppercase tracking-wide font-semibold"
                    >
                      {{ t('videoKind') }}
                    </div>
                    <el-dropdown-item
                      command="mp4"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      MP4 (原始)
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="video_with_subtitles"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      MP4 (含字幕)
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="mp3"
                      class="hover:bg-slate-700/50 hover:text-blue-400 transition-colors text-slate-300"
                    >
                      MP3
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <!-- 字幕数量标签 -->
            <span
              class="bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full text-xs font-medium border border-blue-500/30"
            >
              {{ filteredSubtitles.length }} 条
            </span>
          </div>

          <div
            ref="subtitleListContainer"
            @scroll="handleManualScroll"
            class="space-y-4 flex-1 overflow-y-auto custom-scrollbar min-h-0 pr-2 relative"
          >
            <div
              v-for="(s, i) in filteredSubtitles"
              :key="s.originalIndex"
              :ref="
                (el) => {
                  if (el) subtitleRefs[s.originalIndex] = el as HTMLElement
                }
              "
              :class="[
                'p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer backdrop-blur-sm',
                activeSubtitleIndex === s.originalIndex
                  ? 'border-blue-500 bg-blue-900/30 shadow-lg'
                  : currentSubtitleIndex === s.originalIndex
                    ? 'border-green-500 bg-green-900/30 shadow-md'
                    : 'border-slate-600/30 bg-slate-700/20 hover:border-slate-500/50 hover:bg-slate-700/30',
              ]"
              @click="setActiveSubtitle(s.originalIndex)"
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center space-x-2">
                  <span class="text-sm font-medium text-slate-400">#{{ s.originalIndex }}</span>
                  <span
                    :class="[
                      'text-xs px-2 py-1 rounded-full border',
                      getCharacterSpeedColor(calculateCPS(s)),
                    ]"
                  >
                    {{ calculateCPS(s) }} {{ getSpeedUnit(s.text) }}
                  </span>
                </div>
                <div class="flex space-x-1">
                  <button
                    @click.stop="startEdit(s.originalIndex)"
                    class="h-6 w-6 p-0 hover:bg-blue-600/20 rounded flex items-center justify-center transition-colors text-slate-400 hover:text-blue-400"
                  >
                    <Edit3Icon class="w-3 h-3" />
                  </button>
                  <button
                    @click.stop="deleteSubtitle(s.originalIndex)"
                    class="h-6 w-6 p-0 hover:bg-red-600/20 rounded flex items-center justify-center transition-colors text-slate-400 hover:text-red-400"
                  >
                    <Trash2Icon class="w-3 h-3" />
                  </button>
                </div>
              </div>

              <div class="space-y-2">
                <div class="text-xs font-mono text-slate-400 bg-slate-700/30 px-2 py-1 rounded-md">
                  {{ s.start }} → {{ s.end }}
                </div>
                <!-- if Editing index !=i display plain text as below,if Editing index ==i,change into input -->
                <!-- ▸ EDITING STATE  -->
                <template v-if="editSubtitleIndex === s.originalIndex">
                  <!-- 原文 -->
                  <div class="space-y-2">
                    <label class="text-xs text-slate-400 block">{{ t('original') }}:</label>
                    <textarea
                      v-model="rawSubtitle[s.originalIndex].text"
                      class="w-full p-3 bg-slate-700/50 border border-slate-600/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white placeholder-slate-400 resize-none"
                      placeholder="输入字幕原文…"
                      rows="2"
                    />
                  </div>

                  <!-- 译文 -->
                  <div class="space-y-2">
                    <label class="text-xs text-slate-400 block"
                      >{{ t('translatedSubtitle') }}:</label
                    >
                    <textarea
                      v-model="foreignSubtitle[s.originalIndex].text"
                      class="w-full p-3 bg-slate-700/50 border border-slate-600/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white placeholder-slate-400 resize-none"
                      placeholder="输入字幕译文…"
                      rows="2"
                    />
                  </div>

                  <div class="flex gap-2 mt-3">
                    <button
                      @click.stop="saveSubtitle(s.originalIndex)"
                      class="px-3 py-1 bg-blue-600/80 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors"
                    >
                      {{ t('save') }}
                    </button>
                    <button
                      @click.stop="cancelEdit"
                      class="px-3 py-1 bg-slate-600/50 hover:bg-slate-600/70 text-slate-300 text-sm rounded-lg transition-colors"
                    >
                      {{ t('cancel') }}
                    </button>
                  </div>
                </template>

                <!-- ▸ READ-ONLY STATE  -->
                <template v-else>
                  <div class="text-sm text-white leading-relaxed">
                    <span class="text-xs text-slate-400 block mb-1">{{ t('original') }}:</span>
                    {{ s.text }}
                  </div>

                  <div class="border-t border-slate-600/30 my-2" />

                  <div class="text-sm text-slate-200 leading-relaxed">
                    <span class="text-xs text-slate-400 block mb-1"
                      >{{ t('translatedSubtitle') }}:</span
                    >
                    {{ s.translation }}
                  </div>
                </template>
              </div>
            </div>

            <!-- Floating Ball -->
            <div
              v-show="showFloatingBall"
              @click="scrollToCurrentSubtitle"
              class="fixed bottom-6 right-6 w-10 h-10 bg-green-600/70 hover:bg-green-500/80 text-white rounded-full shadow-md cursor-pointer transition-all duration-200 flex items-center justify-center z-50"
            >
              <ArrowBigDown class="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Language Selection Dialog -->
    <div
      v-if="showLanguageDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showLanguageDialog = false"
    >
      <div class="bg-slate-800 rounded-lg shadow-xl w-96 border border-slate-600">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-white mb-4">选择导出语言</h3>
          <div class="space-y-3">
            <button
              @click="exportWithLanguage('raw')"
              class="w-full p-3 text-left bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors border border-slate-600"
            >
              <div class="font-medium">原文字幕</div>
              <div class="text-sm text-slate-300">仅导出视频原始语言字幕</div>
            </button>
            <button
              @click="exportWithLanguage('translated')"
              class="w-full p-3 text-left bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors border border-slate-600"
            >
              <div class="font-medium">译文字幕</div>
              <div class="text-sm text-slate-300">仅导出翻译后的字幕</div>
            </button>
            <button
              @click="exportWithLanguage('both')"
              class="w-full p-3 text-left bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors border border-slate-600"
            >
              <div class="font-medium">双语字幕</div>
              <div class="text-sm text-slate-300">导出原文+译文（原文在上，译文在下）</div>
            </button>
          </div>
          <div class="mt-4 text-right">
            <button
              @click="showLanguageDialog = false"
              class="px-4 py-2 text-slate-300 hover:text-white transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import { useSubtitles } from '@/composables/useSubtitles'
import { blobUrls, generateVTT } from '@/composables/Buildvtt'
import type { Subtitle } from '@/types/subtitle'
import {
  Edit3 as Edit3Icon,
  Trash2 as Trash2Icon,
  FlagTriangleLeft,
  FlagTriangleRight,
  ArrowBigDown,
} from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { loadConfig } from '@/composables/ConfigAPI'
import { useI18n } from 'vue-i18n'
import { ChapterAPI, type Chapter } from '@/composables/ChapterAPI'
import { getCookie } from '@/composables/GetCSRFToken'

const { subtitles, linkSubtitles, fetchSubtitle } = useSubtitles()
import { BACKEND } from '@/composables/ConfigAPI'

const props = defineProps<{
  currentTime: number
  id: number
  rawLang?: string
  videoName?: string
  duration: number
  /** vue-i18n composer instance for translations */
  i18n?: ReturnType<typeof useI18n>
}>()

// i18n composer (use provided one or fall back to local)
const i18nComposer = props.i18n ?? useI18n()
const t = i18nComposer.t as any
const locale = i18nComposer.locale

const rawSubtitle = ref<Subtitle[]>(subtitles.value)
const foreignSubtitle = ref<Subtitle[]>(subtitles.value)

const bilingualSubs = computed(() =>
  rawSubtitle.value.map((orig, i) => ({
    start: orig.start,
    end: orig.end,
    text: orig.text,
    translation: foreignSubtitle.value[i]?.text ?? '',
    originalIndex: i,
  })),
)

// Chapter filtering state
const chapters = ref<Chapter[]>([])
const selectedFilter = ref('all')
const selectedFilterLabel = computed(() => {
  if (selectedFilter.value === 'all') return t('subtitleList')
  const chapter = chapters.value.find((c) => selectedFilter.value === `chapter-${c.id}`)
  return chapter ? chapter.title : t('subtitleList')
})

// Filtered subtitles based on selected chapter
const filteredSubtitles = computed(() => {
  if (selectedFilter.value === 'all') {
    return bilingualSubs.value
  }

  // Find selected chapter
  const chapterId = selectedFilter.value.replace('chapter-', '')
  const currentChapterIndex = chapters.value.findIndex((c) => c.id === chapterId)

  if (currentChapterIndex === -1) return bilingualSubs.value

  const currentChapter = chapters.value[currentChapterIndex]
  const nextChapter = chapters.value[currentChapterIndex + 1]

  // Calculate end time: next chapter's start time or video duration
  const endTime = nextChapter ? nextChapter.startTime : props.duration

  // Filter subtitles by chapter time range
  return bilingualSubs.value.filter(
    (sub) => sub.start >= currentChapter.startTime && sub.start < endTime,
  )
})

function handleExport(command: string) {
  if (['vtt', 'srt', 'txt', 'ass'].includes(command)) {
    pendingExportFormat.value = command
    showLanguageDialog.value = true
  } else if (command === 'video_with_subtitles') {
    // 导出带字幕硬嵌入的MP4视频
    pendingExportFormat.value = 'video_with_subtitles'
    showLanguageDialog.value = true
  } else {
    switch (command) {
      case 'mp4':
        downloadVideoFile('mp4')
        break
      case 'mp3':
        downloadVideoFile('mp3')
        break
    }
  }
}

// Language selection function
function exportWithLanguage(languageType: 'raw' | 'translated' | 'both') {
  showLanguageDialog.value = false

  const format = pendingExportFormat.value
  switch (format) {
    case 'vtt':
      exportVTT(languageType)
      break
    case 'srt':
      exportSRT(languageType)
      break
    case 'txt':
      exportTXT(languageType)
      break
    case 'ass':
      exportASS(languageType)
      break
    case 'video_with_subtitles':
      exportVideoWithSubtitles(languageType)
      break
  }
}

// Export functions
function exportVTT(languageType: 'raw' | 'translated' | 'both' = 'both') {
  const fmt = (t: number) => new Date(t * 1000).toISOString().substring(11, 23)

  let vtt = 'WEBVTT\n\n'
  bilingualSubs.value.forEach((sub) => {
    let textBlock = ''
    switch (languageType) {
      case 'raw':
        textBlock = sub.text
        break
      case 'translated':
        textBlock = sub.translation || sub.text
        break
      case 'both':
        textBlock = sub.translation ? `${sub.text}\n${sub.translation}` : sub.text
        break
    }
    vtt += `${fmt(sub.start)} --> ${fmt(sub.end)}\n${textBlock}\n\n`
  })

  const suffix =
    languageType === 'raw' ? '_raw' : languageType === 'translated' ? '_translated' : ''
  downloadFile(vtt, `${props.videoName || 'subtitles'}${suffix}.vtt`, 'text/vtt')
  ElMessage.success('VTT字幕导出成功')
}

function exportSRT(languageType: 'raw' | 'translated' | 'both' = 'both') {
  const fmt = (t: number) => {
    const date = new Date(t * 1000)
    return date.toISOString().substring(11, 23).replace('.', ',')
  }

  let srt = ''
  bilingualSubs.value.forEach((sub, i) => {
    let textBlock = ''
    switch (languageType) {
      case 'raw':
        textBlock = sub.text
        break
      case 'translated':
        textBlock = sub.translation || sub.text
        break
      case 'both':
        textBlock = sub.translation ? `${sub.text}\n${sub.translation}` : sub.text
        break
    }
    srt += `${i + 1}\n${fmt(sub.start)} --> ${fmt(sub.end)}\n${textBlock}\n\n`
  })

  const suffix =
    languageType === 'raw' ? '_raw' : languageType === 'translated' ? '_translated' : ''
  downloadFile(srt, `${props.videoName || 'subtitles'}${suffix}.srt`, 'text/srt')
  ElMessage.success('SRT字幕导出成功')
}

function exportTXT(languageType: 'raw' | 'translated' | 'both' = 'both') {
  let txt = ''
  bilingualSubs.value.forEach((sub) => {
    let textBlock = ''
    switch (languageType) {
      case 'raw':
        textBlock = sub.text
        break
      case 'translated':
        textBlock = sub.translation || sub.text
        break
      case 'both':
        textBlock = sub.translation ? `${sub.text}\n${sub.translation}` : sub.text
        break
    }
    txt += `${textBlock}\n\n`
  })

  const suffix =
    languageType === 'raw' ? '_raw' : languageType === 'translated' ? '_translated' : ''
  downloadFile(txt, `${props.videoName || 'subtitles'}${suffix}.txt`, 'text/plain')
  ElMessage.success('TXT文本导出成功')
}

async function exportASS(languageType: 'raw' | 'translated' | 'both' = 'both') {
  // Load subtitle styling configuration
  let subtitleSettings: any = {}
  try {
    const config = await loadConfig()
    subtitleSettings = config
  } catch (error) {
    console.warn('Failed to load subtitle settings, using defaults:', error)
    // Default settings fallback
    subtitleSettings = {
      fontFamily: '宋体',
      fontSize: 18,
      fontColor: '#ea9749',
      fontWeight: '400',
      backgroundColor: '#000000',
      backgroundStyle: 'semi-transparent',
      borderRadius: 4,
      textShadow: false,
      bottomDistance: 80,
      foreignFontFamily: 'Arial',
      foreignFontSize: 16,
      foreignFontColor: '#ffffff',
      foreignFontWeight: '400',
      foreignBackgroundColor: '#000000',
      foreignBackgroundStyle: 'semi-transparent',
      foreignBorderRadius: 4,
      foreignTextShadow: false,
      foreignBottomDistance: 120,
    }
  }

  // Get video dimensions
  let width = 1920,
    height = 1080 // Default resolution
  try {
    const response = await fetch(`${BACKEND}/api/videos/${props.id}/get_dimensions`, {
      method: 'GET',
      credentials: 'include',
    })
    const result = await response.json()
    if (result.success) {
      width = result.width
      height = result.height
      console.log(`Using video dimensions: ${width}x${height}`)
    } else {
      console.warn('Failed to get video dimensions:', result.error)
    }
  } catch (error) {
    console.warn('Error getting video dimensions:', error)
  }

  const fmt = (t: number) => {
    const totalSeconds = Math.floor(t)
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60
    const centiseconds = Math.floor((t - totalSeconds) * 100)
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`
  }

  // Convert hex color to ASS color format (BGR)
  const hexToAssColor = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `&H00${b.toString(16).padStart(2, '0').toUpperCase()}${g.toString(16).padStart(2, '0').toUpperCase()}${r.toString(16).padStart(2, '0').toUpperCase()}`
  }

  // Generate ASS header with styling (use actual video resolution info for proper scaling)
  let ass = `[Script Info]
Title: ${props.videoName || 'Exported Subtitles'}
ScriptType: v4.00+
PlayResX: ${width}
PlayResY: ${height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
`

  // Add styles based on language type
  if (languageType === 'raw' || languageType === 'both') {
    const rawColor = hexToAssColor(
      subtitleSettings.font_color || subtitleSettings.fontColor || '#ea9749',
    )
    const rawBgColor = hexToAssColor(
      subtitleSettings.background_color || subtitleSettings.backgroundColor || '#000000',
    )
    const rawFontSize = subtitleSettings.font_size || subtitleSettings.fontSize || 18
    const rawBold =
      parseInt(subtitleSettings.font_weight || subtitleSettings.fontWeight || '400') > 500 ? -1 : 0
    const rawShadow = subtitleSettings.text_shadow || subtitleSettings.textShadow ? 2 : 0
    const rawMarginV = subtitleSettings.bottom_distance || subtitleSettings.bottomDistance || 80

    // Add text stroke (outline) support
    const rawStroke =
      subtitleSettings.text_stroke || subtitleSettings.textStroke
        ? subtitleSettings.text_stroke_width || subtitleSettings.textStrokeWidth || 2
        : 0
    const rawStrokeColor =
      subtitleSettings.text_stroke || subtitleSettings.textStroke
        ? hexToAssColor(
            subtitleSettings.text_stroke_color || subtitleSettings.textStrokeColor || '#000000',
          )
        : '&H00000000'

    ass += `Style: Raw,${subtitleSettings.font_family || subtitleSettings.fontFamily || '宋体'},${rawFontSize},${rawColor},${rawColor},${rawStrokeColor},${rawBgColor},${rawBold},0,0,0,100,100,0,0,1,${rawStroke},${rawShadow},2,0,0,${rawMarginV},1\n`
  }

  if (languageType === 'translated' || languageType === 'both') {
    const transColor = hexToAssColor(
      subtitleSettings.foreign_font_color || subtitleSettings.foreignFontColor || '#ffffff',
    )
    const transBgColor = hexToAssColor(
      subtitleSettings.foreign_background_color ||
        subtitleSettings.foreignBackgroundColor ||
        '#000000',
    )
    const transFontSize =
      subtitleSettings.foreign_font_size || subtitleSettings.foreignFontSize || 16
    const transBold =
      parseInt(
        subtitleSettings.foreign_font_weight || subtitleSettings.foreignFontWeight || '400',
      ) > 500
        ? -1
        : 0
    const transShadow =
      subtitleSettings.foreign_text_shadow || subtitleSettings.foreignTextShadow ? 2 : 0
    const transMarginV =
      subtitleSettings.foreign_bottom_distance || subtitleSettings.foreignBottomDistance || 120

    // Add text stroke (outline) support
    const transStroke =
      subtitleSettings.foreign_text_stroke || subtitleSettings.foreignTextStroke
        ? subtitleSettings.foreign_text_stroke_width || subtitleSettings.foreignTextStrokeWidth || 2
        : 0
    const transStrokeColor =
      subtitleSettings.foreign_text_stroke || subtitleSettings.foreignTextStroke
        ? hexToAssColor(
            subtitleSettings.foreign_text_stroke_color ||
              subtitleSettings.foreignTextStrokeColor ||
              '#000000',
          )
        : '&H00000000'

    ass += `Style: Foreign,${subtitleSettings.foreign_font_family || subtitleSettings.foreignFontFamily || 'Arial'},${transFontSize},${transColor},${transColor},${transStrokeColor},${transBgColor},${transBold},0,0,0,100,100,0,0,1,${transStroke},${transShadow},2,0,0,${transMarginV},1\n`
  }

  ass += `
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`

  // Add dialogue lines
  bilingualSubs.value.forEach((sub) => {
    const startTime = fmt(sub.start)
    const endTime = fmt(sub.end)

    switch (languageType) {
      case 'raw':
        ass += `Dialogue: 0,${startTime},${endTime},Raw,,0,0,0,,${sub.text}\n`
        break
      case 'translated':
        const translatedText = sub.translation || sub.text
        ass += `Dialogue: 0,${startTime},${endTime},Foreign,,0,0,0,,${translatedText}\n`
        break
      case 'both':
        ass += `Dialogue: 0,${startTime},${endTime},Raw,,0,0,0,,${sub.text}\n`
        if (sub.translation) {
          ass += `Dialogue: 0,${startTime},${endTime},Foreign,,0,0,0,,${sub.translation}\n`
        }
        break
    }
  })

  const suffix =
    languageType === 'raw' ? '_raw' : languageType === 'translated' ? '_translated' : ''
  downloadFile(ass, `${props.videoName || 'subtitles'}${suffix}.ass`, 'text/ass')
  ElMessage.success('ASS字幕导出成功')
}
// Export video with embedded subtitles
async function exportVideoWithSubtitles(languageType: 'raw' | 'translated' | 'both' = 'raw') {
  try {
    // 检查是否有相应的字幕文件
    if (languageType === 'raw' && rawSubtitle.value.length === 0) {
      ElMessage.error('没有找到原文字幕，无法导出')
      return
    }
    if (languageType === 'translated' && foreignSubtitle.value.length === 0) {
      ElMessage.error('没有找到译文字幕，无法导出')
      return
    }
    if (
      languageType === 'both' &&
      (rawSubtitle.value.length === 0 || foreignSubtitle.value.length === 0)
    ) {
      ElMessage.error('原文或译文字幕缺失，无法导出双语字幕')
      return
    }

    const response = await fetch(`${BACKEND}/api/export/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'include',
      body: JSON.stringify({
        video_id: props.id,
        subtitle_type: languageType,
      }),
    })

    const result = await response.json()

    if (result.success) {
      ElMessage.success('视频导出任务已添加到队列，请在主页查看进度')
    } else {
      ElMessage.error(result.message || '导出任务添加失败')
    }
  } catch (error: any) {
    console.error('Export video with subtitles error:', error)
    ElMessage.error('导出任务添加失败：' + (error.message || '网络错误'))
  }
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Progressive video/audio file download with streaming
async function downloadVideoFile(format: 'mp4' | 'mp3') {
  if (!props.id || props.id <= 0) {
    ElMessage.error('无效的视频ID')
    return
  }

  const videoName = props.videoName || `video_${props.id}`
  const filename = `${videoName}.${format}`

  try {
    // Show loading message
    const loadingMessage = ElMessage.info({
      message: `正在准备${format.toUpperCase()}文件下载...`,
      duration: 0, // Don't auto close
    })

    // Check file availability first
    const checkResponse = await fetch(`${BACKEND}/api/videos/download/${props.id}/${format}`, {
      method: 'HEAD',
      credentials: 'include',
    })

    if (!checkResponse.ok) {
      loadingMessage.close()
      if (checkResponse.status === 404) {
        ElMessage.error(`${format.toUpperCase()}文件不存在`)
      } else if (checkResponse.status === 400) {
        ElMessage.error('音频文件无法导出为MP4格式，请选择MP3')
      } else {
        ElMessage.error(`文件检查失败: ${checkResponse.status}`)
      }
      return
    }

    // Get file size from headers
    const contentLength = checkResponse.headers.get('content-length')
    const totalSize = contentLength ? parseInt(contentLength) : 0

    loadingMessage.close()

    // Start streaming download
    const downloadResponse = await fetch(`${BACKEND}/api/videos/download/${props.id}/${format}`, {
      method: 'GET',
      credentials: 'include',
    })

    if (!downloadResponse.ok) {
      throw new Error(`Download failed: ${downloadResponse.status}`)
    }

    if (!downloadResponse.body) {
      throw new Error('No response body for streaming')
    }

    // Progressive download with progress tracking
    const reader = downloadResponse.body.getReader()
    const chunks: Uint8Array[] = []
    let downloadedSize = 0

    // Show download progress
    let progressMessage = ElMessage.info({
      message: `正在下载${format.toUpperCase()}: 0%`,
      duration: 0,
    })

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        chunks.push(value)
        downloadedSize += value.length

        // Update progress
        if (totalSize > 0) {
          const progress = Math.round((downloadedSize / totalSize) * 100)
          progressMessage.close()
          progressMessage = ElMessage.info({
            message: `正在下载${format.toUpperCase()}: ${progress}% (${formatFileSize(downloadedSize)}/${formatFileSize(totalSize)})`,
            duration: 0,
          })
        } else {
          progressMessage.close()
          progressMessage = ElMessage.info({
            message: `正在下载${format.toUpperCase()}: ${formatFileSize(downloadedSize)}`,
            duration: 0,
          })
        }
      }
    } finally {
      reader.releaseLock()
      progressMessage.close()
    }

    // Combine chunks and create blob
    const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
    const combinedArray = new Uint8Array(totalLength)
    let offset = 0

    for (const chunk of chunks) {
      combinedArray.set(chunk, offset)
      offset += chunk.length
    }

    // Create blob and download
    const mimeType = format === 'mp4' ? 'video/mp4' : 'audio/mpeg'
    const blob = new Blob([combinedArray], { type: mimeType })
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    ElMessage.success(`${format.toUpperCase()}文件下载成功: ${filename}`)
  } catch (error: any) {
    console.error(`${format} download error:`, error)
    ElMessage.error(`下载失败: ${error?.message || '未知错误'}`)
  }
}

// Helper function to format file size
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(async () => {
  tryInit(props.id) // 首次挂载时先试一次

  // Load chapters for filtering
  await loadChapters()

  // Set up 2-second interval for current subtitle detection
  updateCurrentSubtitleInterval = window.setInterval(() => {
    updateCurrentSubtitle()
  }, 2000)

  // Initial check
  updateCurrentSubtitle()
})

onUnmounted(() => {
  if (updateCurrentSubtitleInterval) {
    window.clearInterval(updateCurrentSubtitleInterval)
  }
})

watch(
  () => props.id,
  (newId) => {
    tryInit(newId) // id 变化时再试
    loadChapters() // 加载新视频的章节
  },
)

// Watch currentTime changes for immediate response (in addition to 5-second interval)
watch(
  () => props.currentTime,
  () => {
    updateCurrentSubtitle()
  },
)

// Watch bilingualSubs changes to update refs
watch(
  () => bilingualSubs.value,
  () => {
    nextTick(() => {
      updateCurrentSubtitle()
    })
  },
  { deep: true },
)

async function tryInit(id: number) {
  if (id <= 0) return // 忽略 -1 / 0 / 无效 id

  // 使用视频的原始语言和用户界面语言（与SubtitlePanel.vue一致）
  const primaryLang = props.rawLang || 'zh' // 原文语言（视频原始语言）
  const foreignLang = locale.value as string // 译文语言（i18n locale）

  console.log('Loading subtitles with languages:', {
    primaryLang,
    foreignLang,
    rawLang: props.rawLang,
  })

  // 真正获取字幕
  try {
    rawSubtitle.value = await fetchSubtitle(id, primaryLang) // 原文字幕
    console.log('Raw subtitles loaded:', rawSubtitle.value.length, 'items')
  } catch (error) {
    console.warn(`Raw subtitles (${primaryLang}) not found:`, error)
    rawSubtitle.value = []
  }

  try {
    foreignSubtitle.value = await fetchSubtitle(id, foreignLang) // 译文字幕
    console.log('Translation subtitles loaded:', foreignSubtitle.value.length, 'items')
  } catch (error) {
    console.warn(`Translation subtitles (${foreignLang}) not found:`, error)
    foreignSubtitle.value = []
  }

  blobUrls.value[0] = generateVTT('primary', [rawSubtitle.value])
  blobUrls.value[1] = generateVTT('translation', [foreignSubtitle.value])
  blobUrls.value[2] = generateVTT('both', [rawSubtitle.value, foreignSubtitle.value])
}

// Load chapters for the current video
async function loadChapters() {
  if (props.id && props.id > 0) {
    try {
      chapters.value = await ChapterAPI.loadChapters(props.id)
      console.log('Loaded chapters for filtering:', chapters.value)
    } catch (error) {
      console.error('Failed to load chapters:', error)
      chapters.value = []
    }
  }
}

/** which subtitle row is highlighted/being edited **/
// 同时编辑 译文和原文字幕
const activeSubtitleIndex = ref<number | null>(null)
const editSubtitleIndex = ref<number | null>(null)

// Current subtitle detection and floating ball
const currentSubtitleIndex = ref<number | null>(null)
const showFloatingBall = ref(false)
const subtitleRefs: { [key: number]: HTMLElement } = {}
const subtitleListContainer = ref<HTMLElement | null>(null)
let updateCurrentSubtitleInterval: number | null = null

// Manual scroll detection
const isUserManualScrolling = ref(false)

// Language selection dialog
const showLanguageDialog = ref(false)
const pendingExportFormat = ref<string>('')

// Chapter filter handler
function handleSubtitleFilter(command: string) {
  selectedFilter.value = command
}

const emit = defineEmits(['seek-time', 'update-bloburls', 'subs-loaded'])

// Function to update subtitle timing from external sources (like waveform)
function updateSubtitleTiming(index: number, newStart: number, newEnd: number) {
  if (index >= 0 && index < rawSubtitle.value.length) {
    rawSubtitle.value[index].start = newStart
    rawSubtitle.value[index].end = newEnd
  }
  if (index >= 0 && index < foreignSubtitle.value.length) {
    foreignSubtitle.value[index].start = newStart
    foreignSubtitle.value[index].end = newEnd
  }
}

// Expose the function for parent component
defineExpose({
  updateSubtitleTiming,
})

/* build a fresh VTT every time the array changes */
// 1) WATCH THE RAW TRACK (index 0)
watch(
  () => rawSubtitle.value,
  (newRaw, oldRaw) => {
    if (oldRaw && blobUrls.value[0]) URL.revokeObjectURL(blobUrls.value[0])

    blobUrls.value[0] = generateVTT('primary', [newRaw])
    blobUrls.value[2] = generateVTT('both', [newRaw, foreignSubtitle.value]) // ✨ .value
    console.log('emit update bloburls signal')
    emit('update-bloburls', blobUrls.value)
    emit('subs-loaded', rawSubtitle.value)
  },
  { deep: true },
)
// 2) WATCH THE Foreign TRACK (index 1)
watch(
  () => foreignSubtitle.value,
  (newTrans, oldTrans) => {
    if (oldTrans && blobUrls.value[1]) URL.revokeObjectURL(blobUrls.value[1])

    blobUrls.value[1] = generateVTT('translation', [newTrans])
    blobUrls.value[2] = generateVTT('both', [rawSubtitle.value, newTrans]) // ✨ .value
    emit('update-bloburls', blobUrls.value)
  },
  { deep: true },
)

function setActiveSubtitle(index: number) {
  // highlight the row

  activeSubtitleIndex.value = index
  console.log(index)
  console.log('activeSubtitleIndex.value', activeSubtitleIndex.value)
  // find the clicked subtitle safely
  const subtitle1 = rawSubtitle.value[index]
  // const subtitle2 = foreignSubtitle.value[index] // Removed unused variable
  if (!subtitle1) return // guard for out-of-range clicks

  // seek the player to that subtitle’s start time
  emit('seek-time', subtitle1.start)
}

// function isCurrentSubtitle(subtitle) {
//   return props.currentTime >= subtitle.start && props.currentTime <= subtitle.end
// }

function calculateCPS(subtitle: any) {
  if (!subtitle.text) return 0
  const duration = subtitle.end - subtitle.start
  if (duration <= 0) return 0

  // 判断是否为英文文本（检查是否主要包含英文字符）
  const englishChars = subtitle.text.match(/[a-zA-Z]/g)
  const totalChars = subtitle.text.replace(/\s/g, '').length
  const isEnglish = englishChars && englishChars.length / totalChars > 0.5

  let count: number
  if (isEnglish) {
    // 英文：按单词数计算
    const words = subtitle.text
      .trim()
      .split(/\s+/)
      .filter((word: string) => word.length > 0)
    count = words.length
  } else {
    // 中文等其他语言：按字符数计算（去除空格）
    count = subtitle.text.replace(/\s/g, '').length
  }

  return Math.round((count / duration) * 10) / 10
}

function getCharacterSpeedColor(speed: number) {
  if (speed <= 2.5) return 'bg-green-600/20 text-green-400 border-green-500/30'
  if (speed <= 3.0) return 'bg-yellow-600/20 text-yellow-400 border-yellow-500/30'
  return 'bg-red-600/20 text-red-400 border-red-500/30'
}

function getSpeedUnit(text: string) {
  if (!text) return '字/秒'

  // 判断是否为英文文本（检查是否主要包含英文字符）
  const englishChars = text.match(/[a-zA-Z]/g)
  const totalChars = text.replace(/\s/g, '').length
  const isEnglish = englishChars && englishChars.length / totalChars > 0.5

  return isEnglish ? '词/秒' : '字/秒'
}

async function saveSubtitle(index: number) {
  const rawChanged = rawSubtitle.value[index].text !== rawBeforeEdit.value
  const tranChanged = foreignSubtitle.value[index].text !== transBeforeEdit.value

  // 只把有改动的字幕推到后端
  const primaryLang = props.rawLang || 'zh'
  const foreignLang = locale.value as string

  if (rawChanged) {
    await linkSubtitles(props.id, primaryLang, rawSubtitle)
  }
  if (tranChanged) {
    await linkSubtitles(props.id, foreignLang, foreignSubtitle)
  }

  editSubtitleIndex.value = null
}

function cancelEdit() {
  editSubtitleIndex.value = null
}

function addSubtitle() {
  // 查找离当前时间最近且大于当前时间的字幕开始时间
  let endTime: number

  const nextSubtitle = rawSubtitle.value.find((sub) => sub.start > props.currentTime)
  if (nextSubtitle) {
    const timeDiff = nextSubtitle.start - props.currentTime
    if (timeDiff <= 30) {
      endTime = nextSubtitle.start
    } else {
      // 时间差大于30秒，使用默认值
      endTime = Math.min(props.currentTime + 5, props.duration)
    }
  } else {
    // 没有找到下一个字幕，使用默认值
    endTime = Math.min(props.currentTime + 5, props.duration)
  }

  const newSubtitle = {
    start: props.currentTime,
    end: endTime,
    text: '',
  }
  rawSubtitle.value.push(newSubtitle)
  foreignSubtitle.value.push(newSubtitle)

  // 排序后重新找到新字幕的索引
  rawSubtitle.value.sort((a, b) => a.start - b.start)
  foreignSubtitle.value.sort((a, b) => a.start - b.start)

  // 找到新添加字幕的索引
  const newIndex = rawSubtitle.value.findIndex(
    (sub) => sub.start === props.currentTime && sub.end === endTime,
  )
  activeSubtitleIndex.value = newIndex

  ElMessage.success('已添加新字幕')
}

function deleteSubtitle(index: number) {
  // 1 actually remove the cue
  console.log('delete index :', index)
  rawSubtitle.value.splice(index, 1)
  foreignSubtitle.value.splice(index, 1)

  // 2 reset or shift any indices that depended on the old list
  if (activeSubtitleIndex.value === index) {
    activeSubtitleIndex.value = null
  } else if (activeSubtitleIndex.value !== null && activeSubtitleIndex.value > index) {
    activeSubtitleIndex.value-- // shift down by one
  }

  if (editSubtitleIndex.value === index) {
    editSubtitleIndex.value = null
  } else if (editSubtitleIndex.value !== null && editSubtitleIndex.value > index) {
    editSubtitleIndex.value--
  }
}

function markCurrentAsStart() {
  if (activeSubtitleIndex.value == null) return
  rawSubtitle.value[activeSubtitleIndex.value].start = props.currentTime
  foreignSubtitle.value[activeSubtitleIndex.value].start = props.currentTime
}

function markCurrentAsEnd() {
  if (activeSubtitleIndex.value == null) return
  rawSubtitle.value[activeSubtitleIndex.value].end = props.currentTime
  foreignSubtitle.value[activeSubtitleIndex.value].end = props.currentTime
}

const rawBeforeEdit = ref('') // 原文旧值
const transBeforeEdit = ref('') // 译文旧值
function startEdit(i: number) {
  // 把当前字幕内容缓存下来
  rawBeforeEdit.value = rawSubtitle.value[i].text
  transBeforeEdit.value = foreignSubtitle.value[i].text
  editSubtitleIndex.value = i
}

// Current subtitle detection
function updateCurrentSubtitle() {
  const currentTime = props.currentTime
  let found = false

  for (let i = 0; i < bilingualSubs.value.length; i++) {
    const sub = bilingualSubs.value[i]
    if (currentTime >= sub.start && currentTime <= sub.end) {
      currentSubtitleIndex.value = sub.originalIndex
      found = true
      break
    }
  }

  if (!found) {
    currentSubtitleIndex.value = null
  }

  // Auto-scroll to current subtitle if not manually scrolling
  if (!isUserManualScrolling.value && currentSubtitleIndex.value !== null) {
    scrollToSubtitleSilently(currentSubtitleIndex.value)
  }

  // Check if current subtitle is visible
  checkFloatingBallVisibility()
}

// Check if current subtitle is in viewport
function checkFloatingBallVisibility() {
  if (currentSubtitleIndex.value === null || !subtitleListContainer.value) {
    showFloatingBall.value = false
    return
  }

  const currentSubtitleEl = subtitleRefs[currentSubtitleIndex.value]
  if (!currentSubtitleEl) {
    showFloatingBall.value = false
    return
  }

  const containerRect = subtitleListContainer.value.getBoundingClientRect()
  const subtitleRect = currentSubtitleEl.getBoundingClientRect()

  // Check if subtitle is fully visible within the container
  const isVisible =
    subtitleRect.top >= containerRect.top && subtitleRect.bottom <= containerRect.bottom

  showFloatingBall.value = !isVisible
}

// Scroll to subtitle silently (for auto-scroll)
function scrollToSubtitleSilently(index: number) {
  if (!subtitleListContainer.value) {
    return
  }

  const subtitleEl = subtitleRefs[index]
  if (!subtitleEl) {
    return
  }

  // Check if subtitle is already visible
  const containerRect = subtitleListContainer.value.getBoundingClientRect()
  const subtitleRect = subtitleEl.getBoundingClientRect()

  const isVisible =
    subtitleRect.top >= containerRect.top && subtitleRect.bottom <= containerRect.bottom

  if (!isVisible) {
    subtitleEl.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest',
    })
  }
}

// Scroll to current subtitle (for floating ball click)
function scrollToCurrentSubtitle() {
  if (currentSubtitleIndex.value === null || !subtitleListContainer.value) {
    return
  }

  // Reset manual scroll status
  isUserManualScrolling.value = false

  const currentSubtitleEl = subtitleRefs[currentSubtitleIndex.value]
  if (!currentSubtitleEl) {
    return
  }

  // Scroll to the element
  currentSubtitleEl.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
    inline: 'nearest',
  })

  // Hide floating ball after scrolling
  showFloatingBall.value = false

  // Briefly highlight the subtitle by making it active
  const previousActive = activeSubtitleIndex.value
  activeSubtitleIndex.value = currentSubtitleIndex.value

  // Reset to previous active after 1 second
  setTimeout(() => {
    activeSubtitleIndex.value = previousActive
  }, 1000)
}

// Handle manual scroll detection
function handleManualScroll() {
  // Set manual scrolling state - will persist until floating ball is clicked
  isUserManualScrolling.value = true
}

// const subtitleStyle = computed(() => ({
//   fontFamily: `'${subtitleFont.value}'`,
//   color: subtitleColor.value,
//   fontSize: `${subtitleSize.value}px`,
// }))

// function updateSubtitleStyle() {
//   try {
//     localStorage.setItem('subtitleFont', subtitleFont.value)
//     localStorage.setItem('subtitleColor', subtitleColor.value)
//     localStorage.setItem('subtitleSize', subtitleSize.value)
//   } catch (e) {
//     console.error('Failed to save subtitle preferences:', e)
//   }
// }
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease forwards;
  opacity: 0;
}

/* Custom textarea styles */
:deep(.el-textarea__inner) {
  border: 1px solid #e5e7eb !important;
  border-radius: 0.5rem !important;
  transition: all 0.2s !important;
  font-family: inherit !important;
  padding: 0.75rem !important;
}

:deep(.el-textarea__inner:focus) {
  border-color: #4361ee !important;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2) !important;
}

/* 自定义滚动条 - 与背景相融 */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.4); /* slate-800 with opacity */
  border-radius: 4px;
  margin: 4px 0;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.6); /* slate-600 with opacity */
  border-radius: 4px;
  border: 1px solid rgba(51, 65, 85, 0.3); /* slate-700 border */
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.8); /* slate-500 on hover */
  border-color: rgba(71, 85, 105, 0.5);
}

.custom-scrollbar::-webkit-scrollbar-thumb:active {
  background: rgba(100, 116, 139, 1); /* slate-500 solid when active */
}
</style>
