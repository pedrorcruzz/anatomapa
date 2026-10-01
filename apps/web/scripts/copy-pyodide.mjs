import { copyFileSync, existsSync, mkdirSync, rmSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const sourceDir = join(webDir, 'node_modules', 'pyodide')
const outDir = join(webDir, 'public', 'pyodide')

const RUNTIME_FILES = [
  'pyodide.asm.mjs',
  'pyodide.asm.wasm',
  'pyodide-lock.json',
  'python_stdlib.zip',
]

if (!existsSync(sourceDir)) {
  console.error('Pacote pyodide não encontrado em node_modules. Rode a instalação de dependências.')
  process.exit(1)
}

rmSync(outDir, { recursive: true, force: true })
mkdirSync(outDir, { recursive: true })

let total = 0
for (const file of RUNTIME_FILES) {
  const source = join(sourceDir, file)
  if (!existsSync(source)) {
    console.error(`Arquivo do runtime ausente no pacote pyodide: ${file}`)
    process.exit(1)
  }
  copyFileSync(source, join(outDir, file))
  total += statSync(source).size
}

console.log(
  `pyodide -> public/pyodide/ (${RUNTIME_FILES.length} arquivos, ${(total / 1024 / 1024).toFixed(1)} MB)`,
)
