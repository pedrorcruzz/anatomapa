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
peçonhentos, traumas ocupacionais, lesões esportivas, medicina forense, queimaduras e dermatologia.

- **Zero dependências:** só a stdlib do Python no núcleo; PNG/JPG é um extra opcional.
- **Determinística:** a mesma entrada gera exatamente o mesmo SVG.
- **Bilíngue:** entende nomes de região em PT-BR e EN e escreve rótulos nos dois idiomas.

## Instalação

```bash
pip install anatomapa
```

Requer **Python 3.10+** e nenhuma dependência externa. Para gerar PNG/JPG/JPEG (saída raster),
instale o extra opcional, que traz cairosvg e Pillow; o SVG puro não precisa disso. As aspas
importam, shells como zsh e fish tratam os colchetes como glob:

```bash
pip install "anatomapa[raster]"
```

> Para desenvolvimento, clone o repositório: `git clone https://github.com/pedrorcruzz/anatomapa.git`

## Início rápido

```python
import anatomapa as am

fig = am.heatmap({"hand": 5153, "foot": 13666, "face": 845})
fig.save("mapa.svg")
```

Pronto: um SVG com mãos, pés e face coloridos por valor. O resto deste manual é opcional.

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
| `split`      | `True`, `False`                                                | `False`         | Só com `view="both"`: `True` devolve o par (frente, costas) |

**`split`** só vale com `view="both"`: `True` devolve o **par** `(anterior, posterior)` de
figuras independentes, com a mesma escala de cor. Com outra `view`, levanta `ValueError`.

Retorna um objeto [`Figure`](#saída-o-objeto-figure). Nome de região desconhecido levanta
`ResolutionError` (exceção pública da lib). A paleta de cores é sempre a **térmica**
(azul frio para laranja quente, visual de câmera térmica); não há escolha de paleta. A escala
de intensidade é sempre **linear**: a cor cresce proporcional ao valor.

## Fundo e título

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) ou `"transparent"` (padrão). As
  cores da legenda se adaptam ao fundo escolhido.
- **`title`**: quando informado, sai em negrito, centralizado em relação ao corpo, acima do
  desenho; título longo encolhe a fonte para caber e o texto segue também como `<title>` do
  SVG. Com `split=True`, cada figura recebe o título.

A **legenda** (barra de valores mín..máx, rótulo conforme `lang`) e o **degradê térmico** sobre
o corpo são nativos: sempre presentes, sem parâmetro. A escala da legenda conta só valor que
realmente pinta (agregador coberto pelos filhos não entra), e os marcadores ganham casas
decimais quando arredondar para inteiro repetiria dois deles.

## Nomes de região

A identificação é **estrita**: vale o id da região escrito exatamente como definido, ou uma
chave do seu `region_map`. Nada é adivinhado, então não existe uma segunda grafia certa para
a mesma região. Nome desconhecido levanta `ResolutionError`, listando o que falhou e sugerindo
o mais parecido. Controle com `on_unknown`: `"error"` (padrão), `"skip"` ou `"warn"`.

**No código: o enum `Region`.** `from anatomapa import Region` traz 94 constantes: os 32 ids
canônicos mais as versões `_LEFT`/`_RIGHT` das 31 bilaterais. Cada membro é a própria string do
id (`Region.HAND == "hand"`), então vale como chave de `heatmap()` ou valor de `region_map`.
O ganho é autocomplete e typo virando erro imediato. `list(Region)` ou `list_regions()` listam.

**Lateralidade.** Todas as regiões são bilaterais, menos `genital`, que é central. As bilaterais
aceitam lado pelo sufixo do id: `Region.HAND_RIGHT` pinta só a direita; sem sufixo
(`Region.HAND`), pinta os dois lados. O lado segue a convenção do **observador** (esquerda da
imagem), não a anatômica. Pedir lado em região central é erro.

**Seus nomes vindos da planilha: `region_map`.** Como os rótulos da sua fonte quase nunca
batem com os ids, é você quem declara a correspondência, uma vez, no código. A chave é
comparada exatamente como está na planilha, incluindo acento e caixa alta:

```python
am.heatmap(dados, region_map={"MÃO": Region.HAND, "ANTE-BRAÇO": Region.FOREARM})
```

## Regiões e hierarquia

São **32 regiões** numa árvore de até 3 níveis. Região **agregadora** não tem desenho próprio:
um valor nela desce para os filhos. Entre parênteses, a vista onde a região desenha:

```text
head           Cabeça (agregadora)
├─ face            Face (frente)
├─ skull           Crânio (costas)
└─ neck            Pescoço (frente e costas)
trunk          Tronco (agregadora)
├─ shoulder        Ombro (frente e costas)
├─ chest           Peito (agregadora)
│  ├─ upper_chest      Peito superior (frente)
│  └─ lower_chest      Peito inferior (frente)
├─ abdomen         Abdômen (agregadora)
│  ├─ upper_abdomen    Abdômen superior (frente)
│  └─ lower_abdomen    Abdômen inferior (frente)
├─ back            Costas (agregadora)
│  ├─ upper_back       Dorso (costas)
│  └─ lower_back       Região lombar (costas)
└─ genital         Região genital (frente; a única central)
arm            Membro superior (agregadora)
├─ upper_arm       Braço (frente e costas)
├─ elbow           Cotovelo (frente e costas)
├─ forearm         Antebraço (frente e costas)
├─ wrist           Punho (frente e costas)
└─ hand            Mão (frente e costas)
   └─ finger           Dedos da mão (frente e costas)
leg            Membro inferior (agregadora)
├─ hip             Quadril (frente)
├─ buttocks        Nádegas (costas)
├─ thigh           Coxa (frente e costas)
├─ knee            Joelho (frente e costas)
├─ lower_leg       Perna (frente e costas)
├─ ankle           Tornozelo (frente e costas)
└─ foot            Pé (frente e costas)
   └─ toe              Dedos do pé (frente e costas)
```

**Herança (rollup), consciente de lado.** Mande o dado no nível que você tiver. Para pintar
cada região, a lib sobe pela árvore e usa o primeiro ancestral com valor. Três regras:

1. Sobe até achar um valor e para no primeiro.
2. Em cada degrau, o lado explícito vence o geral (`foot_left` antes de `foot`).
3. Região mais funda vence ancestral mais raso: em `{"leg_left": 10, "foot": 2}`,
   o pé esquerdo vale 2, não 10.

O caso real de perícia é descrever um lado no geral e o outro em detalhe:

```python
am.heatmap({
    Region.LEG_RIGHT: 8,       # membro inferior direito inteiro
    Region.THIGH_LEFT: 2,      # esquerdo detalhado segmento a segmento
    Region.LOWER_LEG_LEFT: 9,
    Region.FOOT_LEFT: 4,
})
```

À direita, tudo de `hip` a `foot` sai em 8. À esquerda pinta só o declarado, mais `toe_left`
herdando 4 do pé; `hip_left` e `buttocks_left` ficam sem valor e não pintam. Quem detalha
assume a responsabilidade de cobrir tudo que quer pintar.

**Migrando da 0.3 (quebras).** `leg` e `arm` mudaram de significado: `leg` era a panturrilha
(agora `lower_leg`) e `arm` era o braço acima do cotovelo (agora `upper_arm`); hoje são os
membros inteiros. Como o código antigo continua rodando e pinta outra coisa, usar `leg` ou
`arm` emite `DeprecationWarning` apontando a sua linha e o id novo. `pelvis` deixou de existir:
virou `hip`, filho de `leg`. `buttocks` também mudou para `leg`, então valor em `trunk` não
pinta mais as nádegas. `chest`, `abdomen` e `back` seguem válidos, mas viraram agregadores.

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
| `fig.save("mapa.svg")` | grava o arquivo; a extensão do caminho (`.svg`, `.png`, `.jpg`) decide o formato, `fig.save(caminho, format="png")` força outro e, sem extensão, vale o `format` do heatmap |
| `fig.to_svg()`   | devolve o SVG como `str` |
| `fig.to_png()`   | devolve o PNG como `bytes` (pede `anatomapa[raster]`) |
| `fig.to_jpeg()`  | devolve o JPEG como `bytes` (pede `anatomapa[raster]`) |
| `str(fig)`       | idem `to_svg()`, SVG puro (útil em templates) |
| célula do Jupyter | renderiza inline automaticamente |

Pra saída **raster** (PNG/JPG/JPEG), instale o extra `pip install anatomapa[raster]` (cairosvg e
Pillow, importados só sob demanda; o núcleo segue zero dependências). Qualquer figura rasteriza
com as mesmas cores e o mesmo visual térmico do SVG. Sem o extra instalado, pedir png/jpg/jpeg
levanta `ImportError` com a dica de instalação.

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
`{"id", "label", "bilateral", "parent", "views"}`. Com `view`, filtra por vista (agregadoras,
de `views` vazio, sempre aparecem):

```python
am.list_regions(view="posterior")
# [{'id': 'head', ..., 'views': []}, {'id': 'skull', ..., 'views': ['posterior']}, ...]
```

## Galeria

<p align="center">
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
