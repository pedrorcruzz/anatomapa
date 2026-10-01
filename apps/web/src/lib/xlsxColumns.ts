import type { XlsxPreview } from './anatomapa'

/** Letra de coluna de planilha (0 -> "A", 25 -> "Z", 26 -> "AA", ...). */
export function columnLetter(index: number): string {
  let n = index + 1
  let letters = ''
  while (n > 0) {
    const remainder = (n - 1) % 26
    letters = String.fromCharCode(65 + remainder) + letters
    n = Math.floor((n - 1) / 26)
  }
  return letters
}

export interface ColumnOption {
  /** Valor enviado para from_xlsx: nome do cabeçalho quando existe, senão a letra. */
  value: string
  /** Rótulo mostrado no seletor. */
  label: string
}

/**
 * Opções de coluna para os seletores de região/valor, priorizando o nome do
 * cabeçalho (igual à resolução que from_xlsx já faz) e caindo para a letra
 * quando não há cabeçalho ou a célula está vazia.
 */
export function columnOptions(preview: XlsxPreview): ColumnOption[] {
  return Array.from({ length: preview.columns }, (_, index) => {
    const letter = columnLetter(index)
    const header = preview.headers?.[index]?.trim()
    return header
      ? { value: header, label: `${letter} · ${header}` }
      : { value: letter, label: letter }
  })
}
