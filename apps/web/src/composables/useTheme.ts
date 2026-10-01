import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'anatomapa:theme'

function readStoredTheme(): Theme | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    return null
  }
}

function writeStoredTheme(value: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Modo privado ou storage bloqueado: a preferência só não sobrevive ao reload.
  }
}

function applyTheme(value: Theme): void {
  if (typeof document === 'undefined') {
    return
  }
  document.documentElement.setAttribute('data-theme', value)
}

// Estado em variável de módulo: singleton compartilhado por toda a aplicação,
// aplicado assim que este módulo é importado, antes de qualquer componente montar.
const theme = ref<Theme>(readStoredTheme() ?? 'light')
applyTheme(theme.value)

watch(theme, (value) => {
  writeStoredTheme(value)
  applyTheme(value)
})

export function useTheme() {
  function toggle(): void {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  function setTheme(value: Theme): void {
    theme.value = value
  }

  return { theme, toggle, setTheme }
}
