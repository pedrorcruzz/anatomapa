<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/icon.svg?v=2" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  <strong>Pinte o corpo humano com os seus dados.</strong><br/>
  De um dicionário ou de uma planilha a um mapa de calor anatômico em SVG, pronto pra publicar,
  em poucas linhas de Python e com zero dependências.
</p>

<p align="center">
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.md"><img src="https://flagcdn.com/24x18/br.png" alt="PT-BR" /> <strong>Português</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.en.md"><img src="https://flagcdn.com/24x18/us.png" alt="EN" /> English</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/anatomapa/"><img alt="PyPI" src="https://img.shields.io/pypi/v/anatomapa?color=blue&logo=pypi&logoColor=white" /></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/depend%C3%AAncias-zero%20(s%C3%B3%20stdlib)-orange" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/hero.png?v=2" alt="Mapa de calor anatômico masculino e feminino, com legenda" width="720" />
</p>

<br>

## Sobre

**anatomapa** é uma biblioteca Python para gerar **mapas de calor anatômicos** da superfície
externa do corpo humano. Você entrega dados quantitativos por região (frequência, intensidade
ou densidade de eventos) e a lib devolve o corpo colorido, de frente e de costas,
masculino ou feminino, com a cor proporcional ao valor de cada região.

Serve pra qualquer área que registra a região corporal como variável: acidentes com animais
peçonhentos (escorpiões, serpentes, aranhas), traumas ocupacionais, lesões esportivas,
medicina forense, queimaduras e dermatologia.

- **Zero dependências:** só a stdlib do Python no núcleo; PNG/JPG é um extra opcional.
- **Determinística:** a mesma entrada gera exatamente o mesmo SVG.
- **Bilíngue:** entende nomes de região em PT-BR e EN e escreve rótulos nos dois idiomas.

## Instalação

```bash
pip install anatomapa
```

Requer **Python 3.10+** e nenhuma dependência externa.

Para gerar PNG/JPG/JPEG (saída raster), instale o extra opcional, que traz cairosvg e
Pillow. O SVG puro não precisa disso.

```bash
pip install "anatomapa[raster]"
```

As aspas importam: shells como zsh e fish tratam os colchetes como glob, então use aspas.

> Para desenvolvimento, clone o repositório: `git clone https://github.com/pedrorcruzz/anatomapa.git`

## Início rápido

```python
import anatomapa as am

fig = am.heatmap({"hand": 5153, "foot": 13666, "head": 845})
fig.save("mapa.svg")
```

Pronto: um SVG com mãos, pés e cabeça coloridos por valor. O resto deste manual é opcional.

## Parâmetros de `heatmap()`

```python
am.heatmap(values, view="anterior", body="male", lang="pt", format="svg",
           title=None, background="transparent", on_unknown="error",
           region_map=None, split=False)
```

| Parâmetro    | Valores                                                        | Padrão          | O que faz |
|--------------|----------------------------------------------------------------|-----------------|-----------|
| `values`     | `dict {região: valor}` ou pares `(região, valor)`              | obrigatório     | Dados; chave pode ser `Region`; aceita a saída dos leitores |
| `view`       | `"anterior"`, `"posterior"`, `"both"`                          | `"anterior"`    | Frente, costas, ou as duas lado a lado com uma legenda só |
| `body`       | `"male"`, `"female"`                                           | `"male"`        | Corpo masculino ou feminino |
| `lang`       | `"pt"`, `"en"`                                                 | `"pt"`          | Idioma dos rótulos escritos no SVG |
| `format`     | `"svg"`, `"png"`, `"jpg"`, `"jpeg"`                            | `"svg"`         | Saída; png/jpg/jpeg pedem `pip install anatomapa[raster]` |
| `title`      | `str` ou `None`                                                | `None`          | Título desenhado na figura |
| `background` | `"dark"`, `"light"`, `"transparent"`                           | `"transparent"` | Fundo da figura |
| `on_unknown` | `"error"`, `"skip"`, `"warn"`                                  | `"error"`       | O que fazer com nome não reconhecido |
| `region_map` | `dict {seu rótulo: id da região}`                              | `None`          | De-para de nomes seus; tem precedência |
| `split`      | `True`, `False`                                                | `False`         | Só com `view="both"`: `True` devolve o par (frente, costas) |

**`split`** só vale com `view="both"`: `False` desenha as duas vistas lado a lado numa figura
única com uma legenda; `True` devolve o **par** `(anterior, posterior)` de figuras independentes,
cada uma com a própria legenda e a mesma escala de cor. Com outra `view`, levanta `ValueError`.

```python
frente, costas = am.heatmap(dados, view="both", split=True)
frente.save("frente.png")
costas.save("costas.png")
```

Retorna um objeto [`Figure`](#saída-o-objeto-figure). Nome de região desconhecido levanta
`ResolutionError` (exceção pública da lib). A paleta de cores é sempre a **térmica**
(azul frio para laranja quente, visual de câmera térmica); não há escolha de paleta. A escala
de intensidade é sempre **linear**: a cor cresce proporcional ao valor.

## Fundo

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) ou `"transparent"` (padrão, sem
  fundo). As cores da legenda se adaptam ao fundo escolhido.

A **legenda** com a barra de valores (mín..máx, rótulo conforme `lang`) e o **degradê térmico
contínuo** sobre o corpo são nativos: sempre presentes, sem parâmetro. É a legenda que informa
os valores do mapa. Ex.: `am.heatmap(dados, background="dark")`.

## Nomes de região

A identificação é **estrita**: vale o id da região escrito exatamente como definido, ou uma
chave do seu `region_map`. Nada é adivinhado, então não existe uma segunda grafia certa para
a mesma região. Nome desconhecido levanta `ResolutionError`, listando o que falhou e sugerindo
o mais parecido. Controle com `on_unknown`: `"error"` (padrão), `"skip"` ou `"warn"`.

**No código: o enum `Region`.** `from anatomapa import Region` traz 30 constantes: os 14 ids
canônicos mais as versões `_LEFT`/`_RIGHT` das 8 bilaterais. Cada membro é a própria string do
id (`Region.TRUNK == "trunk"`), então vale como chave de `heatmap()` ou valor de `region_map`.
O ganho é autocomplete e typo virando erro imediato. `list(Region)` ou `list_regions()` listam.

**Lateralidade.** As bilaterais (braço, antebraço, mão, dedo, coxa, perna, pé, dedo do pé)
aceitam lado pelo sufixo do id: `Region.HAND_RIGHT` pinta só a direita; sem sufixo
(`Region.HAND`), o valor pinta os dois lados. Pedir lado em região central é erro.

**Seus nomes vindos da planilha: `region_map`.** Como os rótulos da sua fonte quase nunca
batem com os ids, é você quem declara a correspondência, uma vez, no código. A chave é
comparada exatamente como está na planilha, incluindo acento e caixa alta:

```python
am.heatmap({Region.TRUNK: 50, Region.HAND_LEFT: 100})  # enum (ou "trunk"/"hand_left")
am.heatmap(dados, region_map={"MÃO": Region.HAND, "ANTE-BRAÇO": Region.FOREARM})
```

## Regiões e hierarquia

São **15 regiões**. `trunk` é um **agregador hierárquico**: sem geometria própria, só distribui
valor para os filhos, que mudam conforme a vista, como em qualquer atlas de anatomia externa.
As **bilaterais** aceitam sufixo `_left`/`_right` (ex.: `hand_left`); sem sufixo, pinta os dois lados.

### Visão frontal (`view="anterior"`, padrão)

`head` (cabeça) · `chest` (peito) · `abdomen` (abdômen) · `pelvis` (pelve) ·
`arm` (braço/ombro) · `forearm` (antebraço) · `hand` (mão) · `finger` (dedos da mão) ·
`thigh` (coxa) · `leg` (perna) · `foot` (pé) · `toe` (dedos do pé).
O agregador `trunk` pinta `chest` + `abdomen` + `pelvis`.

### Visão posterior (`view="posterior"`)

`head` (cabeça) · `back` (dorso) · `buttocks` (nádegas) · `arm` (braço) ·
`forearm` (antebraço) · `hand` (mão) · `finger` (dedos da mão) · `thigh` (coxa) ·
`leg` (perna) · `foot` (pé) · `toe` (dedos do pé).
O agregador `trunk` pinta `back` + `buttocks`.

`buttocks` e `back` são exclusivas da posterior; `chest`, `abdomen` e `pelvis`, da
anterior; o resto vale nas duas. `list_regions(view=...)` filtra por vista.

**Rollup (herança pai para filhos).** Mande o dado no nível que você tiver:

```python
am.heatmap({"trunk": 2602})                                # chest+abdomen+pelvis+back herdam
am.heatmap({"chest": 900, "abdomen": 1200, "pelvis": 500})  # ou por parte
```

Um valor no pai desce automaticamente pros filhos; se você informar a parte específica, ela
usa o próprio valor. Mesma lógica em `hand` para `finger` e `foot` para `toe`.

**Região sem dado.** Região sem valor sai nativamente em **cinza neutro** (#9aa0a6),
distinto do frio: "sem dado" não se confunde com "poucos casos". Sem parâmetro.

## Entrada de dados

`heatmap()` aceita `dict` ou qualquer iterável de pares `(região, valor)`, então a saída de
todos os leitores vai direto, sem conversão:

```python
# dict puro (ou normalizado via from_dict)
fig = am.heatmap(am.from_dict({"hand": 10, "foot": 25}))

# CSV: você declara as colunas, nada é adivinhado
dados = am.from_csv("lesoes.csv", region_col="regiao", value_col="total", delimiter=",")

# JSON: objeto {"hand": 10} ou lista [{"region": "...", "value": ...}]
dados = am.from_json("lesoes.json", region_key="region", value_key="value")

# Registros: dicts, namedtuples, dataclasses e DataFrame do pandas (duck typing)
dados = am.from_records(registros, region_col="regiao", value_col="total")

# Excel .xlsx, sem dependência externa; coluna por índice, letra "D" ou nome do cabeçalho
dados = am.from_xlsx("lesoes.xlsx", sheet="2024", region_col="Região",
                     value_col="Total", header=True)
```

No `from_xlsx`, `aggregate` resolve planilhas com uma linha por caso: `"count"` conta as
ocorrências de cada região e `"sum"` soma os valores. `None` (padrão) espera uma linha por região.

## Saída: o objeto `Figure`

| Uso              | Resultado |
|------------------|-----------|
| `fig.save("mapa.svg")` | grava o arquivo; infere o formato pela extensão (`.svg`, `.png`, `.jpg`), usa o `format` do heatmap ou aceita `fig.save(caminho, format="png")` |
| `fig.to_svg()`   | devolve o SVG como `str` |
| `fig.to_png()`   | devolve o PNG como `bytes` (pede `anatomapa[raster]`) |
| `fig.to_jpeg()`  | devolve o JPEG como `bytes` (pede `anatomapa[raster]`) |
| `str(fig)`       | idem `to_svg()`, SVG puro (útil em templates) |
| célula do Jupyter | renderiza inline automaticamente |

Pra saída **raster** (PNG/JPG/JPEG), instale o extra opcional `pip install anatomapa[raster]`
(traz cairosvg e Pillow, importados só sob demanda; o núcleo segue zero dependências e o SVG
puro nunca precisa de extra). O raster usa gradientes por região que se mesclam com as regiões
vizinhas, então o visual térmico sai igual em qualquer formato. Sem o extra instalado, pedir
png/jpg/jpeg levanta `ImportError` com a dica de instalação:

```python
fig = am.heatmap(dados, format="png")
fig.save("mapa.png")
```

## Exemplo completo

Topografia de picadas de escorpião (frequência por região), do dado bruto ao mapa final:

```python
import anatomapa as am
from anatomapa import Region

dados = {Region.HEAD: 845, Region.ARM: 1831, Region.FOREARM: 974, Region.HAND: 5153,
         Region.FINGER: 8684, Region.TRUNK: 2602, Region.THIGH: 1733,
         Region.LEG: 1984, Region.FOOT: 13666, Region.TOE: 6547}

# 1. Confere os nomes antes de renderizar (dry-run, não gera nada)
resultado = am.validate(dados)
assert not resultado["unresolved"]

# 2. Gera o mapa: visual térmico em fundo escuro
fig = am.heatmap(dados, body="male", background="dark")
fig.save("mapa.svg")
```

## Utilidades

**`validate(values, body="male", region_map=None)`**
faz o dry-run: não renderiza, só mostra o que resolve e o que não.

```python
am.validate({"hand": 1, "haand": 2, "hand_right": 3})
# {'resolved': {'hand': 'hand', 'hand_right': 'hand_right'},
#  'unresolved': {'haand': {'reason': 'região desconhecida',
#                           'suggestions': ['hand', 'head', 'hand_left']}}}
```

**`list_regions(lang="pt", body="male", view=None)`** lista as regiões, cada uma como
`{"id", "label", "bilateral", "parent", "views"}`. Com `view`, filtra por vista:

```python
am.list_regions(view="posterior")
# [{'id': 'head', ..., 'views': ['anterior', 'posterior']}, {'id': 'back', ...}, ...]
```

## Galeria

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-maos.png?v=2" alt="Mãos com valores altos" width="300" />
  &nbsp;
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-perna-peito.png?v=2" alt="Pernas e peito com valores altos" width="300" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png?v=2" alt="Mesmo mapa em fundo escuro, claro e transparente, masculino e feminino" width="640" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/corpo-modelo.png?v=2" alt="Modelo anatômico masculino e feminino" width="420" />
</p>

## Licença e atribuição

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](https://github.com/pedrorcruzz/anatomapa/blob/main/LICENSE).

As silhuetas dos modelos SVG derivam de fonte em **domínio público (CC0)**; detalhes em
[`app/anatomapa/assets/ATTRIBUTION.txt`](https://github.com/pedrorcruzz/anatomapa/blob/main/app/anatomapa/assets/ATTRIBUTION.txt).

## Créditos

- **Pedro Rosa**: programador/criador
- **Marcelo Reis**: Professor do Programa de Pós-Graduação em Análise de Sistemas Ambientais, CESMAC
- **Mozart Melo**: coordenador/orientador, CESMAC
- **Centro Universitário CESMAC**: instituição

<br>

<p align="center">
  ⭐ <strong>Se o anatomapa te ajudou, deixa uma estrela no repositório!</strong> ⭐
</p>
