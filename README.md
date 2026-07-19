<p align="center">
  <img src="assets/icon.svg" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  Biblioteca Python para mapas de calor anatômicos da superfície do corpo humano.
  Zero dependências, usa só a stdlib.
</p>

<p align="center">
  <img alt="Brasil" src="https://flagcdn.com/br.svg" width="60" />
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/dependencies-zero%20(stdlib%20only)-orange" />
</p>

<!-- placeholders: adicionar imagens reais depois -->

|  |  |
|:--:|:--:|
| ![Mapa anterior](assets/screenshots/mapa-anterior.png) | ![Mapa posterior](assets/screenshots/mapa-posterior.png) |
| ![Exemplo escorpionismo](assets/screenshots/exemplo-escorpiao.png) | ![Comparação de colormaps](assets/screenshots/colormaps.png) |

<p align="center">
  <img src="assets/screenshots/preview.png" alt="Preview de um mapa de calor anatômico gerado pela lib, vistas anterior e posterior lado a lado" width="760" />
</p>

<br>

### Sobre

**anatomapa** é uma biblioteca Python para gerar mapas de calor anatômicos da superfície
externa do corpo humano. Você associa dados quantitativos (frequência, intensidade ou
densidade de eventos) a regiões anatômicas e a lib produz um mapa colorido nas vistas
anterior e posterior, usando gradação de cores (choropleth) para mostrar a magnitude de
cada fenômeno por região.

Serve para áreas que registram a região corporal afetada como variável de análise:
acidentes com animais peçonhentos (escorpiões, serpentes, aranhas), traumas ocupacionais,
lesões esportivas, medicina forense, queimaduras e dermatologia.

### Recursos

- **Choropleth por região:** cor proporcional ao valor de cada região anatômica.
- **Vistas anterior e posterior:** renderize uma ou as duas (`view="both"`).
- **Entrada flexível:** `dict`, lista de registros, CSV e JSON. Excel `.xlsx` fica como
  extensão pós-MVP.
- **Resolvedor de nomes bilíngue PT-BR/EN:** escreva "MÃO" ou "hand" que a lib resolve para
  o id canônico, e sugere uma correção quando não reconhece o nome.
- **Rótulos bilíngues na saída:** `lang="pt"` ou `lang="en"` controla o texto escrito no SVG.
- **Regiões bilaterais:** um único valor pinta os dois lados (ex.: "mão" colore as duas mãos).
- **Colormaps próprios:** escalas de cor, legenda, título e escala (`linear` ou `log`) feitos
  do zero.
- **Export SVG:** saída vetorial determinística (`.save()`, `.to_svg()`), com preview inline
  no Jupyter.
- **Zero dependências externas:** só a stdlib do Python. Sem matplotlib, pandas, numpy ou pillow.

### Requisitos

- <a href="https://www.python.org/downloads/" target="_blank" rel="noreferrer">Python</a> 3.10 ou mais recente.
- Nenhuma dependência externa. A lib usa apenas a biblioteca padrão (stdlib).

### Instalação e uso

> A lib ainda não está publicada no PyPI (a publicação é um passo futuro do roadmap).
> Por enquanto, use clonando o repositório.

No terminal, clone o projeto e entre na pasta:

```bash
git clone https://github.com/pedrorcruzz/anatomapa.git
cd anatomapa
```

Depois, importe a lib no seu script Python:

```python
import anatomapa as am

fig = am.heatmap({"MÃO": 5153, "PÉ": 13666, "cabeça": 845})
fig.save("mapa.svg")
```

### Exemplo

Gerar um mapa a partir de um `dict` com nomes em PT-BR, nas duas vistas, com colormap `reds`
e rótulos em português:

```python
import anatomapa as am

# Nomes em PT ou EN, o resolvedor bilíngue converte para o id canônico
dados = {"MÃO": 5153, "PÉ": 13666, "ANTE-BRAÇO": 974, "cabeça": 845}

fig = am.heatmap(
    dados,
    view="both",          # anterior + posterior
    cmap="reds",
    scale="frequency",
    lang="pt",            # rótulos escritos em português no SVG
    title="Topografia das picadas",
)

fig.save("mapa.svg")      # exporta o SVG
svg_text = fig.to_svg()   # ou pega a string do SVG
```

Ler os dados de um CSV (você declara as colunas, nada é adivinhado):

```python
import anatomapa as am

dados = am.from_csv("lesoes.csv", region_col="regiao", value_col="total")
fig = am.heatmap(dados, view="anterior", cmap="reds", lang="pt")
fig.save("lesoes.svg")
```

Nomes fora do padrão? Passe um de-para com `region_map`:

```python
fig = am.heatmap(dados, region_map={"Membro Sup Dir": "arm"})
```

Utilidades:

```python
am.list_regions()             # lista as regiões disponíveis
am.load_dataset("escorpiao")  # carrega um dataset de exemplo
```

### Licença

Distribuído sob a licença **MIT**. Veja o arquivo <a href="LICENSE">LICENSE</a> para detalhes.

### Créditos

- **Pedro Rosa** (programador/criador)
- **Marcelo Reis** (professor)
- **Mozart Melo** (coordenador/orientador)
- **Centro Universitário CESMAC** (instituição)

<br>

<p align="center">
  ⭐ <strong>Se o anatomapa te ajudou, deixa uma estrela no repositório!</strong> Ajuda muito o projeto a crescer. ⭐
</p>
