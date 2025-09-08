# 视频介绍:
23:00 ：开始介绍vue项目的基本设置

# 安装方式。

# 一些需要注意的地方:
整体架构中的重要文件为:
```
|--src
|   |componets\
|   |BackButton.vue
|   |Card.vue
|   |Hero.vue
|   |HomeCards.vue
|   |JobListing.vue
|   |JobListings.vue
|   |Navbar.vue
|   |
|   |router\
|   |index.js //Controls which view to display,like urls.py in django. 
|   |
|   |
|   |views\
|   |AddJobView.vue
|   |EditJobView.vue
|   |HomeView.vue
|   |...
以package.json为首的Lock文件.
```

以router/index.js定义用户访问某个链接时前端需要加载什么页面,此时django仅需要提供后端.
```js
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/jobs',
      name: 'jobs',
      component: JobsView,
    },
    {
      path: '/jobs/:id',
      name: 'job',
      component: JobView,
    },
    {
      path: '/jobs/add',
      name: 'add-job',
      component: AddJobView,
    },
    {
      path: '/jobs/edit/:id',
      name: 'edit-job',
      component: EditJobView,
    },
    {
      path: '/:catchAll(.*)',
      name: 'not-found',
      component: NotFoundView,
    },
  ],
});
```


# vue-crash-2024-my-ver

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```
