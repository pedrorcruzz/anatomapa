import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const repoRoot = resolve(webDir, '..', '..')
const outDir = join(webDir, 'public', 'wheels')
const tmpDir = join(webDir, 'node_modules', '.tmp', 'wheel')

function resolvePython() {
  if (process.env.ANATOMAPA_PYTHON) {
    return process.env.ANATOMAPA_PYTHON
  }
  const venvPython = join(repoRoot, 'apps', 'venv', 'bin', 'python')
  return existsSync(venvPython) ? venvPython : 'python3'
}

function buildWheel() {
  rmSync(tmpDir, { recursive: true, force: true })
  mkdirSync(tmpDir, { recursive: true })
  try {
    execFileSync(
      resolvePython(),
      ['-m', 'build', '--wheel', '--no-isolation', '--outdir', tmpDir],
      { cwd: repoRoot, stdio: 'pipe' },
    )
  } catch (cause) {
    console.error('Falha ao construir o wheel do anatomapa.')
    console.error('Instale as ferramentas de build: pip install build setuptools')
    console.error(cause.stderr?.toString() ?? cause.message)
    process.exit(1)
  }
  const wheel = readdirSync(tmpDir).find((entry) => entry.endsWith('.whl'))
  if (!wheel) {
    console.error('Nenhum arquivo .whl foi produzido em', tmpDir)
    process.exit(1)
  }
  return wheel
}

const wheel = buildWheel()
const version = wheel.split('-')[1]

rmSync(outDir, { recursive: true, force: true })
mkdirSync(outDir, { recursive: true })
copyFileSync(join(tmpDir, wheel), join(outDir, wheel))
writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify({ wheel, version }, null, 2)}\n`)

console.log(`anatomapa ${version} -> public/wheels/${wheel}`)
