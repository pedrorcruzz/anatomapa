import { describe, expect, it } from 'vitest'

import { joinBase, toPythonOptions } from '../anatomapa'

describe('joinBase', () => {
  it('keeps a single slash when the base already ends with one', () => {
    expect(joinBase('/anatomapa/', 'wheels/manifest.json')).toBe('/anatomapa/wheels/manifest.json')
  })

  it('adds the missing slash when the base has none', () => {
    expect(joinBase('/anatomapa', 'pyodide/')).toBe('/anatomapa/pyodide/')
  })
})

describe('toPythonOptions', () => {
  const keys = { onUnknown: 'on_unknown', regionMap: 'region_map', view: 'view' }

  it('renames the camelCase keys to the names the library expects', () => {
    expect(toPythonOptions({ onUnknown: 'skip', regionMap: { a: 'b' } }, keys)).toEqual({
      on_unknown: 'skip',
      region_map: { a: 'b' },
    })
  })

  it('drops keys left undefined so the library defaults stay in place', () => {
    expect(toPythonOptions({ view: 'both', onUnknown: undefined }, keys)).toEqual({ view: 'both' })
  })

  it('keeps null, which is a meaningful value for region_map', () => {
    expect(toPythonOptions({ regionMap: null }, keys)).toEqual({ region_map: null })
  })

  it('ignores keys that have no mapping', () => {
    expect(toPythonOptions({ unknownKey: 'x' }, keys)).toEqual({})
  })
})
