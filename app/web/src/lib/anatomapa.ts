import { loadPyodide, type PyodideInterface } from 'pyodide'
import bootstrapSource from './bootstrap.py?raw'

export type View = 'anterior' | 'posterior' | 'both'
export type Body = 'male' | 'female'
export type Lang = 'pt' | 'en'
export type Background = 'dark' | 'light' | 'transparent'
export type OnUnknown = 'error' | 'skip' | 'warn'

export type Values = Record<string, number>

export interface HeatmapOptions {
  view?: View
  body?: Body
  lang?: Lang
  title?: string | null
  background?: Background
  onUnknown?: OnUnknown
  regionMap?: Record<string, string> | null
}

export interface ListRegionsOptions {
  lang?: Lang
  body?: Body
  view?: Exclude<View, 'both'>
}

export interface ValidateOptions {
  body?: Body
  regionMap?: Record<string, string> | null
}

export interface RegionInfo {
  id: string
  label: string
  bilateral: boolean
  parent: string | null
  views: string[]
}

export interface UnresolvedLabel {
  reason: string
  suggestions: string[]
}

export interface ValidationReport {
  resolved: Record<string, string>
  unresolved: Record<string, UnresolvedLabel>
}

export interface WheelManifest {
  wheel: string
  version: string
}

export type LoadStage = 'runtime' | 'library' | 'ready'

export interface LoadOptions {
  baseUrl?: string
  onStage?: (stage: LoadStage) => void
}

export interface Anatomapa {
  version: string
  heatmap(values: Values, options?: HeatmapOptions): string
  listRegions(options?: ListRegionsOptions): RegionInfo[]
  validate(values: Values, options?: ValidateOptions): ValidationReport
}

const WHEEL_PATH = '/tmp/anatomapa.whl'
const SITE_PACKAGES = '/lib/anatomapa'

const HEATMAP_KEYS: Record<string, string> = {
  view: 'view',
  body: 'body',
  lang: 'lang',
  title: 'title',
  background: 'background',
  onUnknown: 'on_unknown',
  regionMap: 'region_map',
}

const LIST_REGIONS_KEYS: Record<string, string> = {
  lang: 'lang',
  body: 'body',
  view: 'view',
}

const VALIDATE_KEYS: Record<string, string> = {
  body: 'body',
  regionMap: 'region_map',
}

export function joinBase(base: string, path: string): string {
  return `${base.endsWith('/') ? base : `${base}/`}${path}`
}

export function toPythonOptions<T extends object>(
  options: T,
  keys: Record<string, string>,
): Record<string, unknown> {
  const source = options as Record<string, unknown>
  const result: Record<string, unknown> = {}
  for (const [camelKey, pythonKey] of Object.entries(keys)) {
    const value = source[camelKey]
    if (value !== undefined) {
      result[pythonKey] = value
    }
  }
  return result
}

async function fetchBuffer(url: string): Promise<ArrayBuffer> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Falha ao baixar ${url}: ${response.status} ${response.statusText}`)
  }
  return response.arrayBuffer()
}

async function fetchManifest(url: string): Promise<WheelManifest> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Manifesto do wheel não encontrado em ${url}: ${response.status}`)
  }
  return response.json() as Promise<WheelManifest>
}

async function installLibrary(pyodide: PyodideInterface, baseUrl: string): Promise<void> {
  const manifest = await fetchManifest(joinBase(baseUrl, 'wheels/manifest.json'))
  const wheel = await fetchBuffer(joinBase(baseUrl, `wheels/${manifest.wheel}`))
  pyodide.FS.writeFile(WHEEL_PATH, new Uint8Array(wheel))
  await pyodide.runPythonAsync(bootstrapSource)
  const install = pyodide.globals.get('install_wheel')
  try {
    install(WHEEL_PATH, SITE_PACKAGES)
  } finally {
    install.destroy()
  }
}

export async function loadAnatomapa(options: LoadOptions = {}): Promise<Anatomapa> {
  const baseUrl = options.baseUrl ?? import.meta.env.BASE_URL

  options.onStage?.('runtime')
  const pyodide = await loadPyodide({ indexURL: joinBase(baseUrl, 'pyodide/') })

  options.onStage?.('library')
  await installLibrary(pyodide, baseUrl)

  const call = <T>(name: string, payload: unknown): T => {
    const fn = pyodide.globals.get(name)
    try {
      return JSON.parse(fn(JSON.stringify(payload)) as string) as T
    } finally {
      fn.destroy()
    }
  }

  const readVersion = pyodide.globals.get('library_version')
  let version: string
  try {
    version = readVersion() as string
  } finally {
    readVersion.destroy()
  }

  options.onStage?.('ready')

  return {
    version,
    heatmap(values, heatmapOptions = {}) {
      const render = pyodide.globals.get('render_heatmap')
      try {
        return render(
          JSON.stringify({ values, options: toPythonOptions(heatmapOptions, HEATMAP_KEYS) }),
        ) as string
      } finally {
        render.destroy()
      }
    },
    listRegions(listOptions = {}) {
      return call<RegionInfo[]>('list_regions', toPythonOptions(listOptions, LIST_REGIONS_KEYS))
    },
    validate(values, validateOptions = {}) {
      return call<ValidationReport>('validate_values', {
        values,
        options: toPythonOptions(validateOptions, VALIDATE_KEYS),
      })
    },
  }
}
