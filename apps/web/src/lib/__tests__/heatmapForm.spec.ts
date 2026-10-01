import { describe, expect, it } from 'vitest'

import {
  availableSides,
  describeKey,
  groupRegions,
  isRegionExhausted,
  regionIndex,
  searchRegions,
  sideKey,
  topGroupOf,
} from '../heatmapForm'
import type { RegionInfo } from '../anatomapa'

function region(partial: Partial<RegionInfo> & Pick<RegionInfo, 'id'>): RegionInfo {
  return {
    label: partial.id,
    bilateral: false,
    parent: null,
    views: ['anterior'],
    ...partial,
  }
}

const REGIONS: RegionInfo[] = [
  region({ id: 'head', label: 'Cabeça', bilateral: true, parent: null, views: [] }),
  region({ id: 'face', label: 'Face', bilateral: true, parent: 'head', views: ['anterior'] }),
  region({ id: 'trunk', label: 'Tronco', bilateral: true, parent: null, views: [] }),
  region({ id: 'chest', label: 'Peito', bilateral: true, parent: 'trunk', views: [] }),
  region({
    id: 'upper_chest',
    label: 'Peito superior',
    bilateral: true,
    parent: 'chest',
    views: ['anterior'],
  }),
  region({ id: 'genital', label: 'Região genital', bilateral: false, parent: 'trunk', views: ['anterior'] }),
  region({ id: 'arm', label: 'Membro superior', bilateral: true, parent: null, views: [] }),
  region({ id: 'hand', label: 'Mão', bilateral: true, parent: 'arm', views: ['anterior', 'posterior'] }),
]

describe('sideKey', () => {
  it('returns the plain id for "both"', () => {
    expect(sideKey('hand', 'both')).toBe('hand')
  })

  it('suffixes the id for a lateralised side', () => {
    expect(sideKey('hand', 'left')).toBe('hand_left')
    expect(sideKey('hand', 'right')).toBe('hand_right')
  })
})

describe('availableSides', () => {
  it('offers all three sides when nothing was used yet', () => {
    expect(availableSides('hand', new Set())).toEqual(['both', 'left', 'right'])
  })

  it('hides left/right once "both" is used', () => {
    expect(availableSides('hand', new Set(['hand']))).toEqual([])
  })

  it('hides "both" once a single side is used, keeping the other side', () => {
    expect(availableSides('hand', new Set(['hand_left']))).toEqual(['right'])
  })

  it('offers nothing once both sides are used', () => {
    expect(availableSides('hand', new Set(['hand_left', 'hand_right']))).toEqual([])
  })
})

describe('isRegionExhausted', () => {
  it('a unilateral region is exhausted once its id is used', () => {
    expect(isRegionExhausted({ id: 'genital', bilateral: false }, new Set(['genital']))).toBe(true)
    expect(isRegionExhausted({ id: 'genital', bilateral: false }, new Set())).toBe(false)
  })

  it('a bilateral region is exhausted once both sides are covered', () => {
    expect(isRegionExhausted({ id: 'hand', bilateral: true }, new Set(['hand']))).toBe(true)
    expect(isRegionExhausted({ id: 'hand', bilateral: true }, new Set(['hand_left']))).toBe(false)
    expect(
      isRegionExhausted({ id: 'hand', bilateral: true }, new Set(['hand_left', 'hand_right'])),
    ).toBe(true)
  })
})

describe('topGroupOf', () => {
  const byId = regionIndex(REGIONS)

  it('returns the region itself when it has no parent', () => {
    expect(topGroupOf('trunk', byId).id).toBe('trunk')
  })

  it('walks up through intermediate parents to the root', () => {
    expect(topGroupOf('upper_chest', byId).id).toBe('trunk')
  })

  it('walks a single level up', () => {
    expect(topGroupOf('face', byId).id).toBe('head')
  })

  it('throws for an unknown id', () => {
    expect(() => topGroupOf('nope', byId)).toThrow('nope')
  })
})

describe('groupRegions', () => {
  it('groups every region under its root ancestor, root-first order preserved', () => {
    const groups = groupRegions(REGIONS)
    expect(groups.map((g) => g.group.id)).toEqual(['head', 'trunk', 'arm'])
  })

  it('keeps the root region itself inside its own group', () => {
    const groups = groupRegions(REGIONS)
    const trunkGroup = groups.find((g) => g.group.id === 'trunk')!
    expect(trunkGroup.regions.map((r) => r.id)).toContain('trunk')
    expect(trunkGroup.regions.map((r) => r.id)).toEqual(['trunk', 'chest', 'upper_chest', 'genital'])
  })

  it('still groups a child under its root when the root itself was filtered out', () => {
    // "head" (a raiz) já foi usado e some da lista visível; "face" (filho)
    // continua tendo que cair no grupo "Cabeça", não virar grupo próprio.
    const withoutHead = REGIONS.filter((r) => r.id !== 'head')
    const groups = groupRegions(withoutHead, REGIONS)
    const headGroup = groups.find((g) => g.group.id === 'head')!
    expect(headGroup.regions.map((r) => r.id)).toEqual(['face'])
    expect(groups.some((g) => g.group.id === 'face')).toBe(false)
  })
})

describe('searchRegions', () => {
  it('returns everything for an empty query', () => {
    expect(searchRegions(REGIONS, '  ')).toHaveLength(REGIONS.length)
  })

  it('matches case-insensitively on the label', () => {
    expect(searchRegions(REGIONS, 'peito').map((r) => r.id)).toEqual(['chest', 'upper_chest'])
  })

  it('matches a partial substring', () => {
    expect(searchRegions(REGIONS, 'genit').map((r) => r.id)).toEqual(['genital'])
  })
})

describe('describeKey', () => {
  const byId = regionIndex(REGIONS)

  it('matches a canonical id directly, side "both"', () => {
    expect(describeKey('hand', byId)).toEqual({ region: byId.get('hand'), side: 'both' })
  })

  it('splits a lateralised id of a bilateral region', () => {
    expect(describeKey('hand_left', byId)).toEqual({ region: byId.get('hand'), side: 'left' })
    expect(describeKey('hand_right', byId)).toEqual({ region: byId.get('hand'), side: 'right' })
  })

  it('returns null for an unknown key', () => {
    expect(describeKey('nope', byId)).toBeNull()
  })

  it('returns null for a lateralised suffix on a non-bilateral base', () => {
    expect(describeKey('genital_left', byId)).toBeNull()
  })
})
