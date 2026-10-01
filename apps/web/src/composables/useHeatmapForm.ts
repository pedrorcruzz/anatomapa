import { computed, reactive, ref, watch, type InjectionKey } from 'vue'
import { useAnatomapa } from './useAnatomapa'
import type { Background, Body, Lang, RegionInfo, Values, View } from '@/lib/anatomapa'
import { format, translate, type MessageKey } from '@/lib/i18n'

export interface HeatmapFormOptions {
  view: View
  body: Body
  lang: Lang
  title: string
  background: Background
}

const DEBOUNCE_MS = 150
const UI_LANG_STORAGE_KEY = 'anatomapa:ui-lang'

function readStoredLang(): Lang | null {
  try {
    const stored = localStorage.getItem(UI_LANG_STORAGE_KEY)
    return stored === 'en' || stored === 'pt' ? stored : null
  } catch {
    return null
  }
}

function writeStoredLang(lang: Lang): void {
  try {
    localStorage.setItem(UI_LANG_STORAGE_KEY, lang)
  } catch {
    // Modo privado ou storage bloqueado: a preferência só não sobrevive ao reload.
  }
}

/**
 * Estado central do dashboard: os valores por região (de entrada manual ou de
 * Excel), o de-para de rótulos não reconhecidos, e as opções do mapa. Tudo
 * que mexe aqui dispara um novo render em `svg`, debatido, pintando em tempo
 * real conforme a pessoa digita.
 */
export function useHeatmapForm() {
  const { library, load, status, stage, error: runtimeError } = useAnatomapa()

  const values = reactive<Values>({})
  const regionMap = reactive<Record<string, string>>({})
  const options = reactive<HeatmapFormOptions>({
    view: 'both',
    body: 'male',
    lang: readStoredLang() ?? 'en',
    title: '',
    background: 'transparent',
  })
  const regions = ref<RegionInfo[]>([])

  const svg = ref('')
  const renderError = ref<string | null>(null)
  const rendering = ref(false)
  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  const regionCount = computed(() => Object.keys(values).length)

  function setValue(key: string, value: number): void {
    values[key] = value
  }

  function removeValue(key: string): void {
    delete values[key]
    delete regionMap[key]
  }

  function setMapping(label: string, regionId: string): void {
    regionMap[label] = regionId
  }

  function clearMapping(label: string): void {
    delete regionMap[label]
  }

  function clearAll(): void {
    for (const key of Object.keys(values)) {
      delete values[key]
    }
    for (const key of Object.keys(regionMap)) {
      delete regionMap[key]
    }
  }

  function render(): void {
    const lib = library.value
    if (!lib) {
      return
    }
    rendering.value = true
    try {
      svg.value = lib.heatmap(values, {
        view: options.view,
        body: options.body,
        lang: options.lang,
        title: options.title.trim() || null,
        background: options.background,
        onUnknown: 'skip',
        regionMap: Object.keys(regionMap).length > 0 ? { ...regionMap } : null,
      })
      renderError.value = null
    } catch (cause) {
      renderError.value = cause instanceof Error ? cause.message : String(cause)
    } finally {
      rendering.value = false
    }
  }

  function scheduleRender(): void {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    debounceTimer = setTimeout(render, DEBOUNCE_MS)
  }

  watch([values, regionMap, options], scheduleRender, { deep: true })

  async function refreshRegions(): Promise<void> {
    const lib = library.value
    if (!lib) {
      return
    }
    regions.value = lib.listRegions({ lang: options.lang, body: options.body })
  }

  watch(() => [options.lang, options.body], refreshRegions)

  watch(
    () => options.lang,
    (lang) => {
      writeStoredLang(lang)
      if (typeof document !== 'undefined') {
        document.documentElement.lang = lang
      }
    },
    { immediate: true },
  )

  function t(key: MessageKey): string {
    return translate(options.lang, key)
  }

  function tf(key: MessageKey, vars: Record<string, string | number>): string {
    return format(t(key), vars)
  }

  async function init(): Promise<void> {
    const lib = await load()
    regions.value = lib.listRegions({ lang: options.lang, body: options.body })
    render()
  }

  return {
    status,
    stage,
    runtimeError,
    values,
    regionMap,
    options,
    regions,
    svg,
    renderError,
    rendering,
    regionCount,
    setValue,
    removeValue,
    setMapping,
    clearMapping,
    clearAll,
    init,
    t,
    tf,
  }
}

export type HeatmapForm = ReturnType<typeof useHeatmapForm>

export const HEATMAP_FORM_KEY: InjectionKey<HeatmapForm> = Symbol('heatmapForm')
