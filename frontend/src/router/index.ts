import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },

    // /watch/stream/foo.mp4 for HLS playback
    {
      path: '/watch/stream/:basename([^/]+?)\\.:ext(mp4|webm|mkv|m4a|mp3|wav|aac)',
      name: 'watch-stream-video',
      component: () => import('@/views/WatchVideo.vue'),
      props: (route) => ({
        basename: route.params.basename as string,
        ext: route.params.ext as string,
        stream: true,
      }),
    },
    // /watch/foo.mp4 for normal playbook
    {
      path: '/watch/:basename([^/]+)\\.:ext(mp4|webm|mkv|m4a|mp3|wav|aac)',
      name: 'watch-video',
      component: () => import('@/views/WatchVideo.vue'),
      props: (route) => ({
        basename: route.params.basename as string,
        ext: route.params.ext as string,
        stream: false,
      }),
    },

    // /editor/foo.mp4
    {
      path: '/editor/:basename([^/]+)\\.:ext(mp4|webm|mkv|m4a|mp3|wav|aac)',
      name: 'subtitle-editor',
      component: () => import('@/views/SubtitleEditorView.vue'),
      props: (route) => {
        const { basename, ext } = route.params as { basename: string; ext: string }
        return { basename, ext }
      },
    },

    {
      path: '/waveform-test',
      name: 'waveform-test',
      component: () => import('@/views/waveform_test.vue'),
    },
  ],
})

export default router
