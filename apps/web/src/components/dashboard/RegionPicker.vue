<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import type { RegionInfo } from '@/lib/anatomapa'
import {
  availableSides,
  groupRegions,
  isRegionExhausted,
  regionIndex,
  searchRegions,
  sideKey,
  topGroupOf,
  type Side,
} from '@/lib/heatmapForm'

const props = withDefaults(
  defineProps<{
    regions: RegionInfo[]
    usedKeys?: ReadonlySet<string>
  }>(),
  {
    usedKeys: () => new Set(),
  },
)

const emit = defineEmits<{
  select: [key: string]
}>()

const form = inject(HEATMAP_FORM_KEY)!

const query = ref('')
const activeGroup = ref<string | null>(null)
const openRegionId = ref<string | null>(null)

const SIDE_KEY: Record<Side, 'picker.sideBoth' | 'picker.sideLeft' | 'picker.sideRight'> = {
  both: 'picker.sideBoth',
  left: 'picker.sideLeft',
  right: 'picker.sideRight',
}

const byId = computed(() => regionIndex(props.regions))

// Chips de filtro por região raiz (Cabeça/Tronco/...), com a contagem de
// quanto ainda dá pra adicionar em cada uma. Calculada sobre o catálogo
// inteiro, não sobre a busca atual, pra não ficar pulando de número
// enquanto a pessoa digita.
const groupChips = computed(() =>
  groupRegions(props.regions, props.regions).map(({ group, regions }) => ({
    id: group.id,
    label: group.label,
    count: regions.filter((region) => !isRegionExhausted(region, props.usedKeys)).length,
  })),
)

const visibleRegions = computed(() => {
  let list = searchRegions(props.regions, query.value).filter(
    (region) => !isRegionExhausted(region, props.usedKeys),
  )
  if (activeGroup.value) {
    list = list.filter((region) => topGroupOf(region.id, byId.value).id === activeGroup.value)
  }
  return list
})

const groups = computed(() => groupRegions(visibleRegions.value, props.regions))

function sidesFor(region: RegionInfo): Side[] {
  return region.bilateral ? availableSides(region.id, props.usedKeys) : ['both']
}

function pick(region: RegionInfo): void {
  const sides = sidesFor(region)
  if (sides.length <= 1) {
    choose(region, sides[0] ?? 'both')
    return
  }
  openRegionId.value = openRegionId.value === region.id ? null : region.id
}

function choose(region: RegionInfo, side: Side): void {
  emit('select', sideKey(region.id, side))
  openRegionId.value = null
  query.value = ''
}

function toggleGroup(id: string): void {
  activeGroup.value = activeGroup.value === id ? null : id
}

function onEnter(): void {
  const first = visibleRegions.value[0]
  if (first) {
    pick(first)
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="relative">
      <svg
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        class="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-ink-muted"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="M21 21l-4.3-4.3" stroke-linecap="round" />
      </svg>
      <input
        v-model="query"
        type="search"
        :placeholder="form.t('picker.placeholder')"
        class="w-full rounded-xl bg-surface-soft py-2.5 pr-9 pl-10 text-sm text-ink placeholder:text-ink-muted ring-1 ring-border/70"
        @keydown.enter.prevent="onEnter"
      />
      <button
        v-if="query"
        type="button"
        class="absolute top-1/2 right-2.5 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full text-ink-muted transition-colors hover:bg-border/60 hover:text-ink"
        :aria-label="form.t('picker.clear')"
        @click="query = ''"
      >
        ✕
      </button>
    </div>

    <!-- min-h reserva o espaço do pior caso (PT quebra em 2 linhas, EN às
         vezes cabe em 1): sem isso, trocar de idioma muda a altura dessa
         linha e empurra a lista de resultados pra uma posição diferente. -->
    <div class="flex min-h-14 flex-wrap content-start gap-1.5">
      <button
        type="button"
        class="h-fit rounded-full px-2.5 py-1 text-xs font-medium transition-colors"
        :class="
          activeGroup === null
            ? 'bg-gradient-to-b from-primary to-primary-hover text-white'
            : 'bg-surface-soft text-ink-muted ring-1 ring-border/70 hover:text-ink'
        "
        @click="activeGroup = null"
      >
        {{ form.t('picker.allGroups') }}
      </button>
      <button
        v-for="chip in groupChips"
        :key="chip.id"
        type="button"
        class="rounded-full px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40"
        :class="
          activeGroup === chip.id
            ? 'bg-gradient-to-b from-primary to-primary-hover text-white'
            : 'bg-surface-soft text-ink-muted ring-1 ring-border/70 hover:text-ink'
        "
        :disabled="chip.count === 0"
        @click="toggleGroup(chip.id)"
      >
        {{ chip.label }} · {{ chip.count }}
      </button>
    </div>

    <div class="max-h-64 overflow-y-auto rounded-xl ring-1 ring-border/70">
      <p v-if="groups.length === 0" class="px-3 py-5 text-center text-sm text-ink-muted">
        {{ form.t('picker.empty') }}
      </p>

      <div v-for="entry in groups" :key="entry.group.id">
        <p
          class="sticky top-0 bg-surface-soft px-3.5 py-1.5 text-xs font-semibold tracking-wide text-ink-muted uppercase"
        >
          {{ entry.group.label }}
        </p>
        <div v-for="region in entry.regions" :key="region.id" class="divide-y divide-border/60">
          <button
            type="button"
            class="flex w-full items-center justify-between px-3.5 py-2.5 text-left text-sm text-ink transition-colors hover:bg-primary/5"
            @click="pick(region)"
          >
            <span>{{ region.label }}</span>
            <span
              v-if="region.bilateral"
              class="rounded-full bg-surface-soft px-2 py-0.5 text-[10px] font-medium text-ink-muted ring-1 ring-border/70"
            >
              {{ form.t('picker.bilateral') }}
            </span>
          </button>
          <div v-if="openRegionId === region.id" class="flex flex-wrap gap-1.5 bg-surface-soft px-3.5 py-2.5">
            <button
              v-for="side in sidesFor(region)"
              :key="side"
              type="button"
              class="rounded-lg bg-surface px-2.5 py-1 text-xs font-medium text-ink ring-1 ring-border/70 transition-colors hover:text-primary hover:ring-primary"
              @click="choose(region, side)"
            >
              {{ form.t(SIDE_KEY[side]) }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
