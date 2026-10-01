<script setup lang="ts">
import { inject } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import { AUTHOR_GITHUB_URL, DOI_URL, GITHUB_URL, PYPI_URL } from '@/lib/links'

const form = inject(HEATMAP_FORM_KEY)!

defineProps<{
  version?: string | null
}>()
</script>

<template>
  <footer class="border-t border-border/70 bg-surface">
    <div
      class="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs text-ink-muted sm:flex-row sm:px-6"
    >
      <p>
        Anatomapa<template v-if="version"> · v{{ version }}</template> · Centro Universitário CESMAC · MIT
        ·
        {{ form.t('footer.madeBy') }}
        <a class="font-medium text-ink-muted transition-colors hover:text-primary" :href="AUTHOR_GITHUB_URL" target="_blank" rel="noreferrer">
          Pedro Rosa
        </a>
      </p>
      <div class="flex items-center gap-4">
        <a class="transition-colors hover:text-primary" :href="GITHUB_URL" target="_blank" rel="noreferrer">
          GitHub
        </a>
        <a class="transition-colors hover:text-primary" :href="PYPI_URL" target="_blank" rel="noreferrer">
          PyPI
        </a>
        <a class="transition-colors hover:text-primary" :href="DOI_URL" target="_blank" rel="noreferrer">
          DOI
        </a>
      </div>
    </div>
  </footer>
</template>
