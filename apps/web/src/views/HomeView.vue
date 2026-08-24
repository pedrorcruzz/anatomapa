<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAnatomapa } from '@/composables/useAnatomapa'
import type { Values } from '@/lib/anatomapa'

const SAMPLE: Values = {
  upper_chest: 8,
  hand_right: 5,
  knee: 3,
  head: 1,
}

const STAGE_LABEL: Record<string, string> = {
  runtime: 'Carregando o runtime Python',
  library: 'Instalando a biblioteca',
  ready: 'Gerando o mapa',
}

const { status, stage, error, library, load } = useAnatomapa()
const svg = ref('')

onMounted(async () => {
  try {
    const anatomapa = await load()
    svg.value = anatomapa.heatmap(SAMPLE, { view: 'both', background: 'dark', lang: 'pt' })
  } catch {
    svg.value = ''
  }
})
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 p-6">
    <p v-if="status === 'loading'" class="text-ink-muted">
      {{ STAGE_LABEL[stage ?? 'runtime'] }}...
    </p>

    <p v-else-if="status === 'error'" class="text-accent">
      Não foi possível carregar a biblioteca: {{ error?.message }}
    </p>

    <template v-else-if="status === 'ready'">
      <p class="text-ink-muted text-sm">anatomapa {{ library?.version }} rodando no navegador</p>
      <div class="border-border overflow-hidden rounded-lg border" v-html="svg"></div>
    </template>
  </main>
</template>
