/**
 * Conversão de SVG para PNG inteiramente no navegador (canvas), sem tocar a
 * lib: o extra "raster" dela exige cairosvg/Pillow, que não cabem no Pyodide
 * sem micropip (decisão fechada do projeto).
 */

export interface SvgSize {
  width: number
  height: number
}

const FALLBACK_SIZE: SvgSize = { width: 800, height: 600 }

/** Codifica o SVG como data URL, seguro para `<img src>` e `canvas.drawImage`. */
export function svgToDataUrl(svg: string): string {
  const encoded = encodeURIComponent(svg).replace(/'/g, '%27').replace(/"/g, '%22')
  return `data:image/svg+xml;charset=utf-8,${encoded}`
}

/** Lê a largura/altura do SVG a partir do viewBox, ou de width/height como alternativa. */
export function parseSvgSize(svg: string, fallback: SvgSize = FALLBACK_SIZE): SvgSize {
  const viewBox = svg.match(/viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"/)
  if (viewBox) {
    const width = parseFloat(viewBox[1]!)
    const height = parseFloat(viewBox[2]!)
    if (width > 0 && height > 0) {
      return { width, height }
    }
  }

  const width = svg.match(/\swidth="([\d.]+)"/)
  const height = svg.match(/\sheight="([\d.]+)"/)
  if (width && height) {
    const w = parseFloat(width[1]!)
    const h = parseFloat(height[1]!)
    if (w > 0 && h > 0) {
      return { width: w, height: h }
    }
  }

  return fallback
}

/** Rasteriza o SVG num PNG, desenhando num canvas off-screen. Só funciona no navegador. */
export async function svgToPngBlob(svg: string, scale = 2): Promise<Blob> {
  const { width, height } = parseSvgSize(svg)
  const image = new Image()
  const url = svgToDataUrl(svg)

  await new Promise<void>((resolve, reject) => {
    image.onload = () => resolve()
    image.onerror = () => reject(new Error('Falha ao carregar o SVG para conversão em PNG.'))
    image.src = url
  })

  const canvas = document.createElement('canvas')
  canvas.width = Math.round(width * scale)
  canvas.height = Math.round(height * scale)
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Canvas 2D não disponível neste navegador.')
  }
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height)

  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob)
      } else {
        reject(new Error('Falha ao gerar o PNG.'))
      }
    }, 'image/png')
  })
}

/** Dispara o download de um Blob com o nome de arquivo dado. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
