<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'
import { useAnatomapa } from '@/composables/useAnatomapa'
import { HEATMAP_FORM_KEY } from '@/composables/useHeatmapForm'
import RegionPicker from './RegionPicker.vue'
import Dropdown from '@/components/ui/Dropdown.vue'
import { columnOptions } from '@/lib/xlsxColumns'
import type { UnresolvedLabel, XlsxAggregate, XlsxPreview } from '@/lib/anatomapa'

const form = inject(HEATMAP_FORM_KEY)!
const { library } = useAnatomapa()

type Step = 'upload' | 'columns' | 'review'

const step = ref<Step>('upload')
const dragOver = ref(false)
const fileName = ref<string | null>(null)
const filePath = ref<string | null>(null)
const preview = ref<XlsxPreview | null>(null)
const sheet = ref<string | null>(null)
const headerRow = ref(true)
const regionCol = ref('')
const valueCol = ref('')
const aggregate = ref<XlsxAggregate>(null)
const busy = ref(false)
const errorMessage = ref<string | null>(null)
const importedLabels = ref<string[]>([])
const unresolved = ref<Record<string, UnresolvedLabel>>({})

const AGGREGATE_OPTIONS = computed<{ value: XlsxAggregate; label: string; hint: string }[]>(() => [
  { value: null, label: form.t('excel.aggregateNone'), hint: form.t('excel.aggregateNoneHint') },
  { value: 'count', label: form.t('excel.aggregateCount'), hint: form.t('excel.aggregateCountHint') },
  { value: 'sum', label: form.t('excel.aggregateSum'), hint: form.t('excel.aggregateSumHint') },
])

const columns = computed(() => (preview.value ? columnOptions(preview.value) : []))
const sheetOptions = computed(() => (preview.value?.sheets ?? []).map((name) => ({ value: name, label: name })))
const unresolvedCount = computed(() => Object.keys(unresolved.value).length)
const resolvedCount = computed(() => importedLabels.value.length - unresolvedCount.value)
const canImport = computed(
  () => !busy.value && !!regionCol.value && (aggregate.value === 'count' || !!valueCol.value),
)

function toMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

async function handleFiles(files: FileList | null | undefined): Promise<void> {
  const file = files?.[0]
  const lib = library.value
  if (!file || !lib) {
    return
  }

  errorMessage.value = null
  busy.value = true
  try {
    const bytes = new Uint8Array(await file.arrayBuffer())
    filePath.value = lib.writeXlsxFile(bytes)
    fileName.value = file.name
    refreshPreview()
    step.value = 'columns'
  } catch (cause) {
    errorMessage.value = toMessage(cause)
  } finally {
    busy.value = false
  }
}

async function onFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  await handleFiles(input.files)
  input.value = ''
}

async function onDrop(event: DragEvent): Promise<void> {
  dragOver.value = false
  await handleFiles(event.dataTransfer?.files)
}

function refreshPreview(): void {
  const lib = library.value
  if (!lib || !filePath.value) {
    return
  }
  errorMessage.value = null
  try {
    const result = lib.previewXlsx(filePath.value, { sheet: sheet.value, header: headerRow.value, nRows: 8 })
    preview.value = result
    sheet.value = result.sheet
    const options = columnOptions(result)
    if (!options.some((option) => option.value === regionCol.value)) {
      regionCol.value = options[0]?.value ?? ''
    }
    if (!options.some((option) => option.value === valueCol.value)) {
      valueCol.value = options[1]?.value ?? options[0]?.value ?? ''
    }
  } catch (cause) {
    errorMessage.value = toMessage(cause)
  }
}

watch([sheet, headerRow], refreshPreview)

function runImport(): void {
  const lib = library.value
  if (!lib || !filePath.value) {
    return
  }
  busy.value = true
  errorMessage.value = null
  try {
    const result = lib.readXlsx(filePath.value, {
      sheet: sheet.value,
      regionCol: regionCol.value,
      valueCol: valueCol.value,
      header: headerRow.value,
      aggregate: aggregate.value,
    })
    const report = lib.validate(result, { body: form.options.body })
    Object.assign(form.values, result)
    importedLabels.value = Object.keys(result)
    unresolved.value = report.unresolved
    step.value = 'review'
  } catch (cause) {
    errorMessage.value = toMessage(cause)
  } finally {
    busy.value = false
  }
}

function mapLabel(label: string, regionId: string): void {
  form.setMapping(label, regionId)
  delete unresolved.value[label]
}

function ignoreLabel(label: string): void {
  form.removeValue(label)
  delete unresolved.value[label]
  importedLabels.value = importedLabels.value.filter((entry) => entry !== label)
}

function reset(): void {
  for (const label of importedLabels.value) {
    form.removeValue(label)
  }
  step.value = 'upload'
  fileName.value = null
  filePath.value = null
  preview.value = null
  sheet.value = null
  regionCol.value = ''
  valueCol.value = ''
  aggregate.value = null
  importedLabels.value = []
  unresolved.value = {}
  errorMessage.value = null
}
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div v-if="step === 'upload'" class="flex flex-1 flex-col gap-3">
      <div
        class="flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-4 py-10 text-center transition-colors"
        :class="dragOver ? 'border-primary bg-primary/5' : 'border-border'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" class="text-ink-muted/70">
          <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <label class="cursor-pointer">
          <span class="text-sm font-semibold text-primary hover:underline">{{ form.t('excel.dropzoneAction') }}</span>
          <span class="text-sm text-ink-muted"> {{ form.t('excel.dropzoneHint') }}</span>
          <input type="file" accept=".xlsx" class="hidden" @change="onFileChange" />
        </label>
      </div>
      <p v-if="errorMessage" class="text-sm text-primary">{{ errorMessage }}</p>
    </div>

    <div v-else-if="step === 'columns'" class="flex flex-col gap-4">
      <div class="flex items-center justify-between gap-2">
        <p class="truncate text-sm text-ink">
          {{ form.t('excel.file') }} <span class="font-medium">{{ fileName }}</span>
        </p>
        <button
          type="button"
          class="shrink-0 text-xs font-medium text-ink-muted hover:text-primary"
          @click="reset"
        >
          {{ form.t('excel.changeFile') }}
        </button>
      </div>

      <div v-if="preview && preview.sheets.length > 1">
        <label class="mb-1.5 block text-xs font-medium text-ink-muted">{{ form.t('excel.sheet') }}</label>
        <Dropdown :model-value="sheet ?? ''" :options="sheetOptions" @update:model-value="sheet = $event" />
      </div>

      <label class="flex items-center gap-2 text-sm text-ink">
        <input v-model="headerRow" type="checkbox" class="h-4 w-4 rounded accent-primary" />
        {{ form.t('excel.headerRow') }}
      </label>

      <div v-if="preview" class="overflow-x-auto rounded-xl ring-1 ring-border/70">
        <table class="w-full text-left text-xs">
          <thead v-if="preview.headers">
            <tr class="bg-surface-soft">
              <th v-for="(h, i) in preview.headers" :key="i" class="px-3 py-2 font-medium text-ink-muted">
                {{ h || '—' }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border/60">
            <tr v-for="(row, i) in preview.rows" :key="i">
              <td v-for="(cell, j) in row" :key="j" class="truncate px-3 py-2 text-ink">{{ cell || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1.5 block text-xs font-medium text-ink-muted">{{ form.t('excel.regionColumn') }}</label>
          <Dropdown v-model="regionCol" :options="columns" />
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-medium text-ink-muted">{{ form.t('excel.valueColumn') }}</label>
          <Dropdown v-model="valueCol" :options="columns" :disabled="aggregate === 'count'" />
        </div>
      </div>

      <div>
        <p class="mb-1.5 text-xs font-medium text-ink-muted">{{ form.t('excel.aggregateLabel') }}</p>
        <div class="flex flex-col gap-1.5">
          <label
            v-for="opt in AGGREGATE_OPTIONS"
            :key="String(opt.value)"
            class="flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm ring-1 transition-colors"
            :class="aggregate === opt.value ? 'bg-primary/5 ring-primary' : 'ring-border/70'"
          >
            <input v-model="aggregate" type="radio" class="mt-0.5 accent-primary" :value="opt.value" />
            <span>
              <span class="font-medium text-ink">{{ opt.label }}</span>
              <span class="block text-xs text-ink-muted">{{ opt.hint }}</span>
            </span>
          </label>
        </div>
      </div>

      <p v-if="errorMessage" class="text-sm text-primary">{{ errorMessage }}</p>

      <button
        type="button"
        class="self-start rounded-xl bg-gradient-to-b from-primary to-primary-hover px-4 py-2 text-sm font-medium text-white shadow-sm shadow-primary/30 transition-opacity hover:opacity-90 disabled:opacity-50"
        :disabled="!canImport"
        @click="runImport"
      >
        {{ form.t('excel.analyze') }}
      </button>
    </div>

    <div v-else class="flex h-full flex-col gap-4">
      <div class="flex items-center justify-between gap-2">
        <p class="text-sm text-ink">
          {{ form.tf('excel.recognizedOf', { resolved: resolvedCount, total: importedLabels.length }) }}
        </p>
        <button
          type="button"
          class="shrink-0 text-xs font-medium text-ink-muted hover:text-primary"
          @click="reset"
        >
          {{ form.t('excel.importAnother') }}
        </button>
      </div>

      <div v-if="unresolvedCount > 0" class="flex flex-col gap-3">
        <p class="text-xs text-ink-muted">
          {{ form.t('excel.unresolvedHint') }}
        </p>
        <div v-for="(info, label) in unresolved" :key="label" class="rounded-xl bg-surface-soft p-3.5 ring-1 ring-border/60">
          <div class="mb-2 flex items-center justify-between gap-2">
            <p class="truncate text-sm font-medium text-ink">"{{ label }}"</p>
            <button
              type="button"
              class="shrink-0 text-xs font-medium text-ink-muted hover:text-primary"
              @click="ignoreLabel(label)"
            >
              {{ form.t('excel.ignore') }}
            </button>
          </div>
          <div v-if="info.suggestions.length > 0" class="mb-2 flex flex-wrap gap-1.5">
            <button
              v-for="suggestion in info.suggestions"
              :key="suggestion"
              type="button"
              class="rounded-full bg-surface px-2.5 py-1 text-xs text-ink ring-1 ring-border/70 transition-colors hover:text-primary hover:ring-primary"
              @click="mapLabel(label, suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
          <RegionPicker :regions="form.regions.value" @select="(key) => mapLabel(label, key)" />
        </div>
      </div>

      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-2 rounded-2xl p-8 text-center ring-1 ring-border/60"
      >
        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" class="text-primary">
          <path d="M5 12l4 4L19 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <p class="text-sm text-ink-muted">{{ form.t('excel.allResolved') }}</p>
      </div>
    </div>
  </div>
</template>
