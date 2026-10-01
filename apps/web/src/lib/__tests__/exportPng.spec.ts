import { describe, expect, it } from 'vitest'

import { parseSvgSize, svgToDataUrl } from '../exportPng'

describe('svgToDataUrl', () => {
  it('encodes the svg as a data URL', () => {
    const url = svgToDataUrl('<svg></svg>')
    expect(url).toBe('data:image/svg+xml;charset=utf-8,%3Csvg%3E%3C%2Fsvg%3E')
  })

  it('escapes quotes so attribute values survive the data URL', () => {
    const url = svgToDataUrl('<svg viewBox="0 0 10 10"></svg>')
    expect(url).toContain('%22')
    expect(url).not.toContain('"')
  })
})

describe('parseSvgSize', () => {
  it('reads width/height from the viewBox', () => {
    expect(parseSvgSize('<svg viewBox="0 0 400 300"></svg>')).toEqual({ width: 400, height: 300 })
  })

  it('falls back to width/height attributes when there is no viewBox', () => {
    expect(parseSvgSize('<svg width="120" height="80"></svg>')).toEqual({ width: 120, height: 80 })
  })

  it('falls back to the default size when nothing matches', () => {
    expect(parseSvgSize('<svg></svg>')).toEqual({ width: 800, height: 600 })
  })

  it('uses a custom fallback when given one', () => {
    expect(parseSvgSize('<svg></svg>', { width: 10, height: 20 })).toEqual({ width: 10, height: 20 })
  })

  it('ignores a malformed viewBox with a zero dimension', () => {
    expect(parseSvgSize('<svg viewBox="0 0 0 0" width="50" height="60"></svg>')).toEqual({
      width: 50,
      height: 60,
    })
  })
})
