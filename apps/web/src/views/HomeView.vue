<script setup lang="ts">
import { inject } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import DataEntryCard from '@/components/dashboard/DataEntryCard.vue'
import MapPreview from '@/components/dashboard/MapPreview.vue'
import type { MessageKey } from '@/lib/i18n'

const form = inject(HEATMAP_FORM_KEY)!

const STAGE_KEY: Record<string, MessageKey> = {
  runtime: 'loading.runtime',
  library: 'loading.library',
  ready: 'loading.ready',
}
</script>

<template>
  <main class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:py-12">
    <div
      v-if="form.status.value === 'loading' || form.status.value === 'idle'"
      class="flex min-h-[60vh] items-center justify-center"
    >
      <div class="flex flex-col items-center gap-3 text-center">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-primary" />
        <p class="text-sm text-ink-muted">{{ form.t(STAGE_KEY[form.stage.value ?? 'runtime']!) }}</p>
      </div>
    </div>

    <div v-else-if="form.status.value === 'error'" class="flex min-h-[60vh] items-center justify-center">
      <div class="max-w-sm rounded-2xl bg-surface p-6 text-center shadow-sm ring-1 ring-border/70">
        <p class="mb-2 text-sm font-semibold text-ink">{{ form.t('loading.errorTitle') }}</p>
        <p class="text-xs text-ink-muted">{{ form.runtimeError.value?.message }}</p>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] lg:gap-8">
      <DataEntryCard />
      <MapPreview />
    </div>
  </main>
</template>
