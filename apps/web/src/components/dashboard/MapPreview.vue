<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import { downloadBlob, svgToPngBlob } from '@/lib/exportPng'
import OptionsPanel from './OptionsPanel.vue'

const form = inject(HEATMAP_FORM_KEY)!

const exportingPng = ref(false)
const exportError = ref<string | null>(null)

// Mesma cor exata que a lib desenha no retângulo de fundo da figura
// (render/svg.py _background_fill), pra não sobrar nenhuma borda visível
// entre o painel e o SVG. "transparent" não desenha retângulo nenhum, então
// aqui entra o xadrez clássico de "sem fundo", pra ficar óbvio que é
// transparente e não um cinza qualquer escolhido à toa.
const canvasClass = computed(() => {
  switch (form.options.background) {
    case 'dark':
      return 'bg-[#0a0a0a]'
    case 'light':
      return 'bg-white'
    default:
      return 'bg-checkerboard'
  }
})

function downloadSvg(): void {
  if (!form.svg.value) {
    return
  }
  downloadBlob(new Blob([form.svg.value], { type: 'image/svg+xml' }), 'anatomapa.svg')
}

async function downloadPng(): Promise<void> {
  if (!form.svg.value) {
    return
  }
  exportError.value = null
  exportingPng.value = true
  try {
    const blob = await svgToPngBlob(form.svg.value)
    downloadBlob(blob, 'anatomapa.png')
  } catch (cause) {
    exportError.value = cause instanceof Error ? cause.message : String(cause)
  } finally {
    exportingPng.value = false
  }
}
</script>

<template>
  <section
    class="flex h-full flex-col gap-6 rounded-3xl bg-surface p-6 shadow-sm ring-1 ring-border/70 sm:p-8"
  >
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold text-ink">{{ form.t('map.heading') }}</h2>
        <p class="text-xs text-ink-muted">
          {{ form.regionCount.value }}
          {{ form.t(form.regionCount.value === 1 ? 'map.regionCountSingular' : 'map.regionCountPlural') }}
        </p>
      </div>
      <div class="flex shrink-0 gap-2">
        <button
          type="button"
          class="min-w-[9.5rem] rounded-xl px-3.5 py-2 text-xs font-medium text-ink ring-1 ring-border transition-colors hover:text-primary hover:ring-primary disabled:opacity-50"
          :disabled="!form.svg.value"
          @click="downloadSvg"
        >
          {{ form.t('map.downloadSvg') }}
        </button>
        <button
          type="button"
          class="min-w-[9.5rem] rounded-xl bg-gradient-to-b from-primary to-primary-hover px-3.5 py-2 text-xs font-medium text-white shadow-sm shadow-primary/30 transition-opacity hover:opacity-90 disabled:opacity-50"
          :disabled="!form.svg.value || exportingPng"
          @click="downloadPng"
        >
          {{ exportingPng ? form.t('map.downloadPngBusy') : form.t('map.downloadPng') }}
        </button>
      </div>
    </div>

    <OptionsPanel />

    <p
      v-if="form.renderError.value"
      class="rounded-xl bg-bg px-3 py-2 text-sm text-primary ring-1 ring-primary/30"
    >
      {{ form.renderError.value }}
    </p>
    <p v-if="exportError" class="text-xs text-primary">{{ exportError }}</p>

    <div
      class="map-canvas flex items-center justify-center overflow-hidden rounded-2xl p-6 transition-colors"
      :class="canvasClass"
      v-html="form.svg.value"
    />
  </section>
</template>
