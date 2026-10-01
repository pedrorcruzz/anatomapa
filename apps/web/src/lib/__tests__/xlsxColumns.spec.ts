import { describe, expect, it } from 'vitest'

import { columnLetter, columnOptions } from '../xlsxColumns'
import type { XlsxPreview } from '../anatomapa'

describe('columnLetter', () => {
  it('spells the first 26 columns as single letters', () => {
    expect(columnLetter(0)).toBe('A')
    expect(columnLetter(3)).toBe('D')
    expect(columnLetter(25)).toBe('Z')
  })

  it('wraps into double letters past Z', () => {
    expect(columnLetter(26)).toBe('AA')
    expect(columnLetter(27)).toBe('AB')
  })
})

describe('columnOptions', () => {
  function preview(partial: Partial<XlsxPreview>): XlsxPreview {
    return { sheets: ['Dados'], sheet: 'Dados', headers: null, rows: [], columns: 0, ...partial }
  }

  it('uses the header name when there is one', () => {
    const options = columnOptions(preview({ headers: ['região', 'valor'], columns: 2 }))
    expect(options).toEqual([
      { value: 'região', label: 'A · região' },
      { value: 'valor', label: 'B · valor' },
    ])
  })

  it('falls back to the column letter when there is no header', () => {
    const options = columnOptions(preview({ headers: null, columns: 2 }))
    expect(options).toEqual([
      { value: 'A', label: 'A' },
      { value: 'B', label: 'B' },
    ])
  })

  it('falls back to the letter for a blank header cell', () => {
    const options = columnOptions(preview({ headers: ['região', '  '], columns: 2 }))
    expect(options[1]).toEqual({ value: 'B', label: 'B' })
  })
})
