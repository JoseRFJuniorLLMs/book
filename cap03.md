# Capítulo 3 — Sua Primeira Query em 10 Minutos: Hello World no Espaço de Poincaré

> *"Quem luta com monstros deve cuidar para que, ao fazê-lo, não se transforme também em monstro. Se olhares demasiado tempo para um abismo, o abismo olhará de volta para ti."*
> — Friedrich Nietzsche, *Além do Bem e do Mal*

Chega de teoria. Neste capítulo, vamos colocar as mãos na massa. Em dez minutos, você terá um banco hiperbólico rodando, uma coleção criada no disco de Poincaré, nós inseridos com coordenadas que respeitam a curvatura do espaço, e queries NQL retornando resultados. Nenhuma linha de código será desperdiçada: cada instrução aqui é executável e reproduzível.

---

## 3.1 Verificando a Instalação

O NietzscheDB expõe duas interfaces: **gRPC** (framework de comunicação remota do Google, baseado em HTTP/2 e Protocol Buffers, que permite chamadas de função entre máquinas com alta performance e tipagem forte) na porta `50051` (protocolo binário, alta performance) e **HTTP** na porta `8080` (dashboard e API REST). Antes de qualquer operação, confirme que o servidor está respondendo.

### Health check via HTTP

```bash
curl http://localhost:8080/api/health
```

Resposta esperada:

```json
{"status": "ok", "version": "0.9.x", "uptime_secs": 12345}
```

### Estatísticas do servidor

```bash
curl http://localhost:8080/api/stats
```

Este endpoint retorna o número de coleções, nós totais, arestas, uso de memória e o backend de vetores ativo (`gpu` ou `cpu`). É o primeiro reflexo que o abismo devolve quando você olha para ele.

### Listando coleções existentes

```bash
curl http://localhost:8080/api/collections
```

Se o servidor acabou de ser instalado, a lista estará vazia. Vamos mudar isso.

---

## 3.2 Criando uma Coleção no Disco de Poincaré

Uma **coleção** no NietzscheDB é o equivalente a uma tabela, mas com geometria embutida. Cada coleção define:

- **Dimensionalidade** do espaço vetorial (tipicamente 128).
- **Métrica** de distância (`poincare`, `cosine`, `euclidean`).
- **Parâmetros HNSW** (Hierarchical Navigable Small World — estrutura de índice em grafos multi-camada para busca aproximada de vizinhos mais próximos em tempo $O(\log N)$) para o índice de busca aproximada.

Vamos criar nossa primeira coleção usando Python e o SDK gRPC:

```python
import grpc
import sys
sys.path.insert(0, 'sdks/python')

from nietzschedb.proto import nietzsche_pb2 as pb
from nietzschedb.proto import nietzsche_pb2_grpc as rpc

# Conexao local (sem TLS)
channel = grpc.insecure_channel('localhost:50051')
stub = rpc.NietzscheDBStub(channel)

# Criar colecao com metrica de Poincare, 128 dimensoes
request = pb.CreateCollectionRequest(
    name="hello_poincare",
    dimension=128,
    metric="poincare",
    hnsw_m=16,
    hnsw_ef_construction=200,
)
response = stub.CreateCollection(request, timeout=10)
print(f"Colecao criada: {response}")
```

O parâmetro `metric="poincare"` é o que diferencia este banco de qualquer outro banco vetorial. Não estamos num espaço plano. Estamos dentro de uma bola unitária onde a distância entre dois pontos explode exponencialmente conforme nos aproximamos da borda.

### Confirmando a criação

```python
from google.protobuf import empty_pb2

stats = stub.GetStats(empty_pb2.Empty(), timeout=10)
print(f"Total de colecoes: {stats.total_collections}")

collections = stub.ListCollections(empty_pb2.Empty(), timeout=10)
for c in collections.collections:
    print(f"  - {c.name}: {c.dimension}D, metrica={c.metric}")
```

Ou via HTTP:

```bash
curl http://localhost:8080/api/collections
```

---

## 3.3 A Restrição Fundamental: $\|x\| < 1$

Antes de inserir qualquer nó, precisamos entender a **única regra inviolável** do modelo de Poincaré:

$$\forall\, x \in \mathbb{B}^n, \quad \|x\| < 1$$

Onde $\mathbb{B}^n = \{x \in \mathbb{R}^n : \|x\| < 1\}$ é a bola aberta unitária em $n$ dimensões.

**Todo vetor de coordenadas deve ter norma estritamente menor que 1.** O servidor rejeita qualquer ponto com $\|x\| \geq 1$. Isso não é um detalhe técnico — é a lei da física deste espaço. Um ponto na borda ($\|x\| = 1$) estaria no infinito hiperbólico; um ponto fora simplesmente não existe.

### Magnitude como profundidade hierárquica

No NietzscheDB, a norma do vetor carrega semântica:

| Magnitude $\|x\|$ | Significado | Exemplo |
|---|---|---|
| $\approx 0.1$ | Conceito raiz, altamente abstrato | "Ser", "Existência" |
| $\approx 0.3$ | Categoria geral | "Animal", "Ciência" |
| $\approx 0.5$ | Conceito intermediário | "Mamífero", "Física" |
| $\approx 0.7$ | Conceito específico | "Gato Persa", "Mecânica Quântica" |
| $\approx 0.9$ | Folha, instância concreta | "Meu gato Felix", "Experimento de Stern-Gerlach" |

Nós perto do **centro** da bola de Poincaré são abstratos e genéricos — como raízes de uma árvore. Nós perto da **borda** são específicos e concretos — como folhas. A magnitude **é** a profundidade na hierarquia.

Isso surge naturalmente da métrica hiperbólica. Numa árvore, o número de nós cresce exponencialmente com a profundidade. O disco de Poincaré tem exatamente essa propriedade: o "espaço disponível" próximo à borda cresce exponencialmente, acomodando a explosão combinatória de conceitos específicos.

---

## 3.4 Inserindo o Primeiro Nó

Vamos inserir um nó que representa o conceito "Filosofia" — abstrato, portanto com magnitude baixa:

```python
import uuid
import math

def make_poincare_vector(dim: int, magnitude: float, direction_seed: int = 42):
    """Cria um vetor no disco de Poincare com magnitude especifica."""
    import random
    rng = random.Random(direction_seed)

    # Gera direcao aleatoria unitaria
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    unit = [x / norm for x in raw]

    # Escala para a magnitude desejada (deve ser < 1.0)
    assert magnitude < 1.0, "Magnitude deve ser < 1.0 (restricao de Poincare)"
    return [x * magnitude for x in unit]


# Conceito abstrato: magnitude 0.15 (perto do centro)
filosofia_id = str(uuid.uuid4())
coords = make_poincare_vector(dim=128, magnitude=0.15, direction_seed=1)

node = pb.InsertNodeRequest(
    collection="hello_poincare",
    id=filosofia_id,
    content='{"nome": "Filosofia", "tipo": "disciplina", "node_label": "Filosofia"}',
    node_type="Semantic",
    coordinates=coords,
    energy=0.8,
)
stub.InsertNode(node, timeout=10)
print(f"No inserido: {filosofia_id} (Filosofia, mag={0.15})")
```

Observe os campos:

- **`id`**: UUID único. O servidor exige formato UUID válido.
- **`content`**: JSON livre com metadados. Aqui mora a riqueza semântica.
- **`node_type`**: Um dos quatro tipos nativos — `Semantic`, `Episodic`, `Concept`, `DreamSnapshot`.
- **`coordinates`**: Vetor de 128 dimensões, norma = 0.15 (dentro da bola).
- **`energy`**: Valor entre 0 e 1 que representa a "vitalidade" do nó. Nós com energia baixa podem ser podados pelo motor de agência.

### Construindo um mini-grafo

Vamos adicionar mais nós para formar uma hierarquia:

```python
# Nos do grafo: conceito → sub-conceito → instancia
nos = [
    ("Filosofia",           0.15, 1,  0.8),
    ("Etica",               0.35, 2,  0.7),
    ("Epistemologia",       0.35, 3,  0.7),
    ("Utilitarismo",        0.55, 4,  0.6),
    ("Deontologia",         0.55, 5,  0.6),
    ("Empirismo",           0.55, 6,  0.6),
    ("Jeremy Bentham",      0.75, 7,  0.5),
    ("Immanuel Kant",       0.75, 8,  0.5),
    ("David Hume",          0.75, 9,  0.5),
    ("O Principe",          0.85, 10, 0.4),
]

node_ids = {}
for nome, mag, seed, energy in nos:
    nid = str(uuid.uuid4())
    node_ids[nome] = nid
    coords = make_poincare_vector(128, mag, seed)

    stub.InsertNode(pb.InsertNodeRequest(
        collection="hello_poincare",
        id=nid,
        content=f'{{"nome": "{nome}", "node_label": "{nome}"}}',
        node_type="Semantic",
        coordinates=coords,
        energy=energy,
    ), timeout=10)
    print(f"  + {nome} (mag={mag}, energy={energy})")

print(f"\n{len(nos)} nos inseridos.")
```

### Conectando com arestas

Nós sem arestas são átomos isolados. Vamos criar a estrutura:

```python
# Definir relacoes hierarquicas
arestas = [
    ("Filosofia",      "Etica",          "CONTAINS"),
    ("Filosofia",      "Epistemologia",  "CONTAINS"),
    ("Etica",          "Utilitarismo",   "CONTAINS"),
    ("Etica",          "Deontologia",    "CONTAINS"),
    ("Epistemologia",  "Empirismo",      "CONTAINS"),
    ("Utilitarismo",   "Jeremy Bentham", "RELATED_TO"),
    ("Deontologia",    "Immanuel Kant",  "RELATED_TO"),
    ("Empirismo",      "David Hume",     "RELATED_TO"),
    ("David Hume",     "Immanuel Kant",  "TEMPORAL_NEXT"),
    ("O Principe",       "Jeremy Bentham", "INFLUENCES"),
]

for src, dst, rel in arestas:
    stub.InsertEdge(pb.InsertEdgeRequest(
        collection="hello_poincare",
        source=node_ids[src],
        target=node_ids[dst],
        relation=rel,
        weight=1.0,
    ), timeout=10)
    print(f"  {src} --[{rel}]--> {dst}")

print(f"\n{len(arestas)} arestas criadas.")
```

Os tipos de aresta usados aqui são:

- **`CONTAINS`**: Relação hierárquica pai-filho. O nó-pai "contém" o nó-filho.
- **`RELATED_TO`**: Associação semântica genérica entre conceitos.
- **`TEMPORAL_NEXT`**: Sequência temporal — "Kant veio depois de Hume" (na influência filosófica).
- **`INFLUENCES`**: Relação de influência — Maquiavel influenciou o pensamento de Bentham.

Outros tipos comuns incluem `HEBBIAN_VISUAL` (co-ativação visual, usado pelo sistema de percepção da EVA) e tipos customizados que você mesmo pode definir.

---

## 3.5 Sua Primeira Query NQL

> **Na Prática:** Uma query language é a forma de "perguntar" coisas ao banco de dados. O NQL permite filtrar nós por propriedades (energia, tipo), percorrer arestas entre nós, e executar operações específicas como difusão de ativação. Se você conhece SQL para bancos relacionais ou Cypher para Neo4j, o NQL é o equivalente para o NietzscheDB.

O NQL (*Nietzsche Query Language*) é a linguagem de consulta inspirada em Cypher (Neo4j), mas adaptada para o modelo hiperbólico. Vejamos três queries fundamentais:

### Query 1: Filtrar nós por energia

```
MATCH (n:Semantic) WHERE n.energy > 0.5 RETURN n
```

Em Python:

```python
result = stub.QueryNodes(pb.QueryRequest(
    collection="hello_poincare",
    nql='MATCH (n:Semantic) WHERE n.energy > 0.5 RETURN n',
), timeout=10)

print(f"Nos com energia > 0.5:")
for node in result.nodes:
    print(f"  - {node.id[:8]}... | energy={node.energy:.2f} | {node.content}")
```

Esta query retorna apenas nós do tipo `Semantic` cuja energia é superior a 0.5. No nosso grafo, isso filtra os conceitos mais "vivos" — Filosofia (0.8), Ética (0.7), Epistemologia (0.7), Utilitarismo (0.6), Deontologia (0.6) e Empirismo (0.6).

### Query 2: Travessia de arestas

```
MATCH (a)-[:CONTAINS]->(b) RETURN a, b
```

```python
result = stub.QueryNodes(pb.QueryRequest(
    collection="hello_poincare",
    nql='MATCH (a)-[:CONTAINS]->(b) RETURN a, b',
), timeout=10)

print("Relacoes CONTAINS:")
for node in result.nodes:
    print(f"  {node.content}")
```

Esta query percorre todas as arestas do tipo `CONTAINS`, devolvendo pares (pai, filho). É assim que você navega a hierarquia — do abstrato ao concreto, do centro à borda.

### Query 3: Difusão a partir de um nó

> **Na Prática:** DIFFUSE é uma operação exclusiva do NietzscheDB que simula a propagação de "ativação" pela rede, semelhante ao modo como um impulso nervoso se espalha por neurônios. Ao contrário do KNN (que encontra vizinhos por proximidade geométrica), o DIFFUSE encontra nós relevantes pela *estrutura de conexões* do grafo — um nó distante geometricamente pode ser altamente relevante se estiver bem conectado ao nó semente.

```
DIFFUSE FROM <node_id> LIMIT 10
```

```python
result = stub.QueryNodes(pb.QueryRequest(
    collection="hello_poincare",
    nql=f'DIFFUSE FROM {node_ids["Filosofia"]} LIMIT 10',
), timeout=10)

print("Difusao a partir de Filosofia:")
for node in result.nodes:
    print(f"  - {node.content}")
```

`DIFFUSE` é uma operação única do NietzscheDB: a partir de um nó semente, ela propaga ativação pela rede, seguindo arestas ponderadas. O resultado é uma lista de nós ordenados por "proximidade de ativação" — não distância geométrica, mas relevância na estrutura do grafo.

---

## 3.6 Busca KNN no Espaço Hiperbólico

> **Na Prática:** KNN (K-Nearest Neighbors) é a operação de encontrar os K pontos mais próximos de um ponto de referência. É a busca fundamental de qualquer banco vetorial: dado um conceito, quais são os conceitos mais semelhantes? No NietzscheDB, a "proximidade" é medida pela distância de Poincaré (hiperbólica), não pela distância euclidiana comum — o que significa que a hierarquia dos conceitos influencia diretamente os resultados.

A busca por vizinhos mais próximos (KNN) no NietzscheDB usa a **distância de Poincaré**:

$$d(u, v) = \text{arcosh}\!\left(1 + \frac{2\,\|u - v\|^2}{(1 - \|u\|^2)(1 - \|v\|^2)}\right)$$

Esta fórmula merece uma pausa. Observe o denominador: $(1 - \|u\|^2)(1 - \|v\|^2)$. Quando ambos os pontos estão perto da borda ($\|u\| \to 1$ e $\|v\| \to 1$), o denominador tende a zero e a distância **explode**. Dois pontos que parecem geometricamente próximos no disco podem estar hiperbolicamente distantes se ambos estiverem perto da fronteira, mas em direções diferentes.

Inversamente, dois pontos perto do **centro** ($\|u\| \approx 0$) têm distância quase euclidiana entre si. O centro é "pequeno" — poucos conceitos abstratos, todos próximos. A periferia é "enorme" — infinitos conceitos específicos, cada um isolado no seu canto do espaço.

É por isso que esta métrica é perfeita para hierarquias. A matemática do espaço hiperbólico naturalmente reproduz a geometria das árvores.

### Executando uma busca KNN

```python
# Buscar os 5 vizinhos mais proximos de "Etica"
etica_coords = make_poincare_vector(128, 0.35, direction_seed=2)

knn_result = stub.SearchKNN(pb.KNNRequest(
    collection="hello_poincare",
    vector=etica_coords,
    k=5,
), timeout=10)

print("5 vizinhos mais proximos de 'Etica':")
for hit in knn_result.results:
    print(f"  - {hit.id[:8]}... | dist={hit.distance:.4f} | {hit.content}")
```

O HNSW (*Hierarchical Navigable Small World*) garante que essa busca é $O(\log n)$ mesmo com milhões de nós. É o índice que o NietzscheDB constrói automaticamente ao inserir cada nó na coleção. Os parâmetros `hnsw_m` e `hnsw_ef_construction` controlam a qualidade versus velocidade dessa estrutura.

---

## 3.7 O Dashboard: Olhando para o Abismo

Abra o navegador em:

```
http://localhost:8080
```

O dashboard do NietzscheDB exibe:

1. **Visão geral**: Coleções, nós totais, arestas, uso de memória.
2. **Grafo interativo**: Visualização dos nós e arestas com layout baseado nas coordenadas de Poincaré. Os nós centrais aparecem no meio; os periféricos, nas bordas.
3. **Explorador de coleções**: Selecione `hello_poincare` e veja a árvore que acabamos de construir.
4. **Console NQL**: Execute queries diretamente no browser.

A API HTTP também expõe endpoints úteis para integração:

```bash
# Grafo da colecao (JSON com nos e arestas para visualizacao)
curl http://localhost:8080/api/graph?collection=hello_poincare

# Informacoes da colecao
curl http://localhost:8080/api/collections/hello_poincare

# Saude do servidor
curl http://localhost:8080/api/health

# Estatisticas globais
curl http://localhost:8080/api/stats
```

---

## 3.8 Seu Primeiro Algoritmo de Grafo: PageRank

> **Na Prática:** PageRank é o algoritmo inventado por Larry Page (americano, 1973–, cofundador da Google e inventor do PageRank) para classificar páginas web por importância. A ideia é simples: um nó é importante se outros nós importantes apontam para ele. No NietzscheDB, o PageRank identifica quais conceitos no grafo de conhecimento são os mais "influentes" — tipicamente os nós centrais e abstratos que conectam muitas sub-árvores.

O NietzscheDB inclui algoritmos de grafo nativos, executados diretamente sobre a estrutura em memória. Vamos rodar **PageRank** para descobrir quais conceitos são os mais "influentes" na nossa rede:

```python
pagerank_result = stub.RunPageRank(pb.PageRankRequest(
    collection="hello_poincare",
    damping=0.85,
    iterations=100,
    tolerance=1e-6,
), timeout=30)

print("PageRank — Conceitos mais influentes:")
ranked = sorted(pagerank_result.scores, key=lambda s: s.score, reverse=True)
for entry in ranked[:5]:
    print(f"  {entry.node_id[:8]}... | score={entry.score:.6f}")
```

O parâmetro `damping=0.85` é o clássico fator de amortecimento do PageRank original de Sergey Brin (russo-americano, 1973–, cofundador da Google) e Page. Ele significa que, a cada passo, há 85% de chance de seguir uma aresta e 15% de "teletransportar" para um nó aleatório.

No nosso grafo, "Filosofia" deverá ter o maior score — é o nó raiz de onde tudo emana. "Ética" vem em segundo, por ser o hub intermediário com mais conexões descendentes. Os nós-folha como "O Príncipe" terão scores baixos: recebem pouca ativação do restante da rede.

Esse resultado não é surpresa: o PageRank, aplicado sobre uma hierarquia no disco de Poincaré, naturalmente destaca os nós **centrais** (magnitude baixa) como os mais influentes. A geometria hiperbólica e o algoritmo de grafo concordam.

---

## 3.9 Exemplo Completo: Script Unificado

Aqui está o script completo que reúne tudo o que vimos. Salve como `hello_poincare.py` e execute:

```python
#!/usr/bin/env python3
"""Hello World no espaco de Poincare — NietzscheDB em 10 minutos."""

import grpc
import uuid
import math
import random
import sys

sys.path.insert(0, 'sdks/python')

from nietzschedb.proto import nietzsche_pb2 as pb
from nietzschedb.proto import nietzsche_pb2_grpc as rpc
from google.protobuf import empty_pb2

# ---------- Conexao ----------
channel = grpc.insecure_channel('localhost:50051')
stub = rpc.NietzscheDBStub(channel)

# Health check
stats = stub.GetStats(empty_pb2.Empty(), timeout=10)
print(f"Servidor ativo | colecoes={stats.total_collections}")

# ---------- Criar colecao ----------
try:
    stub.CreateCollection(pb.CreateCollectionRequest(
        name="hello_poincare",
        dimension=128,
        metric="poincare",
        hnsw_m=16,
        hnsw_ef_construction=200,
    ), timeout=10)
    print("Colecao 'hello_poincare' criada.")
except grpc.RpcError as e:
    if "already exists" in str(e.details()):
        print("Colecao 'hello_poincare' ja existe.")
    else:
        raise

# ---------- Helper ----------
def poincare_vec(dim, magnitude, seed=42):
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x * magnitude / norm for x in raw]

# ---------- Inserir nos ----------
nos = [
    ("Filosofia",      0.15, 1,  0.8),
    ("Etica",          0.35, 2,  0.7),
    ("Epistemologia",  0.35, 3,  0.7),
    ("Utilitarismo",   0.55, 4,  0.6),
    ("Deontologia",    0.55, 5,  0.6),
    ("Empirismo",      0.55, 6,  0.6),
    ("Jeremy Bentham", 0.75, 7,  0.5),
    ("Immanuel Kant",  0.75, 8,  0.5),
    ("David Hume",     0.75, 9,  0.5),
    ("O Principe",     0.85, 10, 0.4),
]

ids = {}
for nome, mag, seed, energy in nos:
    nid = str(uuid.uuid4())
    ids[nome] = nid
    stub.InsertNode(pb.InsertNodeRequest(
        collection="hello_poincare",
        id=nid,
        content=f'{{"nome": "{nome}", "node_label": "{nome}"}}',
        node_type="Semantic",
        coordinates=poincare_vec(128, mag, seed),
        energy=energy,
    ), timeout=10)
print(f"{len(nos)} nos inseridos.")

# ---------- Inserir arestas ----------
arestas = [
    ("Filosofia",      "Etica",          "CONTAINS"),
    ("Filosofia",      "Epistemologia",  "CONTAINS"),
    ("Etica",          "Utilitarismo",   "CONTAINS"),
    ("Etica",          "Deontologia",    "CONTAINS"),
    ("Epistemologia",  "Empirismo",      "CONTAINS"),
    ("Utilitarismo",   "Jeremy Bentham", "RELATED_TO"),
    ("Deontologia",    "Immanuel Kant",  "RELATED_TO"),
    ("Empirismo",      "David Hume",     "RELATED_TO"),
    ("David Hume",     "Immanuel Kant",  "TEMPORAL_NEXT"),
    ("O Principe",       "Jeremy Bentham", "INFLUENCES"),
]

for src, dst, rel in arestas:
    stub.InsertEdge(pb.InsertEdgeRequest(
        collection="hello_poincare",
        source=ids[src],
        target=ids[dst],
        relation=rel,
        weight=1.0,
    ), timeout=10)
print(f"{len(arestas)} arestas criadas.")

# ---------- Query NQL ----------
print("\n--- NQL: nos com energia > 0.5 ---")
r = stub.QueryNodes(pb.QueryRequest(
    collection="hello_poincare",
    nql='MATCH (n:Semantic) WHERE n.energy > 0.5 RETURN n',
), timeout=10)
for n in r.nodes:
    print(f"  {n.content}")

# ---------- KNN ----------
print("\n--- KNN: 3 vizinhos de 'Etica' ---")
knn = stub.SearchKNN(pb.KNNRequest(
    collection="hello_poincare",
    vector=poincare_vec(128, 0.35, seed=2),
    k=3,
), timeout=10)
for hit in knn.results:
    print(f"  dist={hit.distance:.4f} | {hit.content}")

# ---------- PageRank ----------
print("\n--- PageRank ---")
pr = stub.RunPageRank(pb.PageRankRequest(
    collection="hello_poincare",
    damping=0.85,
    iterations=100,
    tolerance=1e-6,
), timeout=30)
ranked = sorted(pr.scores, key=lambda s: s.score, reverse=True)
for entry in ranked[:5]:
    # Encontrar nome pelo ID
    nome = next((n for n, nid in ids.items() if nid == entry.node_id), "?")
    print(f"  {nome:20s} | score={entry.score:.6f}")

print("\nHello, Poincare!")
```

---

## 3.10 O Que Acabou de Acontecer

Recapitulemos o que construímos nestes 10 minutos:

1. **Uma coleção hiperbólica** com métrica de Poincaré em 128 dimensões.
2. **10 nós semânticos** organizados em cinco níveis de profundidade, cada nível codificado pela magnitude do vetor ($0.15 \to 0.35 \to 0.55 \to 0.75 \to 0.85$).
3. **10 arestas** de quatro tipos diferentes, formando uma hierarquia conceitual.
4. **Queries NQL** para filtrar, navegar e difundir informação.
5. **Busca KNN** usando a distância de Poincaré — não a euclidiana.
6. **PageRank** para descobrir quais nós são estruturalmente centrais.

Tudo isso aconteceu dentro da bola unitária $\mathbb{B}^{128}$, onde a geometria hiperbólica naturalmente codifica o que bancos relacionais precisam de JOINs para expressar: hierarquia, especificidade e distância semântica.

A distância de Poincaré entre "Filosofia" ($\|x\| = 0.15$) e "O Principe" ($\|x\| = 0.85$) é enorme — não porque os vetores apontem em direções opostas, mas porque a **curvatura do espaço** amplifica separações na periferia. O denominador $(1 - \|u\|^2)(1 - \|v\|^2)$ garante isso algebricamente. Para "O Principe", com $\|v\| = 0.85$, temos $(1 - 0.85^2) = 0.2775$ — o espaço ao redor dele já é quase quatro vezes mais "denso" que ao redor de "Filosofia", onde $(1 - 0.15^2) = 0.9775$.

É essa assimetria que faz do modelo de Poincaré a escolha natural para grafos de conhecimento. O abismo não tem fundo — e cada nível de profundidade acomoda exponencialmente mais nós que o anterior, exatamente como uma árvore real.

---

No próximo capítulo, vamos sair do tutorial e mergulhar nas quatro geometrias cognitivas do NietzscheDB: o disco de Poincaré para hierarquia, o modelo de Klein para raciocínio lógico, a esfera de Riemann para síntese de contradições e o espaço-tempo de Minkowski para causalidade — quatro lentes sobre a mesma estrutura hiperbólica subjacente.

O abismo está começando a olhar de volta. Continue.
