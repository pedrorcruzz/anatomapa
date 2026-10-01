import type { Lang } from './anatomapa'

/** O idioma da interface é o mesmo `lang` que a lib usa pros rótulos do mapa. */
export type UiLang = Lang

export type MessageKey =
  | 'tabs.manual'
  | 'tabs.excel'
  | 'manual.hint'
  | 'manual.empty'
  | 'manual.sideLeft'
  | 'manual.sideRight'
  | 'manual.removeRegion'
  | 'manual.decrease'
  | 'manual.increase'
  | 'manual.filterPlaceholder'
  | 'manual.clearAll'
  | 'manual.noMatches'
  | 'picker.placeholder'
  | 'picker.empty'
  | 'picker.bilateral'
  | 'picker.sideBoth'
  | 'picker.sideLeft'
  | 'picker.sideRight'
  | 'picker.allGroups'
  | 'picker.clear'
  | 'options.view'
  | 'options.view.anterior'
  | 'options.view.posterior'
  | 'options.view.both'
  | 'options.body'
  | 'options.body.male'
  | 'options.body.female'
  | 'options.title'
  | 'options.titlePlaceholder'
  | 'options.background'
  | 'options.background.light'
  | 'options.background.dark'
  | 'options.background.transparent'
  | 'footer.madeBy'
  | 'theme.label'
  | 'theme.light'
  | 'theme.dark'
  | 'map.heading'
  | 'map.regionCountSingular'
  | 'map.regionCountPlural'
  | 'map.downloadSvg'
  | 'map.downloadPng'
  | 'map.downloadPngBusy'
  | 'loading.runtime'
  | 'loading.library'
  | 'loading.ready'
  | 'loading.errorTitle'
  | 'excel.dropzoneAction'
  | 'excel.dropzoneHint'
  | 'excel.file'
  | 'excel.changeFile'
  | 'excel.sheet'
  | 'excel.headerRow'
  | 'excel.regionColumn'
  | 'excel.valueColumn'
  | 'excel.aggregateLabel'
  | 'excel.aggregateNone'
  | 'excel.aggregateNoneHint'
  | 'excel.aggregateCount'
  | 'excel.aggregateCountHint'
  | 'excel.aggregateSum'
  | 'excel.aggregateSumHint'
  | 'excel.analyze'
  | 'excel.recognizedOf'
  | 'excel.importAnother'
  | 'excel.unresolvedHint'
  | 'excel.ignore'
  | 'excel.allResolved'

export const MESSAGES: Record<UiLang, Record<MessageKey, string>> = {
  en: {
    'tabs.manual': 'Manual entry',
    'tabs.excel': 'Import Excel',
    'manual.hint': 'Search a region and add its value to the map.',
    'manual.empty': 'No region added yet.',
    'manual.sideLeft': 'left side',
    'manual.sideRight': 'right side',
    'manual.removeRegion': 'Remove region',
    'manual.decrease': 'Decrease value',
    'manual.increase': 'Increase value',
    'manual.filterPlaceholder': 'Filter added regions…',
    'manual.clearAll': 'Clear all',
    'manual.noMatches': 'No added region matches this filter.',
    'picker.placeholder': 'Search a region (e.g. hand, knee, chest)…',
    'picker.empty': 'No region found.',
    'picker.bilateral': 'bilateral',
    'picker.sideBoth': 'Both sides',
    'picker.sideLeft': 'Left',
    'picker.sideRight': 'Right',
    'picker.allGroups': 'All',
    'picker.clear': 'Clear search',
    'options.view': 'View',
    'options.view.anterior': 'Anterior',
    'options.view.posterior': 'Posterior',
    'options.view.both': 'Both',
    'options.body': 'Body',
    'options.body.male': 'Male',
    'options.body.female': 'Female',
    'options.title': 'Title (optional)',
    'options.titlePlaceholder': 'e.g. Sting topography',
    'options.background': 'Background',
    'options.background.light': 'Light',
    'options.background.dark': 'Dark',
    'options.background.transparent': 'Transparent',
    'footer.madeBy': 'Built by',
    'theme.label': 'Theme',
    'theme.light': 'Light',
    'theme.dark': 'Dark',
    'map.heading': 'Map',
    'map.regionCountSingular': 'region filled',
    'map.regionCountPlural': 'regions filled',
    'map.downloadSvg': 'Download SVG',
    'map.downloadPng': 'Download PNG',
    'map.downloadPngBusy': 'Generating…',
    'loading.runtime': 'Loading the Python runtime…',
    'loading.library': 'Installing the library…',
    'loading.ready': 'Generating the map…',
    'loading.errorTitle': 'Could not load the library',
    'excel.dropzoneAction': 'Click to choose',
    'excel.dropzoneHint': 'or drag an .xlsx file here',
    'excel.file': 'File:',
    'excel.changeFile': 'Change file',
    'excel.sheet': 'Sheet',
    'excel.headerRow': 'The first row is a header',
    'excel.regionColumn': 'Region column',
    'excel.valueColumn': 'Value column',
    'excel.aggregateLabel': 'Aggregate repeated rows',
    'excel.aggregateNone': 'None',
    'excel.aggregateNoneHint': 'one row per region; if repeated, the last one wins',
    'excel.aggregateCount': 'Count occurrences',
    'excel.aggregateCountHint': 'each row is 1 event; counts how many times the region appears',
    'excel.aggregateSum': 'Sum values',
    'excel.aggregateSumHint': 'sums the value column per region',
    'excel.analyze': 'Analyze spreadsheet',
    'excel.recognizedOf': '{resolved} of {total} labels recognized',
    'excel.importAnother': 'Import another file',
    'excel.unresolvedHint': "These spreadsheet labels don't match any id in the library. Map them to a region or ignore.",
    'excel.ignore': 'Ignore',
    'excel.allResolved': 'All labels were recognized. The map is already painted with this data.',
  },
  pt: {
    'tabs.manual': 'Entrada manual',
    'tabs.excel': 'Importar Excel',
    'manual.hint': 'Busque uma região e adicione o valor dela no mapa.',
    'manual.empty': 'Nenhuma região adicionada ainda.',
    'manual.sideLeft': 'lado esquerdo',
    'manual.sideRight': 'lado direito',
    'manual.removeRegion': 'Remover região',
    'manual.decrease': 'Diminuir valor',
    'manual.increase': 'Aumentar valor',
    'manual.filterPlaceholder': 'Filtrar regiões adicionadas…',
    'manual.clearAll': 'Limpar tudo',
    'manual.noMatches': 'Nenhuma região adicionada bate com esse filtro.',
    'picker.placeholder': 'Buscar região (ex.: mão, joelho, tórax)…',
    'picker.empty': 'Nenhuma região encontrada.',
    'picker.bilateral': 'bilateral',
    'picker.sideBoth': 'Ambos os lados',
    'picker.sideLeft': 'Esquerdo',
    'picker.sideRight': 'Direito',
    'picker.allGroups': 'Todas',
    'picker.clear': 'Limpar busca',
    'options.view': 'Vista',
    'options.view.anterior': 'Anterior',
    'options.view.posterior': 'Posterior',
    'options.view.both': 'Ambas',
    'options.body': 'Corpo',
    'options.body.male': 'Masculino',
    'options.body.female': 'Feminino',
    'options.title': 'Título (opcional)',
    'options.titlePlaceholder': 'ex.: Topografia das picadas',
    'options.background': 'Fundo',
    'options.background.light': 'Claro',
    'options.background.dark': 'Escuro',
    'options.background.transparent': 'Transparente',
    'footer.madeBy': 'Feito por',
    'theme.label': 'Tema',
    'theme.light': 'Claro',
    'theme.dark': 'Escuro',
    'map.heading': 'Mapa',
    'map.regionCountSingular': 'região preenchida',
    'map.regionCountPlural': 'regiões preenchidas',
    'map.downloadSvg': 'Baixar SVG',
    'map.downloadPng': 'Baixar PNG',
    'map.downloadPngBusy': 'Gerando…',
    'loading.runtime': 'Carregando o runtime Python…',
    'loading.library': 'Instalando a biblioteca…',
    'loading.ready': 'Gerando o mapa…',
    'loading.errorTitle': 'Não foi possível carregar a biblioteca',
    'excel.dropzoneAction': 'Clique para escolher',
    'excel.dropzoneHint': 'ou arraste um arquivo .xlsx aqui',
    'excel.file': 'Arquivo:',
    'excel.changeFile': 'Trocar arquivo',
    'excel.sheet': 'Aba',
    'excel.headerRow': 'A primeira linha é cabeçalho',
    'excel.regionColumn': 'Coluna da região',
    'excel.valueColumn': 'Coluna do valor',
    'excel.aggregateLabel': 'Agregação de linhas repetidas',
    'excel.aggregateNone': 'Nenhuma',
    'excel.aggregateNoneHint': 'uma linha por região; se repetir, a última vale',
    'excel.aggregateCount': 'Contar ocorrências',
    'excel.aggregateCountHint': 'cada linha é 1 evento; conta quantas vezes a região aparece',
    'excel.aggregateSum': 'Somar valores',
    'excel.aggregateSumHint': 'soma a coluna de valor por região',
    'excel.analyze': 'Analisar planilha',
    'excel.recognizedOf': '{resolved} de {total} rótulos reconhecidos',
    'excel.importAnother': 'Importar outro arquivo',
    'excel.unresolvedHint':
      'Esses rótulos da planilha não batem com nenhum id da lib. Mapeie para uma região ou ignore.',
    'excel.ignore': 'Ignorar',
    'excel.allResolved': 'Todos os rótulos foram reconhecidos. O mapa já está pintado com esses dados.',
  },
}

export function translate(lang: UiLang, key: MessageKey): string {
  return MESSAGES[lang][key] ?? MESSAGES.en[key] ?? key
}

/** Substitui `{chave}` no template pelo valor correspondente em `vars`. */
export function format(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in vars ? String(vars[key]) : match,
  )
}
