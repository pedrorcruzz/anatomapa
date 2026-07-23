<p align="center">
  <img src="assets/icon.svg" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  Transforme dados de lesões e acidentes em mapas de calor sobre o corpo humano.
  Da planilha ao SVG pronto pra publicar, em poucas linhas de Python.
</p>

<p align="center">
  <a href="README.md"><img src="https://flagcdn.com/24x18/br.png" alt="PT-BR" /> <strong>Português</strong></a>
  &nbsp;·&nbsp;
  <a href="README.en.md"><img src="https://flagcdn.com/24x18/us.png" alt="EN" /> English</a>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/depend%C3%AAncias-zero%20(s%C3%B3%20stdlib)-orange" />
</p>

<p align="center">
  <img src="assets/screenshots/hero.png" alt="Mapa de calor anatômico masculino e feminino, com legenda" width="720" />
</p>

<br>

## Sobre

**anatomapa** é uma biblioteca Python para gerar **mapas de calor anatômicos** da superfície
externa do corpo humano. Você associa dados quantitativos (frequência, intensidade ou
densidade de eventos) a regiões anatômicas e a lib produz um mapa colorido nas vistas
anterior e posterior, com a cor proporcional ao valor de cada região.

Serve para áreas que registram a região corporal como variável de análise: acidentes com
animais peçonhentos (escorpiões, serpentes, aranhas), traumas ocupacionais, lesões
esportivas, medicina forense, queimaduras e dermatologia.

- **Zero dependências:** só a biblioteca padrão do Python. Sem matplotlib, pandas, numpy ou pillow.
- **Determinístico:** a mesma entrada gera exatamente o mesmo SVG.
- **Bilíngue:** entende nomes de região em PT-BR e EN e escreve rótulos em qualquer um dos dois.

## Instalação

Ainda não publicada no PyPI. Por enquanto, clone o repositório:

```bash
git clone https://github.com/pedrorcruzz/anatomapa.git
cd anatomapa
```

Requer **Python 3.10+**. Nenhuma dependência externa.

## Uso rápido

```python
import anatomapa as am

fig = am.heatmap(
    {"MÃO": 5153, "PÉ": 13666, "cabeça": 845},
    cmap="thermal",
    smooth=True,
    legend=True,
    background="dark",
)

fig.save("mapa.svg")     # exporta o SVG
svg = fig.to_svg()       # ou pega a string do SVG
```

Os nomes das regiões podem vir em **PT-BR ou EN**, em maiúsculas ou minúsculas: o resolvedor
converte "MÃO", "mao" ou "hand" para o mesmo id canônico, e sugere uma correção quando não
reconhece o nome.

## Parâmetros de `heatmap()`

| Parâmetro     | Valores                                             | Padrão       |
|---------------|-----------------------------------------------------|--------------|
| `values`      | `dict` `{região: valor}`                            | obrigatório  |
| `view`        | `"anterior"`, `"posterior"`                         | `"anterior"` |
| `body`        | `"male"`, `"female"`                                | `"male"`     |
| `cmap`        | `"thermal"`, `"reds"`, `"heat"`, `"viridis"`, `"blues"`, `"greens"` | `"reds"` |
| `scale`       | `"linear"`, `"log"`                                 | `"linear"`   |
| `lang`        | `"pt"`, `"en"` (idioma dos rótulos no SVG)          | `"pt"`       |
| `title`       | `str` ou `None`                                     | `None`       |
| `smooth`      | `bool` (degradê térmico contínuo)                   | `False`      |
| `legend`      | `bool` (barra de valores ao lado)                   | `False`      |
| `background`  | `"dark"`, `"light"`, `"transparent"`                | `"transparent"` |
| `on_unknown`  | `"error"`, `"skip"`, `"warn"` (nome não reconhecido)| `"error"`    |
| `region_map`  | `dict` de-para de nomes customizados                | `None`       |
| `assets_dir`  | caminho alternativo dos assets                      | `None`       |

Retorna um objeto `Figure` com `.save(caminho)`, `.to_svg()` e `str(fig)`. No Jupyter, a
figura aparece inline automaticamente.

## Entrada de dados

Além do `dict`, há leitores para os formatos mais comuns. O `heatmap()` aceita tanto um
`dict` quanto a saída dos leitores direto (não precisa converter):

```python
# CSV (você declara as colunas, nada é adivinhado)
dados = am.from_csv("lesoes.csv", region_col="regiao", value_col="total")
fig = am.heatmap(dados, cmap="thermal", lang="pt")

# JSON  (objeto {"mão": 10} ou lista [{"region": "...", "value": ...}])
fig = am.heatmap(am.from_json("lesoes.json"))

# Registros (dicts, namedtuples, dataclasses, DataFrame do pandas via duck typing)
fig = am.heatmap(am.from_records(registros, region_col="regiao", value_col="total"))

# Excel .xlsx (sem dependência externa)
dados = am.from_xlsx("lesoes.xlsx", region_col="D", value_col="E", header=True)
```

## Nomes de região

O resolvedor é tolerante: aceita **PT ou EN**, maiúsc/minúsc, **acentos**, **plurais** e
**sinônimos** ("MÃO", "mao", "hand", "mãos", "punho" → `hand`). Nomes desconhecidos **não são
chutados**: por padrão a lib **erra e sugere** o mais parecido (controle com `on_unknown`).

**Lateralidade (esquerda/direita).** As regiões bilaterais aceitam lado: escreva "mão direita"
ou "right hand" e só a mão direita acende; sem lado, pinta os dois:

```python
am.heatmap({"mão direita": 500, "mão esquerda": 20, "perna direita": 80})
```

**Seus próprios nomes.** Use `region_map` (seu rótulo → id da região, aceita ids lateralizados):

```python
am.heatmap(dados, region_map={"Membro Sup Dir": "arm", "right_hand": "hand_right"})
```

**Conferir antes de gerar (dry-run).** `validate()` mostra o que resolve e o que não, sem renderizar:

```python
am.validate({"mao": 1, "pedro": 2, "mão direita": 3})
# {'resolved': {'mao': 'hand', 'mão direita': 'hand_right'},
#  'unresolved': {'pedro': {'reason': 'região desconhecida', 'suggestions': ['dedo', ...]}}}
```

## Regiões

São 10 regiões macro. `head` e `trunk` são centrais; as demais são **bilaterais** (um único
valor pinta os dois lados):

| id        | PT-BR       | id        | PT-BR        |
|-----------|-------------|-----------|--------------|
| `head`    | Cabeça      | `thigh`   | Coxa         |
| `trunk`   | Tronco      | `leg`     | Perna        |
| `arm`     | Braço       | `foot`    | Pé           |
| `forearm` | Antebraço   | `toe`     | Dedo do pé   |
| `hand`    | Mão         | `finger`  | Dedo         |

```python
am.list_regions()          # lista id, rótulo, se é bilateral e a região-pai
```

## Galeria

Corpo masculino e feminino, vistas anterior e posterior, com paleta térmica e legenda de
valores. Fundo à escolha (escuro, claro ou transparente).

<p align="center">
  <img src="assets/screenshots/exemplo-maos.png" alt="Mãos com valores altos" width="300" />
  &nbsp;
  <img src="assets/screenshots/exemplo-perna-peito.png" alt="Pernas e peito com valores altos" width="300" />
</p>

<p align="center">
  <img src="assets/screenshots/fundos.png" alt="Mesmo mapa em fundo escuro, claro e transparente, masculino e feminino" width="640" />
</p>

<p align="center">
  <img src="assets/screenshots/corpo-modelo.png" alt="Modelo anatômico masculino e feminino" width="420" />
</p>

## Licença

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE).

As silhuetas dos modelos SVG derivam de fonte em **domínio público (CC0)**; detalhes em
[`app/anatomapa/assets/ATTRIBUTION.txt`](app/anatomapa/assets/ATTRIBUTION.txt).

## Créditos

- **Pedro Rosa** — programador/criador
- **Marcelo Reis** — professor
- **Mozart Melo** — coordenador/orientador
- **Centro Universitário CESMAC** — instituição

<br>

<p align="center">
  ⭐ <strong>Se o anatomapa te ajudou, deixa uma estrela no repositório!</strong> ⭐
</p>
