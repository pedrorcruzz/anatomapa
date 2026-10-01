<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import RegionPicker from './RegionPicker.vue'
import { describeKey, regionIndex, topGroupOf, type Side } from '@/lib/heatmapForm'

const form = inject(HEATMAP_FORM_KEY)!

const byId = computed(() => regionIndex(form.regions.value))
const usedKeys = computed(() => new Set(Object.keys(form.values)))
const filterTerm = ref('')

const SIDE_KEY: Record<Side, 'manual.sideLeft' | 'manual.sideRight' | null> = {
  both: null,
  left: 'manual.sideLeft',
  right: 'manual.sideRight',
}

const rows = computed(() =>
  Object.keys(form.values)
    .map((key) => {
      const description = describeKey(key, byId.value)
      const group = description ? topGroupOf(description.region.id, byId.value) : null
      return {
        key,
        value: form.values[key] ?? 0,
        label: description?.region.label ?? key,
        side: description?.side ?? ('both' as Side),
        groupId: group?.id ?? null,
        groupLabel: group?.label ?? null,
      }
    })
    .sort((a, b) => a.label.localeCompare(b.label, form.options.lang === 'pt' ? 'pt-BR' : 'en')),
)

// Resumo por grupo (Cabeça/Tronco/...) só das regiões já adicionadas, pra
// dar um botão de "limpar essas aqui" quando a lista cresce e fica difícil
// de enxergar tudo que foi marcado.
const groupSummary = computed(() => {
  const counts = new Map<string, { label: string; count: number }>()
  for (const row of rows.value) {
    if (!row.groupId) {
      continue
    }
    const entry = counts.get(row.groupId) ?? { label: row.groupLabel!, count: 0 }
    entry.count += 1
    counts.set(row.groupId, entry)
  }
  return Array.from(counts.entries()).map(([id, value]) => ({ id, ...value }))
})

const filteredRows = computed(() => {
  const needle = filterTerm.value.trim().toLocaleLowerCase()
  if (!needle) {
    return rows.value
  }
  return rows.value.filter((row) => row.label.toLocaleLowerCase().includes(needle))
})

function onSelect(key: string): void {
  form.setValue(key, 1)
}

function onInput(key: string, raw: string): void {
  const value = Number(raw)
  form.setValue(key, Number.isFinite(value) ? value : 0)
}

function step(key: string, current: number, delta: number): void {
  form.setValue(key, Math.max(0, current + delta))
}

function clearGroup(groupId: string): void {
  for (const row of rows.value) {
    if (row.groupId === groupId) {
      form.removeValue(row.key)
    }
  }
}

</script>

<template>
  <div class="flex flex-col gap-5">
    <p class="text-sm text-ink-muted">{{ form.t('manual.hint') }}</p>

    <RegionPicker :regions="form.regions.value" :used-keys="usedKeys" @select="onSelect" />

    <div v-if="rows.length > 0" class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative min-w-40 flex-1">
          <svg
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-muted"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4.3-4.3" stroke-linecap="round" />
          </svg>
          <input
            v-model="filterTerm"
            type="search"
            :placeholder="form.t('manual.filterPlaceholder')"
            class="w-full rounded-lg bg-surface-soft py-2 pr-3 pl-8 text-xs text-ink placeholder:text-ink-muted ring-1 ring-border/70"
          />
        </div>
        <button
          type="button"
          class="shrink-0 text-xs font-medium text-ink-muted hover:text-primary"
          @click="form.clearAll()"
        >
          {{ form.t('manual.clearAll') }}
        </button>
      </div>

      <div v-if="groupSummary.length > 1" class="flex flex-wrap gap-1.5">
        <button
          v-for="g in groupSummary"
          :key="g.id"
          type="button"
          class="flex items-center gap-1 rounded-full bg-surface-soft px-2.5 py-1 text-xs font-medium text-ink-muted ring-1 ring-border/70 transition-colors hover:text-primary hover:ring-primary"
          @click="clearGroup(g.id)"
        >
          {{ g.label }} · {{ g.count }}
          <span aria-hidden="true">✕</span>
        </button>
      </div>

      <div class="flex flex-col gap-2.5">
        <div
          v-for="row in filteredRows"
          :key="row.key"
          class="flex items-center gap-3 rounded-xl bg-surface-soft px-4 py-3 ring-1 ring-border/60"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-ink">{{ row.label }}</p>
            <p v-if="SIDE_KEY[row.side]" class="text-xs text-ink-muted">{{ form.t(SIDE_KEY[row.side]!) }}</p>
          </div>
          <div
            class="flex items-center overflow-hidden rounded-lg bg-surface ring-1 ring-border/70 focus-within:ring-2 focus-within:ring-primary"
          >
            <button
              type="button"
              class="px-2 py-1.5 text-ink-muted transition-colors hover:bg-surface-soft hover:text-primary"
              :aria-label="form.t('manual.decrease')"
              @click="step(row.key, row.value, -1)"
            >
              −
            </button>
            <input
              type="number"
              min="0"
              step="any"
              :value="row.value"
              class="w-14 bg-transparent py-1.5 text-center text-sm text-ink outline-none"
              @input="onInput(row.key, ($event.target as HTMLInputElement).value)"
            />
            <button
              type="button"
              class="px-2 py-1.5 text-ink-muted transition-colors hover:bg-surface-soft hover:text-primary"
              :aria-label="form.t('manual.increase')"
              @click="step(row.key, row.value, 1)"
            >
              +
            </button>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-lg p-1.5 text-ink-muted transition-colors hover:bg-surface hover:text-primary"
            :aria-label="form.t('manual.removeRegion')"
            @click="form.removeValue(row.key)"
          >
            ✕
          </button>
        </div>
        <p v-if="filteredRows.length === 0" class="px-3 py-4 text-center text-sm text-ink-muted">
          {{ form.t('manual.noMatches') }}
        </p>
      </div>
    </div>
    <div
      v-else
      class="flex flex-1 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-border p-8 text-center"
    >
      <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" class="text-ink-muted/70">
        <circle cx="12" cy="8" r="4" stroke-linecap="round" />
        <path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7" stroke-linecap="round" />
      </svg>
      <p class="text-sm text-ink-muted">{{ form.t('manual.empty') }}</p>
    </div>
  </div>
</template>
