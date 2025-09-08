<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref, watch } from 'vue'
const { locale } = useI18n()
const current = ref(locale.value)

watch(current, (val) => {
  locale.value = val
  localStorage.setItem('lang', val)
  // simplest way to refresh Element-Plus locale
  location.reload()
})
</script>

<template>
  <el-select v-model="current" size="small" class="w-28">
    <el-option label="English" value="en" />
    <el-option label="简体中文" value="zh" />
  </el-select>
</template>
