<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/icon.svg?v=7" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  <strong>Pinte o corpo humano com os seus dados.</strong><br/>
  De um dicionário ou de uma planilha a um mapa de calor anatômico em SVG, pronto pra publicar,
  em poucas linhas de Python e com zero dependências.
</p>

<p align="center">
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.md"><img src="https://flagcdn.com/24x18/us.png" alt="EN" /> English</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.pt-BR.md"><img src="https://flagcdn.com/24x18/br.png" alt="PT-BR" /> <strong>Português</strong></a>
</p>

<p align="center">
  <a href="https://pypi.org/project/anatomapa/"><img alt="PyPI" src="https://img.shields.io/pypi/v/anatomapa?color=blue&logo=pypi&logoColor=white" /></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/depend%C3%AAncias-zero%20(s%C3%B3%20stdlib)-orange" />
  <a href="https://doi.org/10.5281/zenodo.22017924"><img alt="DOI" src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22017924-1682D4?logo=doi&logoColor=white" /></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/hero.png?v=7" alt="Mapa de calor anatômico masculino e feminino, com legenda" width="720" />
</p>

## Sobre

**anatomapa** é uma biblioteca Python para gerar **mapas de calor anatômicos** da superfície externa
do corpo humano: você entrega valores por região (frequência, intensidade ou densidade de eventos) e a
lib devolve o corpo colorido, de frente e de costas, masculino ou feminino, com a cor proporcional ao
valor. Serve pra qualquer área que registra a região corporal: peçonhentos, trauma ocupacional, lesão esportiva, forense, queimaduras e dermatologia.

- **Zero dependências:** só a stdlib do Python no núcleo; PNG/JPG é um extra opcional.
- **Determinística:** a mesma entrada gera exatamente o mesmo SVG.
- **Bilíngue:** entende nomes de região em PT-BR e EN e escreve rótulos nos dois idiomas.

## Instalação

```bash
pip install anatomapa
```

Requer **Python 3.10+**. Para gerar PNG/JPG/JPEG (saída raster), instale o extra opcional,
que traz cairosvg e Pillow. As aspas importam, zsh e fish tratam os colchetes como glob:

```bash
pip install "anatomapa[raster]"
```

## Início rápido

```python
import anatomapa as am

fig = am.heatmap({"hand": 5153, "foot": 13666, "face": 845})
fig.save("mapa.svg")
```

Pronto: um SVG com mãos, pés e face coloridos por valor. O resto deste manual é opcional.

## Exemplos rápidos

```python
import anatomapa as am
from anatomapa import Region

am.heatmap({
    Region.UPPER_CHEST: 90,
    Region.HAND: 40,
    Region.KNEE: 12,
}).save("mapa.svg")
```

Um dicionário com três regiões já basta. Região sem valor sai em cinza neutro, que significa
"sem dado", não "valor baixo"; e a mão sem sufixo de lado pinta as duas mãos.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-minimo.png?v=7" alt="Mapa com peito superior, mãos e joelhos coloridos e o resto em cinza" width="340" /></p>

```python
am.heatmap(
    {Region.LEG: 80, Region.UPPER_BACK: 30},
    view="posterior",
).save("mapa.svg")
```

`leg` é o membro inferior inteiro: um valor só desce para nádegas, coxa, joelho, perna,
tornozelo, pé e dedos. É a herança em ação: você manda o dado no nível que tiver.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-heranca.png?v=7" alt="Vista posterior com o membro inferior inteiro quente e o dorso mais frio" width="340" /></p>

```python
am.heatmap({
    Region.LEG_RIGHT: 80,        # membro inferior direito inteiro
    Region.THIGH_LEFT: 20,       # o esquerdo, segmento a segmento
    Region.LOWER_LEG_LEFT: 95,
    Region.FOOT_LEFT: 40,
    Region.UPPER_CHEST_RIGHT: 60,
}).save("mapa.svg")
```

Um lado no geral e o outro em detalhe, na mesma chamada. À direita tudo sai em 80; à esquerda pinta só
o declarado, e o dedo do pé herda 40 do pé, o ancestral mais próximo. O quadril esquerdo fica sem valor e não pinta: quem detalha assume cobrir tudo que quer pintar.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-lados.png?v=7" alt="Lado direito uniforme e lado esquerdo detalhado segmento a segmento" width="340" /></p>

```python
dados = {
    Region.UPPER_BACK: 120,
    Region.LOWER_BACK: 340,
    Region.SHOULDER_LEFT: 90,
    Region.KNEE: 55,
}

fig = am.heatmap(dados, view="both", body="female", title="Lesões por região")
fig.save("mapa.svg")
fig.save("mapa.png")  # o formato sai da extensão
```

A figura é um objeto: monte o dado numa variável, gere uma vez e salve em quantos formatos quiser,
sem recalcular nada (o `.png` pede o extra `raster`). `view="both"` desenha frente e costas com uma escala e uma legenda só.

```python
# uma linha por região; você declara as colunas, nada é adivinhado
dados = am.from_xlsx("lesoes.xlsx", sheet="2024",
                     region_col="Região", value_col="Total", header=True)

# os rótulos da planilha quase nunca batem com os ids, então o de-para é seu
de_para = {"MÃO": Region.HAND, "ANTE-BRAÇO": Region.FOREARM, "PERNA": Region.LOWER_LEG}

print(am.validate(dados, region_map=de_para))  # confere antes de desenhar
am.heatmap(dados, region_map=de_para).save("mapa.svg")
```

A resolução é estrita, então caixa alta, acento, espaço e hífen contam: é pra isso que o `region_map`
existe. `validate()` é um ensaio que não desenha nada, pra conferir o de-para antes. Atenção ao recorte:
planilha com `BRAÇO` e `ANTE-BRAÇO` em linhas separadas quer `UPPER_ARM` (o segmento acima do cotovelo),
não `ARM`, que é o membro inteiro; o mesmo vale pra `PERNA` ao lado de `COXA`, que é `LOWER_LEG`.

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
| `format`     | `"svg"`, `"png"`, `"jpg"`, `"jpeg"`                            | `"svg"`         | Padrão quando o caminho salvo não tem extensão; png/jpg/jpeg pedem o extra `raster` |
| `title`      | `str` ou `None`                                                | `None`          | Opcional: só desenha o título se for informado |
| `background` | `"dark"`, `"light"`, `"transparent"`                           | `"transparent"` | Fundo da figura |
| `on_unknown` | `"error"`, `"skip"`, `"warn"`                                  | `"error"`       | O que fazer com nome não reconhecido |
| `region_map` | `dict {seu rótulo: id da região}`                              | `None`          | De-para de nomes seus; tem precedência |
| `split`      | `True`, `False`                                                | `False`         | Só com `view="both"`, senão `ValueError`: `True` devolve o par (frente, costas) de figuras independentes com a mesma escala de cor |

Retorna um objeto [`Figure`](#saída-o-objeto-figure). Nome de região desconhecido levanta `ResolutionError`
(exceção pública da lib). A paleta é sempre a **térmica** (azul frio para laranja quente, visual de câmera térmica) e a escala sempre **linear**, sem escolha.

## Fundo e título

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) ou `"transparent"` (padrão); as cores da legenda se adaptam ao fundo escolhido.
- **`title`**: negrito, centralizado acima do corpo; título longo encolhe a fonte pra caber e o texto vai também no `<title>` do SVG. Com `split=True`, cada figura recebe o título.
- **Legenda e degradê térmico**: nativos, sem parâmetro. A escala conta só valor que realmente pinta (agregador coberto pelos filhos fica de fora), e os marcadores ganham casas decimais quando arredondar para inteiro repetiria dois deles.

## Nomes de região

A identificação é **estrita**: vale o id exato da região ou uma chave do seu `region_map`; nada é
adivinhado. Nome desconhecido levanta `ResolutionError`, listando o que falhou e sugerindo o mais parecido. Controle com `on_unknown`: `"error"` (padrão), `"skip"` ou `"warn"`.

**No código: o enum `Region`.** `from anatomapa import Region` traz 94 constantes: os 32 ids canônicos
mais as versões `_LEFT`/`_RIGHT` das 31 bilaterais. Cada membro é a própria string do id (`Region.HAND == "hand"`), com autocomplete e typo virando erro imediato.

**Lateralidade.** Todas as regiões são bilaterais, menos `genital`, central. O sufixo do id
escolhe o lado: `Region.HAND_RIGHT` pinta só a direita; sem sufixo, os dois lados. O lado é
o do **observador** (esquerda da imagem), não o anatômico; lado em região central é erro.

**Seus nomes vindos da planilha: `region_map`.** Você declara o de-para uma vez, no código; a chave é
comparada exatamente como está na fonte, com acento e caixa. Exemplo com Excel nos [Exemplos rápidos](#exemplos-rápidos).

## Regiões e hierarquia

São **32 regiões** numa árvore de até 3 níveis; a coluna **Dentro de** mostra o pai de cada uma.
Linha sem marca em Frente e Costas é **agregadora**: não desenha nada, e um valor nela desce para os filhos.

| Id | Região | Dentro de | Frente | Costas |
|----|--------|-----------|:------:|:------:|
| `head` | Cabeça | raiz |  |  |
| `face` | Face | `head` | ✓ |  |
| `skull` | Crânio | `head` |  | ✓ |
| `neck` | Pescoço | `head` | ✓ | ✓ |
| `trunk` | Tronco | raiz |  |  |
| `shoulder` | Ombro | `trunk` | ✓ | ✓ |
| `chest` | Peito | `trunk` |  |  |
| `upper_chest` | Peito superior | `chest` | ✓ |  |
| `lower_chest` | Peito inferior | `chest` | ✓ |  |
| `abdomen` | Abdômen | `trunk` |  |  |
| `upper_abdomen` | Abdômen superior | `abdomen` | ✓ |  |
| `lower_abdomen` | Abdômen inferior | `abdomen` | ✓ |  |
| `back` | Costas | `trunk` |  |  |
| `upper_back` | Dorso | `back` |  | ✓ |
| `lower_back` | Região lombar | `back` |  | ✓ |
| `genital` | Região genital | `trunk` | ✓ |  |
| `arm` | Membro superior | raiz |  |  |
| `upper_arm` | Braço | `arm` | ✓ | ✓ |
| `elbow` | Cotovelo | `arm` | ✓ | ✓ |
| `forearm` | Antebraço | `arm` | ✓ | ✓ |
| `wrist` | Punho | `arm` | ✓ | ✓ |
| `hand` | Mão | `arm` | ✓ | ✓ |
| `finger` | Dedos da mão | `hand` | ✓ | ✓ |
| `leg` | Membro inferior | raiz |  |  |
| `hip` | Quadril | `leg` | ✓ |  |
| `buttocks` | Nádegas | `leg` |  | ✓ |
| `thigh` | Coxa | `leg` | ✓ | ✓ |
| `knee` | Joelho | `leg` | ✓ | ✓ |
| `lower_leg` | Perna | `leg` | ✓ | ✓ |
| `ankle` | Tornozelo | `leg` | ✓ | ✓ |
| `foot` | Pé | `leg` | ✓ | ✓ |
| `toe` | Dedos do pé | `foot` | ✓ | ✓ |

**Herança (rollup), consciente de lado.** Mande o dado no nível que você tiver. Para pintar
cada região, a lib sobe pela árvore e usa o primeiro ancestral com valor. Três regras:

1. Sobe até achar um valor e para no primeiro.
2. Em cada degrau, o lado explícito vence o geral (`foot_left` antes de `foot`).
3. Região mais funda vence ancestral mais raso: em `{"leg_left": 10, "foot": 2}`,
   o pé esquerdo vale 2, não 10.

O caso real de perícia, um lado no geral e o outro em detalhe, é o terceiro dos [Exemplos rápidos](#exemplos-rápidos).

**Migrando da 0.3 (quebras).** `leg` era a panturrilha (agora `lower_leg`) e `arm` era o braço acima do
cotovelo (agora `upper_arm`); hoje são os membros inteiros. Desde a 0.4.0 não há mais aviso em tempo de
execução: o código antigo roda em silêncio pintando outra coisa, então confira seus usos antes de atualizar.
`pelvis` virou `hip`, filho de `leg`; `buttocks` também mudou para `leg`, então valor em `trunk` não pinta mais as nádegas. `chest`, `abdomen` e `back` viraram agregadores.

**Região sem dado** sai nativamente em **cinza neutro** (#9aa0a6), distinto do frio: "sem dado" não se confunde com "poucos casos". Sem parâmetro.

## Entrada de dados

`heatmap()` aceita `dict` ou qualquer iterável de pares `(região, valor)`, então a saída dos leitores
vai direto. Em todos, você declara as colunas; nada é adivinhado.

- **`from_dict(data)`**: normaliza um dict `{região: valor}` em pares.
- **`from_csv(fonte, region_col, value_col, delimiter=",")`**: arquivo ou string CSV.
- **`from_json(fonte, region_key, value_key)`**: objeto `{"hand": 10}` ou lista `[{"region": ..., "value": ...}]`.
- **`from_records(registros, region_col, value_col)`**: dicts, namedtuples, dataclasses e DataFrame do pandas (duck typing).
- **`from_xlsx(fonte, sheet, region_col, value_col, header, aggregate)`**: Excel `.xlsx` sem dependência externa; coluna por índice, letra `"D"` ou nome do cabeçalho. `aggregate="count"` conta uma linha por caso, `"sum"` soma e `None` (padrão) espera uma linha por região. Exemplo completo nos [Exemplos rápidos](#exemplos-rápidos).

## Saída: o objeto `Figure`

| Uso              | Resultado |
|------------------|-----------|
| `fig.save("mapa.svg")` | grava o arquivo; a extensão do caminho (`.svg`, `.png`, `.jpg`) decide o formato, `fig.save(caminho, format="png")` força outro e, sem extensão, vale o `format` do heatmap |
| `fig.to_svg()`   | devolve o SVG como `str` |
| `fig.to_png()`   | devolve o PNG como `bytes` (pede `anatomapa[raster]`) |
| `fig.to_jpeg()`  | devolve o JPEG como `bytes` (pede `anatomapa[raster]`) |
| `str(fig)`       | idem `to_svg()`, SVG puro (útil em templates) |
| célula do Jupyter | renderiza inline automaticamente |

Pra saída **raster**, instale o extra `pip install "anatomapa[raster]"` (cairosvg e Pillow, importados só
sob demanda; o núcleo segue zero dependências). A figura rasteriza com o mesmo visual térmico do SVG; sem o extra, png/jpg/jpeg levanta `ImportError` com a dica.

## Utilidades

**`validate(values, body="male", region_map=None)`** faz o dry-run: mostra o que resolve e o que não, sem renderizar.

```python
am.validate({"hand": 1, "haand": 2, "hand_right": 3})
# {'resolved': {'hand': 'hand', 'hand_right': 'hand_right'},
#  'unresolved': {'haand': {'reason': 'região desconhecida', 'suggestions': ['hand', 'head', 'hand_left']}}}
```

**`list_regions(lang="pt", body="male", view=None)`** lista as regiões, cada uma como `{"id", "label", "bilateral", "parent", "views"}`; `view` filtra por vista (agregadoras, de `views` vazio, sempre aparecem).

## Galeria

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png?v=7" alt="Mesmo mapa em fundo escuro, claro e transparente, masculino e feminino" width="640" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/corpo-modelo.png?v=7" alt="Modelo anatômico masculino e feminino" width="420" />
</p>

## Como citar

Toda release é arquivada no Zenodo com um DOI permanente. Cite o concept DOI abaixo, que
sempre resolve para a versão mais recente arquivada.

**ABNT:**

> ROSA, Pedro; REIS, Marcelo; MELO, Mozart. **anatomapa**: a Python library for anatomical
> heatmaps of the human body surface. Zenodo. DOI: 10.5281/zenodo.22017924. Disponível em:
> https://doi.org/10.5281/zenodo.22017924.

**BibTeX:**

```bibtex
@software{rosa_anatomapa,
  author    = {Rosa, Pedro and Reis, Marcelo and Melo, Mozart},
  title     = {anatomapa: a Python library for anatomical heatmaps
               of the human body surface},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22017924},
  url       = {https://doi.org/10.5281/zenodo.22017924}
}
```

O GitHub também gera a citação pronta: use o botão **Cite this repository** na barra
lateral, alimentado pelo [`CITATION.cff`](https://github.com/pedrorcruzz/anatomapa/blob/main/CITATION.cff).

## Licença e atribuição

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](https://github.com/pedrorcruzz/anatomapa/blob/main/LICENSE).

As silhuetas dos modelos SVG derivam de fonte em **domínio público (CC0)**; detalhes em
[`app/anatomapa/assets/ATTRIBUTION.txt`](https://github.com/pedrorcruzz/anatomapa/blob/main/app/anatomapa/assets/ATTRIBUTION.txt).

## Créditos

- **Pedro Rosa**: programador/criador
- **Marcelo Reis**: Professor do Programa de Pós-Graduação em Análise de Sistemas Ambientais, CESMAC
- **Mozart Melo**: coordenador/orientador, CESMAC
- **Centro Universitário CESMAC**: instituição

<p align="center">⭐ <strong>Se o anatomapa te ajudou, deixa uma estrela no repositório!</strong> ⭐</p>
