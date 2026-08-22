import { readonly, ref, shallowRef } from 'vue'
import { loadAnatomapa, type Anatomapa, type LoadStage } from '@/lib/anatomapa'

export type RuntimeStatus = 'idle' | 'loading' | 'ready' | 'error'

const status = ref<RuntimeStatus>('idle')
const stage = ref<LoadStage | null>(null)
const error = ref<Error | null>(null)
const library = shallowRef<Anatomapa | null>(null)

let pending: Promise<Anatomapa> | null = null

function toError(cause: unknown): Error {
  return cause instanceof Error ? cause : new Error(String(cause))
}

function start(): Promise<Anatomapa> {
  status.value = 'loading'
  error.value = null

  return loadAnatomapa({ onStage: (next) => (stage.value = next) })
    .then((loaded) => {
      library.value = loaded
      status.value = 'ready'
      return loaded
    })
    .catch((cause) => {
      error.value = toError(cause)
      status.value = 'error'
      pending = null
      throw error.value
    })
}

export function useAnatomapa() {
  function load(): Promise<Anatomapa> {
    pending ??= start()
    return pending
  }

  return {
    status: readonly(status),
    stage: readonly(stage),
    error: readonly(error),
    library,
    load,
  }
}
