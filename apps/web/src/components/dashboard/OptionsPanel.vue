<script setup lang="ts">
import { computed, inject } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Dropdown from '@/components/ui/Dropdown.vue'
import type { Background, Body, View } from '@/lib/anatomapa'

const form = inject(HEATMAP_FORM_KEY)!

// Larguras fixas, independentes do texto: a troca de idioma não pode
// deslocar nem estourar os campos vizinhos (PT costuma ser mais longo que
// EN — "Masculino"/"Transparente" vs "Male"/"Transparent"). O wrap pra uma
// segunda linha, se precisar, também fica igual nos dois idiomas, porque
// depende só dessas larguras fixas, nunca do texto em si.
const VIEW_OPTIONS = computed<{ value: View; label: string }[]>(() => [
  { value: 'anterior', label: form.t('options.view.anterior') },
  { value: 'posterior', label: form.t('options.view.posterior') },
  { value: 'both', label: form.t('options.view.both') },
])

const BODY_OPTIONS = computed<{ value: Body; label: string }[]>(() => [
  { value: 'male', label: form.t('options.body.male') },
  { value: 'female', label: form.t('options.body.female') },
])

const BACKGROUND_OPTIONS = computed<{ value: Background; label: string }[]>(() => [
  { value: 'transparent', label: form.t('options.background.transparent') },
  { value: 'light', label: form.t('options.background.light') },
  { value: 'dark', label: form.t('options.background.dark') },
])
</script>

<template>
  <div class="flex flex-wrap items-end gap-x-6 gap-y-4 border-b border-border/70 pb-6">
    <div class="w-full sm:w-72">
      <p class="mb-1.5 text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {{ form.t('options.view') }}
      </p>
      <SegmentedControl v-model="form.options.view" :options="VIEW_OPTIONS" />
    </div>

    <div class="w-full sm:w-52">
      <p class="mb-1.5 text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {{ form.t('options.body') }}
      </p>
      <SegmentedControl v-model="form.options.body" :options="BODY_OPTIONS" />
    </div>

    <div class="w-full sm:w-44">
      <label for="map-background" class="mb-1.5 block text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {{ form.t('options.background') }}
      </label>
      <Dropdown id="map-background" v-model="form.options.background" :options="BACKGROUND_OPTIONS" />
    </div>

    <div class="w-full sm:min-w-56 sm:flex-1">
      <label for="map-title" class="mb-1.5 block text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {{ form.t('options.title') }}
      </label>
      <input
        id="map-title"
        v-model="form.options.title"
        type="text"
        :placeholder="form.t('options.titlePlaceholder')"
        class="w-full rounded-xl bg-surface-soft px-4 py-2.5 text-sm text-ink placeholder:text-ink-muted ring-1 ring-border/70"
      />
    </div>
  </div>
</template>
