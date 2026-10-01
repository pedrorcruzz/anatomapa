import { describe, expect, it } from 'vitest'

import { format, MESSAGES, translate } from '../i18n'

describe('translate', () => {
  it('returns the message for the given language', () => {
    expect(translate('en', 'tabs.manual')).toBe('Manual entry')
    expect(translate('pt', 'tabs.manual')).toBe('Entrada manual')
  })

  it('every pt key has an en counterpart and vice versa', () => {
    expect(Object.keys(MESSAGES.en).sort()).toEqual(Object.keys(MESSAGES.pt).sort())
  })
})

describe('format', () => {
  it('substitutes placeholders with the given values', () => {
    expect(format('{resolved} of {total} labels recognized', { resolved: 3, total: 5 })).toBe(
      '3 of 5 labels recognized',
    )
  })

  it('leaves an unmatched placeholder untouched', () => {
    expect(format('{missing} here', {})).toBe('{missing} here')
  })
})
