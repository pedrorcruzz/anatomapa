<script setup lang="ts">
import { onMounted, provide } from 'vue'
import { RouterView } from 'vue-router'
import { useAnatomapa } from '@/composables/useAnatomapa'
import { HEATMAP_FORM_KEY, useHeatmapForm } from '@/composables/useHeatmapForm'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const { library } = useAnatomapa()

const form = useHeatmapForm()
provide(HEATMAP_FORM_KEY, form)

onMounted(() => {
  void form.init()
})
</script>

<template>
  <div class="flex min-h-screen flex-col bg-bg">
    <AppHeader />
    <div class="flex-1">
      <RouterView />
    </div>
    <AppFooter :version="library?.version ?? null" />
  </div>
</template>
