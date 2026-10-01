<script setup lang="ts">
import { inject } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import { useTheme, type Theme } from '@/composables/useTheme'
import { DOI_URL, GITHUB_URL, PYPI_URL } from '@/lib/links'
import type { Lang } from '@/lib/anatomapa'

const form = inject(HEATMAP_FORM_KEY)!
const { theme, setTheme } = useTheme()

const LOGO_URL = `${import.meta.env.BASE_URL}favicon.svg`

const THEMES: { value: Theme }[] = [{ value: 'light' }, { value: 'dark' }]

const LANGS: { value: Lang; label: string; flag: string; alt: string }[] = [
  { value: 'en', label: 'EN', flag: 'https://flagcdn.com/24x18/us.png', alt: 'English' },
  { value: 'pt', label: 'PT', flag: 'https://flagcdn.com/24x18/br.png', alt: 'Português' },
]
</script>

<template>
  <header class="sticky top-0 z-10 border-b border-border/70 bg-surface/85 backdrop-blur-md">
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
      <div class="flex items-center gap-3">
        <img :src="LOGO_URL" alt="Anatomapa" class="h-9 w-9 rounded-xl shadow-sm" />
        <p class="text-xl font-semibold tracking-tight text-ink">Anatomapa</p>
      </div>

      <div class="flex items-center gap-4">
        <nav class="hidden items-center gap-4 text-sm font-medium text-ink-muted sm:flex">
          <a class="transition-colors hover:text-primary" :href="GITHUB_URL" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a class="transition-colors hover:text-primary" :href="PYPI_URL" target="_blank" rel="noreferrer">
            PyPI
          </a>
          <a class="transition-colors hover:text-primary" :href="DOI_URL" target="_blank" rel="noreferrer">
            DOI
          </a>
        </nav>

        <!-- Tema do site: mesmo padrão visual do toggle de idioma ao lado, pra
             ficar claro que são duas opções nomeadas (não um ícone ambíguo que
             alterna sozinho) e qual delas está ativa agora. -->
        <div class="flex items-center gap-0.5 rounded-lg bg-surface-soft p-1 ring-1 ring-border/70" role="radiogroup" :aria-label="form.t('theme.label')">
          <button
            v-for="entry in THEMES"
            :key="entry.value"
            type="button"
            role="radio"
            :aria-checked="theme === entry.value"
            class="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-semibold transition-colors"
            :class="theme === entry.value ? 'bg-surface text-ink shadow-sm' : 'text-ink-muted hover:text-ink'"
            @click="setTheme(entry.value)"
          >
            <svg v-if="entry.value === 'light'" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="#818cf8" stroke="#818cf8" stroke-width="1" stroke-linejoin="round" class="shrink-0">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
            </svg>
            <span class="hidden sm:inline">{{ form.t(entry.value === 'light' ? 'theme.light' : 'theme.dark') }}</span>
          </button>
        </div>

        <div class="flex items-center gap-0.5 rounded-lg bg-surface-soft p-1 ring-1 ring-border/70" role="radiogroup">
          <button
            v-for="entry in LANGS"
            :key="entry.value"
            type="button"
            role="radio"
            :aria-checked="form.options.lang === entry.value"
            class="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-semibold transition-colors"
            :class="
              form.options.lang === entry.value
                ? 'bg-surface text-ink shadow-sm'
                : 'text-ink-muted hover:text-ink'
            "
            @click="form.options.lang = entry.value"
          >
            <img :src="entry.flag" :alt="entry.alt" width="18" height="13" class="rounded-[2px]" />
            {{ entry.label }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
