import type { RegionInfo } from './anatomapa'

/** Lado de uma região bilateral, ou "both" para o valor único que pinta os dois. */
export type Side = 'both' | 'left' | 'right'

/** Chave de entrada em "values" para uma região e um lado. */
export function sideKey(regionId: string, side: Side): string {
  return side === 'both' ? regionId : `${regionId}_${side}`
}

/** Indexa a lista de regiões pelo id, para lookups O(1). */
export function regionIndex(regions: RegionInfo[]): Map<string, RegionInfo> {
  return new Map(regions.map((region) => [region.id, region]))
}

/**
 * Lados ainda disponíveis para adicionar de uma região bilateral, dadas as
 * chaves já usadas em "values". "both" e lados individuais são mutuamente
 * exclusivos: usar um esconde o outro, para não ter dois valores competindo
 * pela mesma região na mesma pintura.
 */
export function availableSides(regionId: string, usedKeys: ReadonlySet<string>): Side[] {
  if (usedKeys.has(regionId)) {
    return []
  }
  const leftUsed = usedKeys.has(`${regionId}_left`)
  const rightUsed = usedKeys.has(`${regionId}_right`)
  const sides: Side[] = []
  if (!leftUsed && !rightUsed) {
    sides.push('both')
  }
  if (!leftUsed) {
    sides.push('left')
  }
  if (!rightUsed) {
    sides.push('right')
  }
  return sides
}

/** Se uma região não tem mais nenhum lado disponível para adicionar. */
export function isRegionExhausted(
  region: Pick<RegionInfo, 'id' | 'bilateral'>,
  usedKeys: ReadonlySet<string>,
): boolean {
  if (!region.bilateral) {
    return usedKeys.has(region.id)
  }
  return availableSides(region.id, usedKeys).length === 0
}

/** O ancestral raiz de uma região (head/trunk/arm/leg), usado para agrupar o picker. */
export function topGroupOf(regionId: string, byId: ReadonlyMap<string, RegionInfo>): RegionInfo {
  let current = byId.get(regionId)
  if (!current) {
    throw new Error(`Região desconhecida: ${regionId}`)
  }
  while (current.parent) {
    const parent = byId.get(current.parent)
    if (!parent) {
      break
    }
    current = parent
  }
  return current
}

export interface RegionGroup {
  group: RegionInfo
  regions: RegionInfo[]
}

/**
 * Agrupa as regiões pelo ancestral raiz, preservando a ordem de regions.json.
 *
 * `catalog` resolve a ancestralidade e por padrão é o próprio `regions`, mas
 * quando `regions` já veio filtrado (ex.: escondendo regiões esgotadas) é
 * preciso passar a lista completa, senão uma região cujo ancestral raiz foi
 * filtrado fora perde o agrupamento correto.
 */
export function groupRegions(regions: RegionInfo[], catalog: RegionInfo[] = regions): RegionGroup[] {
  const byId = regionIndex(catalog)
  const order: RegionInfo[] = []
  const buckets = new Map<string, RegionInfo[]>()

  for (const region of regions) {
    const top = topGroupOf(region.id, byId)
    let bucket = buckets.get(top.id)
    if (!bucket) {
      bucket = []
      buckets.set(top.id, bucket)
      order.push(top)
    }
    bucket.push(region)
  }

  return order.map((group) => ({ group, regions: buckets.get(group.id) ?? [] }))
}

export interface KeyDescription {
  region: RegionInfo
  side: Side
}

/**
 * Decompõe uma chave de "values" (id canônico ou lateralizado) de volta na
 * região e no lado, para exibir um rótulo legível nas linhas da tabela.
 */
export function describeKey(key: string, byId: ReadonlyMap<string, RegionInfo>): KeyDescription | null {
  const direct = byId.get(key)
  if (direct) {
    return { region: direct, side: 'both' }
  }
  for (const side of ['left', 'right'] as const) {
    const suffix = `_${side}`
    if (key.endsWith(suffix)) {
      const base = byId.get(key.slice(0, -suffix.length))
      if (base && base.bilateral) {
        return { region: base, side }
      }
    }
  }
  return null
}

/** Filtra regiões pelo rótulo, sem diferenciar maiúsculas/acentos de caixa. */
export function searchRegions(regions: RegionInfo[], query: string): RegionInfo[] {
  const needle = query.trim().toLocaleLowerCase('pt-BR')
  if (!needle) {
    return regions
  }
  return regions.filter((region) => region.label.toLocaleLowerCase('pt-BR').includes(needle))
}
