# Capítulo 5 — O Motor de Grafos Multi-Manifold: O crate `nietzsche-graph` e a gestão de curvaturas

> *"O que não me mata, fortalece-me."*
> — Friedrich Nietzsche, *Götzen-Dämmerung*

O `nietzsche-graph` é o coração anatômico do NietzscheDB. Tudo o que o banco sabe — nós, arestas, adjacência, persistência, transações — vive neste crate. Ele não é uma abstração sobre um grafo qualquer: é um motor de grafos que opera simultaneamente em múltiplas variedades geométricas, onde a curvatura não é um parâmetro — é a semântica.

Este capítulo disseca a arquitetura interna do crate, os modelos de dados, os 11 algoritmos de grafo, o sistema emocional de valência/arousal, o motor dialético hegeliano e os CRDTs semânticos para merge distribuído.

---

## 5.1 Arquitetura do Crate

O `nietzsche-graph` expõe 14 módulos públicos, cada um com responsabilidade cirurgicamente definida:

| Módulo | Responsabilidade |
|--------|-----------------|
| `model` | Tipos fundamentais: `Node`, `NodeMeta`, `Edge`, `PoincareVector`, `SparseVector` |
| `adjacency` | Índice bidirecional lock-free (`DashMap`) |
| `storage` | Persistência RocksDB com 6 column families |
| `wal` | Write-Ahead Log binário append-only |
| `db` | Coordenador dual-write (grafo + vector store) |
| `traversal` | BFS, Dijkstra, diffusion walk, greedy routing hiperbólico |
| `valence` | Dimensões emocionais (valência/arousal) e gravidade emocional |
| `schrodinger` | Arestas probabilísticas com colapso tipo Schrödinger |
| `concept_path` | Caminhos semânticos anotados com metadata por hop |
| `ego_cache` | Cache de vizinhança ego-cêntrica |
| `fulltext` | Índice full-text invertido |
| `transaction` | Transações ACID via saga pattern |
| `schema` | Validação de schema por collection |
| `encryption` | Cifra AES-GCM-256 em repouso |

As dependências externas são mínimas e deliberadas: `rocksdb` para persistência, `dashmap` para concorrência lock-free, `bincode` para serialização compacta, `ordered-float` para heaps com f64, e `rayon` para paralelismo. Nenhuma dependência em frameworks de grafos genéricos — tudo é construído de raiz para geometria hiperbólica.

---

## 5.2 O Modelo de Nó: `NodeMeta` (~108 bytes)

A decisão arquitetural mais impactante do NietzscheDB foi a separação entre metadados leves (`NodeMeta`, ~108 bytes) e o embedding pesado (`PoincareVector`, ~12 KB a 3072 dimensões). Esta cisão, documentada como "BUG A fix" na auditoria do comité técnico de 2026-02-19, resulta em speedup de 10-25x em travessias BFS que nunca precisam tocar no embedding.

O `NodeMeta` contém todos os campos necessários para filtros, energy gates e NQL:

| Campo | Tipo | Range | Semântica |
|-------|------|-------|-----------|
| `id` | `Uuid` | UUIDv4 | Identificador único |
| `depth` | `f32` | $[0, 1)$ | $\|embedding\|$ — proxy de profundidade hierárquica |
| `content` | `serde_json::Value` | JSON arbitrário | Payload semântico |
| `node_type` | `NodeType` | Enum (4 variantes) | Episodic, Semantic, Concept, DreamSnapshot |
| `energy` | `f32` | $[0.0, 1.0]$ | Nível de energia — a 0.0 o nó é podável |
| `lsystem_generation` | `u32` | $\geq 0$ | Geração L-System (0 = inserção manual) |
| `hausdorff_local` | `f32` | $[0, 2]$ | Dimensão Hausdorff local da vizinhança |
| `created_at` | `i64` | Unix timestamp | Momento de criação |
| `expires_at` | `Option<i64>` | Unix timestamp ou `None` | TTL — `None` = imortal |
| `metadata` | `HashMap<String, Value>` | Chave-valor arbitrário | Metadata extensível |
| `valence` | `f32` | $[-1.0, 1.0]$ | Eixo prazer/desprazer |
| `arousal` | `f32` | $[0.0, 1.0]$ | Intensidade emocional |
| `is_phantom` | `bool` | true/false | Cicatriz topológica após poda |

> **Na Prática:** Cada nó no NietzscheDB não é apenas um dado — é uma entidade viva com ciclo de vida. O campo `energy` determina se o nó ainda está ativo ou pronto para garbage collection. Os campos `valence` e `arousal` permitem ao banco compreender contexto emocional: uma memória com valência negativa e arousal alto (como um alerta de sistema) comporta-se de forma diferente nos resultados de busca do que uma memória calma e positiva. O campo `hausdorff_local` mede a dimensão fractal da vizinhança — se cai demasiado, o nó está isolado; se dispara, o nó está numa região patologicamente densa. Nenhum outro banco de dados monitora estas propriedades nativamente.

A profundidade `depth` merece atenção especial. No modelo de Poincaré, a norma do vetor codifica a posição hierárquica:

$$\text{depth}(v) = \|x_v\| \in [0, 1)$$

Nós próximos do centro ($\|x\| \approx 0$) representam conceitos abstratos e semânticos. Nós próximos da fronteira ($\|x\| \to 1$) representam memórias episódicas específicas. Esta não é uma convenção — é uma consequência matemática da métrica hiperbólica, onde o volume disponível cresce exponencialmente com o raio.

> **Na Prática:** Quando um banco de dados deve esquecer algo? O NietzscheDB tem três gatilhos para o esquecimento: o nó ficou sem energia (ninguém o acessa, ninguém o referencia), o nó está demasiado isolado (dimensão de Hausdorff abaixo de 0.5), ou o nó está num cluster patologicamente denso (Hausdorff acima de 1.9, um "tumor" de informação redundante). Bancos tradicionais nunca esquecem a menos que sejam explicitamente instruídos a apagar.

### Condição de Poda

Um nó é candidato a poda quando:

$$\text{isPrunable}(v) \iff E(v) \leq 0 \;\lor\; D_H^{local}(v) < 0.5 \;\lor\; D_H^{local}(v) > 1.9$$

onde $E(v)$ é a energia e $D_H^{local}$ é a dimensão de Hausdorff local. Os limiares 0.5 e 1.9 são empíricos: nós com dimensão fractal demasiado baixa são ilhas desconectadas; nós com dimensão demasiado alta são tumores topológicos.

### Nós Fantasma

Quando um nó é podado ou expira por TTL, ele não é deletado — é transformado em *phantom*. O `is_phantom = true` marca uma "cicatriz" estrutural: o nó mantém todas as suas conexões topológicas (arestas, adjacência) para que a geometria hiperbólica não colapse, mas é excluído de KNN e travessias ativas. Este mecanismo imita os traços de memória estrutural do cérebro que facilitam a reaprendizagem.

> **Na Prática:** No Neo4j, apagar um nó requer primeiro apagar todas as suas arestas — uma operação cascata que pode ser cara e destrutiva. No Pinecone, a eliminação é imediata e permanente — o vetor e todas as suas relações simplesmente desaparecem. No NietzscheDB, um nó eliminado se torna "fantasma": os seus dados desaparecem, mas a sua posição estrutural permanece como uma cicatriz topológica. Se conhecimento similar for inserido mais tarde, pode reutilizar a posição do fantasma — semelhante a como o cérebro retém o traço estrutural de uma memória esquecida, tornando a reaprendizagem mais rápida.

---

## 5.3 O Modelo de Aresta: `Edge`

Cada aresta é direcionada, tipada e transporta metadados de causalidade Minkowski:

| Campo | Tipo | Semântica |
|-------|------|-----------|
| `id` | `Uuid` | Identificador único |
| `from` | `Uuid` | Nó de origem |
| `to` | `Uuid` | Nó de destino |
| `edge_type` | `EdgeType` | Association, LSystemGenerated, Hierarchical, Pruned |
| `weight` | `f32` $\in [0, 1]$ | Peso da aresta para funções de custo |
| `lsystem_rule` | `Option<String>` | Regra L-System que criou a aresta |
| `created_at` | `i64` | Unix timestamp |
| `metadata` | `HashMap<String, Value>` | Metadata extensível |
| `minkowski_interval` | `f32` | $ds^2 = -c^2\Delta t^2 + \|\Delta x\|^2$ |
| `causal_type` | `CausalType` | Timelike, Spacelike, Lightlike, Unknown |

O campo `minkowski_interval` merece explicação. Quando uma aresta é inserida entre dois nós com timestamps e embeddings, o servidor calcula automaticamente o intervalo de Minkowski:

$$ds^2 = -c^2 (t_{target} - t_{source})^2 + \|emb_{source} - emb_{target}\|^2$$

A classificação causal segue diretamente:

- **Timelike** ($ds^2 < 0$): a origem *causou* o destino — dentro do cone de luz
- **Spacelike** ($ds^2 > 0$): eventos causalmente independentes — fora do cone de luz
- **Lightlike** ($ds^2 \approx 0$): na fronteira do cone de luz

Este mecanismo permite travessias causais: `get_causal_neighbors()` filtra por `causal_type == Timelike` para retornar apenas caminhos provavelmente causais.

### O Campo Hidráulico: Conductivity

Além dos campos nativos do `Edge`, o sistema hidráulico (crate `nietzsche-agency`) adiciona um campo semântico crítico: a **condutividade** ($\kappa$). Cada aresta transporta um $\kappa \in [0.01, 10.0]$ que modifica a distância efetiva:

$$d_{eff}(u, v) = \frac{d_{\mathbb{H}}(u, v)}{\kappa(u, v)}$$

onde $d_{\mathbb{H}}$ é a distância de Poincaré pura. A condutividade é atualizada por quatro mecanismos:

1. **LTP Hebbiano** (Long-Term Potentiation — potenciação de longo prazo, o mecanismo neural pelo qual sinapses frequentemente co-ativadas se fortalecem permanentemente): co-ativação frequente $\Rightarrow$ aumento de $\kappa$
2. **Reforço de fluxo**: taxa de fluxo alta $\Rightarrow$ aumento de $\kappa$, via $\Delta\kappa = \alpha_{flow} \cdot (f_{edge}/\bar{f} - 1) \cdot \kappa$
3. **Decay temporal**: arestas não utilizadas $\Rightarrow$ $\kappa$ decai em direção a 1.0
4. **Rebalanceador Murray**: equilíbrio fractal durante ciclos de sono

A distinção entre distância raw e efetiva é fundamental:

| Operação | Distância Utilizada |
|----------|-------------------|
| HNSW KNN (similaridade) | $d_{\mathbb{H}}$ (pura geométrica) |
| DIFFUSE walk (propagação de calor) | $d_{eff}$ (caminhos mielinizados) |
| Força gravitacional | $d_{eff}$ (atrai por canais condutivos) |
| Fluxo de calor (lei de Fourier) | $d_{eff}$: $q = \kappa \cdot \Delta E / d_{eff}$ |

---

## 5.4 Armazenamento de Adjacência

O `AdjacencyIndex` é um índice bidirecional in-memory, lock-free, respaldado por `DashMap` — um hashmap com sharded locking fino que suporta leituras e escritas concorrentes sem lock global.

A estrutura interna:

```
outgoing: DashMap<Uuid, Vec<AdjEntry>>   // source -> [(edge_id, target, weight, edge_type)]
incoming: DashMap<Uuid, Vec<AdjEntry>>   // target -> [(edge_id, source, weight, edge_type)]
```

Cada `AdjEntry` contém `(edge_id, neighbor_id, weight, edge_type)` — informação suficiente para decisões de travessia sem acessar o RocksDB.

Características críticas:

- **Deduplicação por edge ID**: re-inserções (migration, WAL replay) não criam duplicados
- **Remoção bidirecional**: `remove_edge()` limpa ambas as direções atomicamente
- **Remoção de nó**: `remove_node()` limpa todas as arestas conectadas e os ponteiros reversos
- **Deduplicação em `neighbors_both()`**: usa `HashSet` para $O(1)$ dedup em nós hub com grau alto
- **Snapshot para CSR**: `snapshot_outgoing()` exporta a adjacência para construção de matrizes CSR no `nietzsche-cugraph`

O índice é reconstruído no startup por scan da column family de arestas — separado do `GraphStorage` (RocksDB). Esta separação permite que o índice in-memory opere com latência de nanosegundos enquanto a persistência opera com latência de microsegundos.

---

## 5.5 Os 11 Algoritmos de Grafo

### 5.5.1 PageRank (Power Iteration)

**Na Prática:** Num grafo de conhecimento com milhares de nós, nem todos os conceitos são igualmente importantes. O PageRank atribui a cada nó um score de "influência" baseado em quantos outros nós apontam para ele e quão influentes são esses nós. O NietzscheDB usa este score para priorizar resultados de busca, decidir que nós preservar durante a poda do Sleep Cycle, e identificar conceitos-chave no grafo.

O PageRank mede a influência relativa de cada nó no grafo de conhecimento. A implementação usa iteração de potência com damping factor configurável.

**Fórmula de convergência:**

$$PR(v) = \frac{1-d}{N} + d \sum_{u \in B_v} \frac{PR(u)}{L(u)}$$

onde:
- $d = 0.85$ (damping factor padrão)
- $N$ = número total de nós
- $B_v$ = conjunto de nós com arestas apontando para $v$
- $L(u)$ = grau de saída do nó $u$

**Convergência** é medida pela norma $L_1$ do vetor de deltas:

$$\|PR^{(t+1)} - PR^{(t)}\|_1 = \sum_{v=1}^{N} |PR^{(t+1)}(v) - PR^{(t)}(v)| < \epsilon$$

com $\epsilon = 10^{-7}$ por padrão e máximo de 20 iterações.

**Complexidade:** $O(I \cdot (V + E))$ onde $I$ é o número de iterações até convergência. Na prática, $I \leq 20$ para grafos de conhecimento típicos.

A implementação pré-computa o grau de saída de cada nó e inicializa todos os scores a $1/N$, garantindo que $\sum_v PR(v) = 1.0$ ao longo de toda a execução.

### 5.5.2 Detecção de Comunidades Louvain (desenvolvido na Université catholique de Louvain, Bélgica, por Vincent Blondel e colegas em 2008)

**Na Prática:** Um grafo de conhecimento organiza-se naturalmente em clusters temáticos — um grupo de nós sobre "física quântica", outro sobre "culinária italiana", etc. O algoritmo Louvain detecta automaticamente estas comunidades, permitindo ao NietzscheDB segmentar o conhecimento em domínios, otimizar buscas dentro de um tema, e identificar conceitos-ponte que conectam áreas distintas.

O algoritmo Louvain maximiza a modularidade $Q$ do grafo através de otimização gulosa iterativa.

**Função de modularidade:**

$$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

onde:
- $m$ = peso total das arestas
- $A_{ij}$ = peso da aresta entre $i$ e $j$
- $k_i$ = grau ponderado do nó $i$
- $c_i$ = comunidade do nó $i$
- $\delta(c_i, c_j)$ = 1 se $c_i = c_j$, 0 caso contrário

**Fase 1 (Otimização Local):** Cada nó é movido iterativamente para a comunidade vizinha que maximiza o ganho de modularidade $\Delta Q$. O ganho de mover o nó $i$ para a comunidade $C$ é:

$$\Delta Q = \left[ \frac{\Sigma_{in} + 2k_{i,in}}{2m} - \left(\frac{\Sigma_{tot} + k_i}{2m}\right)^2 \right] - \left[ \frac{\Sigma_{in}}{2m} - \left(\frac{\Sigma_{tot}}{2m}\right)^2 - \left(\frac{k_i}{2m}\right)^2 \right]$$

onde $\Sigma_{in}$ é a soma dos pesos internos da comunidade, $\Sigma_{tot}$ é a soma total dos graus dos nós na comunidade, e $k_{i,in}$ é a soma dos pesos das arestas de $i$ para nós em $C$.

A implementação suporta um parâmetro `resolution` $\gamma$ que controla a granularidade das comunidades — $\gamma > 1$ favorece comunidades menores, $\gamma < 1$ favorece comunidades maiores.

**Complexidade:** $O(V \cdot I \cdot \bar{k})$ onde $\bar{k}$ é o grau médio e $I$ é o número de iterações (tipicamente $\leq 10$).

### 5.5.3 Componentes Fracamente Conectados (WCC)

**Na Prática:** O WCC responde a uma pergunta de saúde do grafo: "existem ilhas de conhecimento desconectadas?". Se o grafo de conhecimento se fragmentar em múltiplos componentes isolados, conceitos de um componente tornam-se invisíveis a queries originadas em outro. O NietzscheDB usa WCC para diagnosticar fragmentação e, durante o Sleep Cycle, para criar arestas-ponte que reconectam componentes isolados.

Implementado via Union-Find com path compression e union by rank — o algoritmo textbook, mas com uma sutileza: trata o grafo como não-direcionado (arestas em ambas as direções).

**Complexidade:** $O((V + E) \cdot \alpha(V))$ onde $\alpha$ é a função inversa de Ackermann — efetivamente $O(V + E)$ na prática.

A estrutura Union-Find interna:

$$\text{find}(x) = \begin{cases} x & \text{se } parent[x] = x \\ \text{find}(parent[x]) & \text{com path compression} \end{cases}$$

$$\text{union}(x, y): \text{anexa a raiz de menor rank à raiz de maior rank}$$

O resultado inclui `component_count` e `largest_component_size`, métricas essenciais para diagnosticar fragmentação do grafo de conhecimento.

### 5.5.4 BFS (Breadth-First Search — busca em largura, algoritmo que explora o grafo nível por nível, como ondas concêntricas a partir de um ponto; útil para encontrar todos os vizinhos até uma profundidade específica)

A BFS do `nietzsche-graph` não é uma BFS genérica — é uma BFS com energy gate e pool de visited sets.

**Otimização crítica:** Cada chamada adquire um `HashSet<Uuid>` pré-alocado de um pool thread-local, eliminando ~1-3 µs de overhead de alocador por travessia. O pool é limitado a 8 sets por thread para evitar crescimento ilimitado.

**Energy gate:** Vizinhos com $E < E_{min}$ são ignorados — nem visitados nem expandidos. O filtro usa `get_node_meta()` (~108 bytes) em vez de `get_node()` (~12.4 KB), evitando deserialização desnecessária do embedding.

**Complexidade:** $O(V + E)$ com constante reduzida pelo pool de visited sets e pelo energy gate que poda ramos inteiros.

### 5.5.5 Dijkstra (Edsger Dijkstra, neerlandês, 1930–2002, Turing Award 1972, criador do algoritmo de caminho mínimo) com Distâncias Hiperbólicas

**Na Prática:** O Dijkstra encontra o caminho mais curto entre dois nós no grafo, usando a distância hiperbólica de Poincaré como custo de cada aresta. O NietzscheDB usa-o para responder a queries do tipo "qual é a cadeia de conceitos mais próxima entre A e B?", e como base para o cálculo de centralidade de intermediação (Betweenness).

A implementação de Dijkstra usa a distância de Poincaré como custo de aresta:

$$d_{\mathbb{H}}(u, v) = \text{acosh}\left(1 + \frac{2\|u - v\|^2}{(1 - \|u\|^2)(1 - \|v\|^2)}\right)$$

O min-heap usa `OrderedFloat<f64>` envolvido em `Reverse` para obter um min-heap a partir do max-heap padrão do Rust. Entradas stale (quando um caminho mais curto já foi settled) são descartadas por comparação com o mapa de distâncias.

**Otimização BUG A:** O energy gate usa `get_node_meta()` para decidir se um vizinho deve ser explorado. O embedding só é carregado via `get_embedding()` para vizinhos que passam o energy gate. Isto reduz I/O em 10-25x para grafos com muitos nós de baixa energia.

**Complexidade:** $O((V + E) \log V)$ — o custo padrão de Dijkstra com binary heap.

O `shortest_path()` estende Dijkstra com reconstrução de caminho via ponteiros de predecessor, terminando imediatamente quando o nó destino é settled.

### 5.5.6 Centralidade de Intermediação (Betweenness)

**Na Prática:** A centralidade de intermediação identifica nós que são "pontes" entre regiões do grafo de conhecimento — conceitos por onde passam muitos caminhos mais curtos. No NietzscheDB, um nó com betweenness alta é um conceito estruturalmente crítico: se for removido, muitos pares de conceitos ficam desconectados ou com caminhos muito mais longos. Esta métrica é usada para proteger nós-ponte da poda e para detectar gargalos no fluxo de conhecimento.

Implementada via algoritmo de Brandes (Ulrik Brandes, alemão, 1969–, criador do algoritmo eficiente de centralidade de intermediação), que calcula a centralidade de intermediação em tempo $O(VE)$ em vez do naive $O(V^3)$.

**Fórmula:**

$$g(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

onde $\sigma_{st}$ é o número de caminhos mais curtos entre $s$ e $t$, e $\sigma_{st}(v)$ é o número desses caminhos que passam por $v$.

**Algoritmo de Brandes:**
1. Para cada nó fonte $s$: BFS para computar $\sigma$ e predecessores
2. Back-propagation na ordem reversa do BFS:

$$\delta_s(v) = \sum_{w: v \in pred(w)} \frac{\sigma_s(v)}{\sigma_s(w)} \cdot (1 + \delta_s(w))$$

3. Acumular: $g(v) \mathrel{+}= \delta_s(v)$

**Amostragem:** Para grafos grandes, o parâmetro `sample_size` limita o número de fontes $s$ exploradas, dando uma aproximação $O(k \cdot E)$ em vez do exato $O(V \cdot E)$. As fontes são selecionadas aleatoriamente via `rand::seq::SliceRandom`.

### 5.5.7 Contagem de Triângulos

**Na Prática:** Um triângulo no grafo (A conhece B, B conhece C, C conhece A) indica que três conceitos estão fortemente interligados — formando um cluster denso. O NietzscheDB conta triângulos para calcular o coeficiente de clustering local de cada nó, que alimenta o cálculo da dimensão de Hausdorff local: clusters demasiado densos (muitos triângulos) sinalizam "tumores" de informação redundante que devem ser compactados durante o Sleep Cycle.

Triângulos no grafo de conhecimento indicam clusters densos e redundância semântica. A contagem é feita por interseção de vizinhanças:

$$\Delta = \frac{1}{3} \sum_{v} \sum_{\substack{(u, w) \in N(v) \times N(v) \\ u \neq w}} \mathbf{1}[u \in N(w)]$$

O fator $1/3$ corrige a tripla contagem (cada triângulo é contado uma vez por cada vértice). O coeficiente de clustering local de um nó é:

$$C(v) = \frac{2\Delta(v)}{k_v(k_v - 1)}$$

**Complexidade:** $O(V \cdot \bar{k}^2)$ no caso geral. Para grafos sparse ($\bar{k} \ll V$), isto é muito mais rápido que a abordagem por multiplicação de matrizes.

### 5.5.8 Centralidade de Grau

**Na Prática:** A centralidade de grau é a medida mais direta de quão "conectado" é um nó: quantas arestas entram, saem, ou ambas. No NietzscheDB, nós com grau alto são conceitos-hub que conectam muitos outros — e são candidatos naturais a receber energia extra para evitar poda. A consulta é instantânea porque opera apenas sobre o índice de adjacência em memória.

A centralidade mais simples e mais rápida — simplesmente o grau normalizado:

$$C_D(v) = \frac{k_v^{dir}}{N - 1}$$

onde $k_v^{dir}$ é o grau na direção escolhida (In, Out ou Both). A implementação suporta as três direções via o enum `Direction`.

**Complexidade:** $O(V)$ — linear no número de nós, consultando apenas o `AdjacencyIndex` in-memory.

### 5.5.9 Diffusion Walk (Passeio Aleatório com Bias Energético)

**Na Prática:** O diffusion walk simula a forma como a atenção humana "vagueia" por associações — partindo de um conceito e seguindo caminhos de alta energia e carga emocional. O NietzscheDB usa-o para descobrir conceitos associados que não seriam encontrados por busca KNN direta, especialmente memórias emocionalmente marcantes que atraem o passeio com força redobrada.

O diffusion walk é um passeio aleatório onde a probabilidade de transição é ponderada pela energia dos vizinhos e modulada pelo arousal emocional:

$$P(v \to u) \propto w_{vu} \cdot \exp\left(E(u) \cdot \beta_{eff}(u)\right)$$

onde o bias efetivo incorpora o arousal:

$$\beta_{eff}(u) = \beta \cdot (1 + \text{arousal}(u))$$

Isto significa que memórias emocionalmente carregadas (arousal alto) atraem o walk com força dobrada. Um nó com $\text{arousal} = 1.0$ duplica o gradiente de temperatura, fazendo o walk "gravitar" para vizinhos emocionais.

A amostragem usa `WeightedIndex` sobre os pesos computados, com RNG opcionalmente seeded para reprodutibilidade.

**Complexidade:** $O(S \cdot \bar{k})$ onde $S$ é o número de passos (padrão 50).

### 5.5.10 Greedy Routing Hiperbólico

**Na Prática:** O greedy routing é o algoritmo principal de navegação do NietzscheDB para encontrar caminhos entre conceitos. Em vez de explorar o grafo inteiro (como o Dijkstra), avança em cada passo para o vizinho geometricamente mais próximo do destino — uma estratégia que, graças à geometria hiperbólica, tipicamente chega ao alvo em $O(\log N)$ saltos. Quando fica preso num mínimo local, ativa o fallback A* com heurística hiperbólica.

O routing guloso explora a propriedade fundamental dos grafos hiperbólicos: em cada hop, mover-se para o vizinho que minimiza a distância de Poincaré ao alvo tipicamente encontra o caminho em $O(\log N)$ hops.

**Algoritmo:**
1. Em cada passo, para cada vizinho $u$ de $v$, computar $d_{\mathbb{H}}(u, target)$
2. Mover para o $u$ que minimiza esta distância
3. Se nenhum vizinho está mais perto que $v$ (mínimo local), ativar fallback A*

**Fallback A*:** Quando o routing guloso fica preso, o algoritmo muda para A* (algoritmo de busca de caminho que combina o custo real percorrido com uma estimativa heurística da distância restante — no NietzscheDB, a heurística usa a distância de Poincaré, garantindo que nunca superestima) com heurística $h(n) = d_{\mathbb{H}}(n, target)$, que é admissível (nunca sobrestima) em espaços hiperbólicos. O A* é limitado por `astar_max_nodes` (padrão 5000) para garantir terminação.

**Complexidade:**
- Fase gulosa: $O(\text{hops} \times \bar{k})$ — tipicamente $O(\log N \cdot \bar{k})$
- Fallback A*: $O(N \log N)$ worst case, bounded pelo parâmetro de configuração

### 5.5.11 Pregel (BSP para Computação Distribuída)

O modelo Pregel (Bulk Synchronous Parallel) está implementado no crate `nietzsche-cugraph` para aceleração GPU. Cada vértice executa uma função `compute()` em cada superstep, enviando mensagens para os vizinhos. A barreira de sincronização entre supersteps garante consistência.

O modelo é particularmente útil para PageRank e propagação de labels em grafos com milhões de nós, onde a GPU pode processar todos os vértices em paralelo.

---

## 5.6 Operações Multi-Manifold

O NietzscheDB opera em quatro variedades simultaneamente. O cálculo de distância muda conforme o contexto do manifold:

### Distância de Poincaré (variedade principal)

A distância é computada num único passo sobre os arrays de coordenadas, promovendo de `f32` para `f64` internamente para evitar cancelamento catastrófico perto da fronteira:

$$d_{\mathbb{H}}(u, v) = \text{acosh}\left(1 + \frac{2\|u - v\|^2}{(1 - \|u\|^2)(1 - \|v\|^2)}\right)$$

O kernel `poincare_sums()` computa $(\|u-v\|^2, \|u\|^2, \|v\|^2)$ numa única iteração sobre as coordenadas — sem passes adicionais. O corpo do loop não tem dependências entre iterações, permitindo ao compilador auto-vetorizar com SIMD (AVX2/SSE4.2) quando compilado com `-C target-cpu=native`. O compilador emite instruções `vmovss` (load f32) + `vcvtss2sd` (promover) + `vfmadd` (FMA f64).

### Projeção de Segurança

Para nós que derivam para fora da bola unitária (acumulação de ruído em treino longo), a projeção two-stage garante invariante:

$$\text{project}(x) = \begin{cases} x \cdot \frac{0.999}{\|x\| + 10^{-10}} & \text{se } \|x\| > 0.999 \\ x & \text{caso contrário} \end{cases}$$

O limiar 0.999 (e não 1.0) previne underflow catastrófico no denominador $(1 - \|x\|^2)$ durante sessões de treino longas.

### Distância Efetiva (Hidráulica)

Para operações de difusão e fluxo, a distância é modulada pela condutividade:

$$d_{eff}(u, v) = \frac{d_{\mathbb{H}}(u, v)}{\kappa(u, v)}$$

onde $\kappa \in [0.01, 10.0]$. Arestas com alta condutividade (caminhos "mielinizados" — por analogia com a mielina, a bainha lipídica que envolve axônios no cérebro e acelera dramaticamente a condução de impulsos nervosos) parecem mais curtas para o walk de difusão — o conhecimento flui mais rápido por associações frequentemente utilizadas.

### Intervalo de Minkowski (Causalidade)

Para travessias causais, o intervalo espaço-temporal classifica arestas:

$$ds^2 = -c^2 \Delta t^2 + \|\Delta x\|^2$$

Arestas timelike ($ds^2 < 0$) formam chains causais; arestas spacelike ($ds^2 > 0$) são filtradas em queries de causalidade.

---

## 5.7 Dimensões Emocionais: Valência e Arousal

A memória humana é inseparável da emoção. O NietzscheDB modela isto com duas dimensões no `NodeMeta`:

### Valência $\in [-1, 1]$: Eixo Prazer/Desprazer

- $v < 0$: memória punitiva, traumática
- $v = 0$: neutra
- $v > 0$: recompensadora, agradável

### Arousal $\in [0, 1]$: Intensidade Emocional

- $a = 0$: calmo, neutro
- $a = 1$: emocionalmente intenso

### Efeito no Diffusion Walk

O arousal amplifica o `energy_bias` na propagação de calor:

$$\beta_{eff} = \beta \cdot (1 + \text{arousal})$$

Um nó com arousal = 1.0 *duplica* o gradiente de temperatura. Memórias emocionalmente carregadas atraem a atenção computacional com o dobro da força.

### Efeito nos Pesos Laplacianos

A valência modula os pesos das arestas na difusão espectral:

$$\text{valence\_mod} = 1 + \frac{|v_u + v_v|}{2}$$

$$w(u, v) = \frac{\text{valence\_mod}}{1 + d_{\mathbb{H}}(u, v)}$$

**Clustering emocional:** Arestas entre nós da mesma polaridade emocional (ambos positivos ou ambos negativos) propagam calor mais rápido. Exemplos:

- Ambos positivos (+0.8, +0.6): $\text{mod} = 1 + |1.4|/2 = 1.7$ (boost forte)
- Ambos negativos (-0.5, -0.7): $\text{mod} = 1 + |-1.2|/2 = 1.6$ (boost forte)
- Polaridades opostas (+0.5, -0.5): $\text{mod} = 1 + |0|/2 = 1.0$ (sem boost)
- Ambos neutros (0, 0): $\text{mod} = 1.0$ (sem boost)

### Gravidade Emocional

A "gravidade" combinada de um nó é:

$$G_{emo}(v) = \text{arousal}(v) \cdot (1 + |\text{valence}(v)|)$$

Arousal alto + valência forte = alta gravidade emocional. Arousal baixo + valência neutra = gravidade zero (fato mundano).

### Decaimento e Reforço

As emoções não são estáticas. O arousal decai ao longo do tempo (emoções acalmam):

$$\text{arousal}^{(t+1)} = \text{arousal}^{(t)} \cdot (1 - r)$$

E o reforço emocional (após recuperação em contexto emocional) desloca a valência em direção ao alvo:

$$v^{(t+1)} = v^{(t)} + (v_{target} - v^{(t)}) \cdot s$$

onde $s \in [0, 1]$ é a força do reforço. Simultaneamente, o arousal recebe um boost de $s/2$.

---

## 5.8 O Motor Dialético Hegeliano

O motor dialético é uma das peças mais filosoficamente ambiciosas do NietzscheDB. Implementa o processo hegeliano de **Tese + Antítese $\to$ Síntese** como operação autônoma sobre o grafo de conhecimento.

### Algoritmo

**1. Scan:** Coletar nós semânticos com embeddings próximos (distância de Poincaré $< 0.8$).

**2. Detecção de Contradições:** Identificar pares onde o conteúdo indica oposição — negação, palavras-chave de contradição, ou campo `polarity` tagado pelo usuário. A diferença de polaridade deve exceder o limiar (padrão 1.2):

$$|\text{polarity}(thesis) - \text{polarity}(antithesis)| > \theta_{polarity}$$

**3. Criação de Tensão:** Inserir um `TensionNode` que liga tese e antítese. O nó de tensão carrega metadata de `certainty` (confiança epistêmica) e `truth_gradient` (direção de revisão de crença).

**4. Síntese via Média de Fréchet:** Durante o ciclo de sono, nós de tensão são resolvidos por síntese. O ponto de síntese é calculado pela média de Fréchet no disco de Poincaré:

$$\mu^* = \arg\min_{\mu \in \mathbb{D}^n} \sum_{i=1}^{k} w_i \cdot d_{\mathbb{H}}(\mu, x_i)^2$$

resolvida por gradiente Riemanniano iterativo:

$$\mu^{(t+1)} = \text{exp}_{\mu^{(t)}}\left(-\eta \sum_{i=1}^{k} w_i \cdot \text{log}_{\mu^{(t)}}(x_i)\right)$$

onde $\text{exp}$ e $\text{log}$ são os mapas exponencial e logarítmico do modelo de Poincaré.

A síntese produz um ponto *mais abstrato* (mais próximo do centro) que ambos os inputs — uma "subida" hierárquica que captura a reconciliação conceitual.

---

## 5.9 CRDTs Semânticos para Merge de Cluster

Quando nós de um cluster NietzscheDB evoluem os seus grafos de conhecimento independentemente, o merge tradicional (last-writer-wins) destrói a intenção estrutural. O crate `nietzsche-cluster` implementa CRDTs (Conflict-free Replicated Data Types — estruturas de dados que convergem automaticamente quando réplicas independentes são reconciliadas, sem necessidade de consenso centralizado ou resolução manual de conflitos) especializados para grafos de conhecimento hiperbólico.

### Regras de Merge

| Campo | Estratégia | Racional |
|-------|-----------|----------|
| `energy` | **max-wins** | O peer mais ativo ganha |
| `is_phantom` | **add-wins** (OR) | Poda é irreversível no merge |
| `embedding` | **energy-biased** | O embedding do peer com maior energia vence |
| `content` | **energy-biased** | Idem — topologia mais ativa é mais autoritativa |
| `edges` | **add-wins** | Arestas de qualquer peer sobrevivem |
| `timestamp` | **max** | Relógio Lamport (Leslie Lamport, americano, 1941–, Turing Award 2013, criador dos relógios lógicos distribuídos) |

### Propriedades CRDT

Todas as operações satisfazem as três propriedades fundamentais:

**Comutatividade:**
$$\text{merge}(A, B) = \text{merge}(B, A)$$

**Associatividade:**
$$\text{merge}(\text{merge}(A, B), C) = \text{merge}(A, \text{merge}(B, C))$$

**Idempotência:**
$$\text{merge}(A, A) = A$$

A escolha de **energy-biased** para embeddings (em vez de média vetorial) é deliberada: num espaço hiperbólico, o ponto médio euclidiano de dois pontos no disco de Poincaré permanece dentro da bola aberta (que é convexa em $\mathbb{R}^n$), mas é *geometricamente desprovido de significado* — não corresponde ao ponto médio geodésico no espaço hiperbólico. A média aritmética ignora a curvatura negativa do manifold, produzindo um ponto que distorce as relações de distância e hierarquia codificadas pela métrica de Poincaré. O embedding do peer mais energético é aceito integralmente, preservando a coerência geométrica.

A regra **add-wins para phantoms** ($a \lor b$) garante que operações destrutivas são irreversíveis no merge — se um peer decidiu que um nó deve ser phantomizado, essa decisão persiste. Isto previne "ressurreição" acidental de nós que foram deliberadamente podados.

---

## 5.10 Arestas de Schrödinger (Erwin Schrödinger, austríaco, 1887–1961, Nobel de Física, criador da equação de onda quântica): Colapso Probabilístico

O `schrodinger.rs` modela arestas como superposições quânticas que colapsam apenas no momento do MATCH. Uma associação entre "Maçã" e "Isaac Newton" não é fixa — tem uma probabilidade de existir que depende do contexto da query.

Cada `SchrodingerEdge` transporta:

- `probability` $\in [0, 1]$: probabilidade base de transição
- `decay_rate`: decaimento por tick (arestas não usadas desaparecem)
- `context_boost`: tag de contexto para boosting
- `boost_factor`: multiplicador quando o contexto corresponde (padrão 1.5)

**Colapso clássico:**

$$P(\text{existe}) = \min\left(1, \; p_{base} \cdot f_{boost}^{\mathbf{1}[\text{ctx match}]}\right)$$

**Colapso quântico:** Quando estados de Bloch (Felix Bloch, suíço-americano, 1905–1983, Nobel de Física, criador da esfera de Bloch) do contexto estão altamente entangled com o estado alvo ($F > \theta_{entanglement}$), a aresta é forçada a materializar-se — independente de $p_{base}$. Isto modela a observação de metade de um par entangled forçando o colapso da outra metade.

A fidelidade entre estados de Bloch é calculada como:

$$F(\psi, \phi) = \frac{1 + \cos\alpha}{2}$$

onde $\alpha$ é o ângulo entre os vetores de Bloch na esfera. O proxy de entanglement entre dois grupos é a fidelidade média:

$$E(A, B) = \frac{1}{|A| \cdot |B|} \sum_{a \in A} \sum_{b \in B} F(a, b)$$

---

## 5.11 Concept Path: Caminhos Semânticos Anotados

O módulo `concept_path` transforma rotas brutas do greedy router em caminhos semânticos anotados. Cada `PathHop` carrega:

- Tipo de nó, energia, profundidade radial
- Distância de Poincaré ao hop anterior e ao alvo
- Resumo textual extraído do payload JSON

Isto permite explicações legíveis:

```
[1] Matemática (Concept, r=0.21, E=0.85)
  --0.42-->
[2] Teoria da Informação (Semantic, r=0.48, E=0.72)
  --0.31-->
[3] Algoritmos (Semantic, r=0.63, E=0.67)
  --0.27-->
[4] Ciência da Computação (Concept, r=0.35, E=0.91)
```

A propriedade gulosa garante que `distance_to_target` decresce monotonicamente ao longo do caminho — cada hop aproxima o walker do destino no espaço hiperbólico.

---

## 5.12 Resumo das Complexidades

| Algoritmo | Complexidade | Notas |
|-----------|-------------|-------|
| PageRank | $O(I \cdot (V + E))$ | $I \leq 20$ tipicamente |
| Louvain | $O(V \cdot I \cdot \bar{k})$ | $I \leq 10$ |
| WCC (Union-Find) | $O((V+E) \cdot \alpha(V))$ | Efetivamente linear |
| BFS | $O(V + E)$ | Com pool de visited sets |
| Dijkstra | $O((V + E) \log V)$ | Min-heap com OrderedFloat |
| Betweenness (Brandes) | $O(V \cdot E)$ | Ou $O(k \cdot E)$ com amostragem |
| Contagem de Triângulos | $O(V \cdot \bar{k}^2)$ | Sparse: $\bar{k} \ll V$ |
| Centralidade de Grau | $O(V)$ | In-memory, AdjacencyIndex |
| Diffusion Walk | $O(S \cdot \bar{k})$ | $S$ = passos (padrão 50) |
| Greedy Routing | $O(\log N \cdot \bar{k})$ | $O(N \log N)$ com fallback A* |
| Pregel (GPU) | $O(S \cdot (V + E))$ | $S$ = supersteps, paralelo na GPU |

---

O `nietzsche-graph` não é um motor de grafos que suporta geometria hiperbólica como feature opcional. É um motor de grafos onde a geometria hiperbólica *é* a estrutura fundamental — onde a curvatura codifica hierarquia, a condutividade codifica experiência, a valência codifica emoção, e o colapso de Schrödinger codifica a natureza contextual de toda a associação. Cada campo, cada algoritmo, cada decisão de design reflete a mesma premissa: o conhecimento não vive num espaço plano.
