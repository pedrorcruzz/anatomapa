<script setup lang="ts">
import { inject, ref } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import ManualEntryTab from './ManualEntryTab.vue'
import ExcelImportTab from './ExcelImportTab.vue'

const form = inject(HEATMAP_FORM_KEY)!

type Tab = 'manual' | 'excel'

const tab = ref<Tab>('manual')
</script>

<template>
  <section class="flex h-full flex-col rounded-3xl bg-surface p-6 shadow-sm ring-1 ring-border/70 sm:p-8">
    <div class="mb-6 flex gap-1 rounded-xl bg-surface-soft p-1 ring-1 ring-border/70">
      <button
        type="button"
        class="flex-1 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-all"
        :class="
          tab === 'manual'
            ? 'bg-gradient-to-b from-primary to-primary-hover text-white shadow-sm'
            : 'text-ink-muted hover:text-ink'
        "
        @click="tab = 'manual'"
      >
        {{ form.t('tabs.manual') }}
      </button>
      <button
        type="button"
        class="flex-1 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-all"
        :class="
          tab === 'excel'
            ? 'bg-gradient-to-b from-primary to-primary-hover text-white shadow-sm'
            : 'text-ink-muted hover:text-ink'
        "
        @click="tab = 'excel'"
      >
        {{ form.t('tabs.excel') }}
      </button>
    </div>

    <ManualEntryTab v-show="tab === 'manual'" class="flex-1" />
    <ExcelImportTab v-show="tab === 'excel'" class="flex-1" />
  </section>
</template>
