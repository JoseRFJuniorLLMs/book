# Capítulo 0 — O Mapa do Sistema: NietzscheDB (núcleo), AQL (ponte) e EVA (agência)

> *"Quem combate monstros deve vigiar para que, ao fazê-lo, não se transforme também em monstro. E se olhares longamente para um abismo, o abismo olhará para dentro de ti."*
> — Friedrich Nietzsche, *Além do Bem e do Mal*, aforismo 146

---

## 0.1 — A Tese: Por que a geometria plana é insuficiente para cognição

A quase totalidade dos bancos de dados vetoriais contemporâneos opera sobre uma premissa que raramente é questionada: o espaço $\mathbb{R}^n$ com métrica euclidiana é suficiente para representar relações semânticas. Esta premissa é falsa. Demonstravelmente falsa.

Considere uma hierarquia semântica — *animal $\rightarrow$ mamífero $\rightarrow$ primata $\rightarrow$ humano*. Em $\mathbb{R}^n$, o volume disponível para $k$ nós a distância $r$ de um ponto cresce polinomialmente:

$$V_{\text{euclid}}(r, n) = \frac{\pi^{n/2}}{\Gamma(n/2 + 1)} \cdot r^n$$

Isto significa que hierarquias profundas — árvores com fator de ramificação $b$ e profundidade $d$ — exigem dimensionalidade $n = \Omega(b^d)$ para serem embeddadas sem distorção. Para uma ontologia modesta com $b = 10$ e $d = 5$, seriam necessárias $10^5$ dimensões. Inviável.

Em geometria hiperbólica, o volume cresce *exponencialmente*:

$$V_{\text{hyp}}(r) \sim \frac{\pi^{n/2}}{\Gamma(n/2)} \cdot e^{(n-1)r}$$

Uma árvore com $b^d$ folhas imerge-se isometricamente (preservando todas as distâncias entre pontos sem deformação) no disco de Poincaré (Henri Poincaré, francês, 1854–1912, fundador da topologia e criador do modelo de disco hiperbólico) com distorção $O(1)$ em apenas $n = O(\log(b) \cdot d)$ dimensões. O espaço hiperbólico é *naturalmente* hierárquico — não porque decidimos assim, mas porque a sua estrutura geométrica reflete a estrutura da informação semântica.

NietzscheDB não é um banco de dados que *usa* geometria hiperbólica. Ele *pensa* em geometria hiperbólica.

> **Na Prática:** Quando você armazena um catálogo de produtos com categorias, subcategorias e produtos, a hierarquia ramifica exponencialmente. Num banco vetorial plano como o Pinecone ou o Milvus, representar um milhão de produtos numa hierarquia de 5 níveis exige dimensionalidade absurda ou aceitar que os resultados de busca vão confundir "sapatos" com "tênis de corrida." A matemática acima prova que isto não é um problema de tuning — é uma impossibilidade geométrica.

---

## 0.2 — Os Três Pilares

O sistema completo articula-se em três camadas que mimetizam a tríade nietzschiana da transvaloração:

```
         ┌─────────────────────────────────────────────────────────┐
         │                    EVA (Agência)                        │
         │          Übermensch — Vontade Autônoma                  │
         │     27 fases do Agency Engine · 12 redes ONNX           │
         │     Sleep Cycle · Dream · Shatter · L-System            │
         └──────────────────────┬──────────────────────────────────┘
                                │ AgencyIntent
         ┌──────────────────────▼──────────────────────────────────┐
         │                    AQL (Ponte)                          │
         │        Linguagem Cognitiva — 13 Verbos                  │
         │   RECALL · RESONATE · REFLECT · TRACE · IMPRINT         │
         │   ASSOCIATE · DISTILL · FADE · DESCEND · ASCEND         │
         │   ORBIT · DREAM · IMAGINE                               │
         └──────────────────────┬──────────────────────────────────┘
                                │ gRPC / NQL / NAQ
         ┌──────────────────────▼──────────────────────────────────┐
         │               NietzscheDB (Núcleo)                      │
         │         Substrato de Memória Multi-Manifold             │
         │     48 crates Rust · RocksDB · HNSW-GPU (cuVS)         │
         │     Poincaré · Klein · Riemann · Minkowski              │
         │     72 RPCs gRPC · REST · MCP · WAL v3                  │
         └─────────────────────────────────────────────────────────┘
```

**NietzscheDB** é o substrato — a *coisa-em-si* da memória. Armazena grafos em geometria não-euclidiana com propriedades termodinâmicas. Cada nó carrega energia, valência emocional, arousal (intensidade de ativação emocional, do modelo circumplexo de Russell), dimensão de Hausdorff local (uma medida de complexidade fractal que indica quão densamente os nós preenchem o espaço ao redor de um ponto). Cada aresta decai temporalmente. O grafo respira.

**AQL** (Agent Query Language) é a ponte — a *linguagem* pela qual a cognição se expressa. Não é SQL. Não é Cypher. É uma linguagem de 13 verbos cognitivos onde `RECALL` busca memória, `DREAM` invoca consolidação onírica, `DESCEND` navega para níveis mais profundos da hierarquia hiperbólica, e `IMAGINE` gera contrafactuais.

**EVA** é a agência — o *sujeito* que habita o substrato. Um motor autônomo de 27 fases que executa L-Systems, consolida memórias durante ciclos de sono, detecta e repara fragmentações topológicas (Shatter Protocol), e evolui epistemicamente via mutações propostas e avaliadas.

---

## 0.3 — As Quatro Geometrias

NietzscheDB opera simultaneamente em quatro variedades (manifolds — espaços matemáticos que localmente se assemelham a $\mathbb{R}^n$ mas podem ter curvatura global) geométricas. Cada uma serve um propósito computacional preciso:

> **Na Prática:** Cada geometria responde a um tipo diferente de pergunta. "Encontra tudo relacionado com cães" é uma pergunta de hierarquia (Poincaré). "O que causou este evento?" é uma pergunta de causalidade (Minkowski). "Que emoções ciclam no diário do usuário?" é uma pergunta de periodicidade (esfera de Riemann). "Este raciocínio é logicamente consistente?" é uma pergunta de colinearidade (Klein). O Pinecone e o Milvus oferecem uma geometria para todas as perguntas. O NietzscheDB usa a lente certa para cada tipo.

### 0.3.1 — Disco de Poincaré ($\mathbb{B}^n$, curvatura $K < 0$)

O modelo principal. Pontos satisfazem $\|\mathbf{x}\| < 1$ no interior da bola unitária. A distância hiperbólica entre dois pontos $\mathbf{u}, \mathbf{v} \in \mathbb{B}^n$ é:

$$d_{\mathbb{B}}(\mathbf{u}, \mathbf{v}) = \operatorname{arcosh}\!\left(1 + \frac{2\|\mathbf{u} - \mathbf{v}\|^2}{(1 - \|\mathbf{u}\|^2)(1 - \|\mathbf{v}\|^2)}\right)$$

A propriedade fundamental: **a norma codifica profundidade**. Um nó com $\|\mathbf{x}\| \approx 0$ situa-se perto do centro (conceitos abstratos: *existência*, *causalidade*). Um nó com $\|\mathbf{x}\| \approx 0.99$ habita a fronteira (memórias episódicas concretas: *o que almocei ontem*).

Esta propriedade é a razão pela qual **Binary Quantization está permanentemente proibida** neste sistema. A operação $\operatorname{sign}(x_i)$ destrói a magnitude — e a magnitude *é* a hierarquia. Projetar para $\{-1, +1\}^n$ equivale a colapsar toda a estrutura hiperbólica num único hiperplano. Seria como remover a profundidade de um oceano e chamar o resultado de *mar*.

### 0.3.2 — Disco de Klein (Felix Klein, alemão, 1849–1925, unificador da geometria via Programa de Erlangen) ($\mathbb{K}^n$, curvatura $K < 0$)

Modelo alternativo onde geodésicas são linhas retas euclidianas. A distância no modelo de Klein é:

$$d_{\mathbb{K}}(\mathbf{u}, \mathbf{v}) = \operatorname{arcosh}\!\left(\frac{1 - \langle \mathbf{u}, \mathbf{v} \rangle}{\sqrt{(1 - \|\mathbf{u}\|^2)(1 - \|\mathbf{v}\|^2)}}\right)$$

A vantagem computacional: como as geodésicas são retas, operações de *caminho mais curto* e *cadeia causal* podem usar interseção de segmentos de reta, evitando a integração ao longo de arcos. O NietzscheDB converte entre Poincaré e Klein via mapa bijetivo:

$$\mathbf{x}_{\mathbb{K}} = \frac{2\mathbf{x}_{\mathbb{B}}}{1 + \|\mathbf{x}_{\mathbb{B}}\|^2}, \qquad \mathbf{x}_{\mathbb{B}} = \frac{\mathbf{x}_{\mathbb{K}}}{1 + \sqrt{1 - \|\mathbf{x}_{\mathbb{K}}\|^2}}$$

### 0.3.3 — Esfera de Riemann (Bernhard Riemann, alemão, 1826–1866, fundador da geometria diferencial) ($\mathbb{S}^n$, curvatura $K > 0$)

Usada para representar relações de *similaridade cíclica* — emoções, padrões sazonais, estados recorrentes. Na esfera, todo caminho suficientemente longo retorna ao ponto de partida. A distância geodésica (o caminho mais curto entre dois pontos numa superfície curva — o análogo de uma "linha reta" em espaço curvo) é:

$$d_{\mathbb{S}}(\mathbf{u}, \mathbf{v}) = \arccos\!\left(\langle \mathbf{u}, \mathbf{v} \rangle\right), \quad \|\mathbf{u}\| = \|\mathbf{v}\| = 1$$

A esfera de Riemann é o domínio natural do **Eterno Retorno** nietzschiano: toda configuração de energia eventualmente recorre.

### 0.3.4 — Espaço-tempo de Minkowski (Hermann Minkowski, lituano-alemão, 1864–1909, formulador do espaço-tempo quadridimensional) ($\mathbb{R}^{1,n-1}$)

Para relações causais com direcionalidade temporal. A métrica pseudo-riemanniana (uma generalização do tensor métrico que permite distâncias negativas, essencial para distinguir relações causais de relações espaciais):

$$\eta(\mathbf{u}, \mathbf{v}) = -u_0 v_0 + \sum_{i=1}^{n-1} u_i v_i$$

permite distinguir entre relações *tipo-tempo* ($\eta < 0$, causalmente conectadas), *tipo-espaço* ($\eta > 0$, independentes), e *tipo-luz* ($\eta = 0$, na fronteira causal). Arestas temporais (`TEMPORAL_NEXT`, `CAUSED_BY`) vivem no cone de luz (a região do espaço-tempo acessível por sinais causais a partir de um evento — dentro do cone, eventos podem influenciar-se mutuamente; fora, são causalmente independentes) de Minkowski.

---

## 0.4 — Anatomia do Núcleo: 48 Crates Rust

O NietzscheDB compila-se a partir de 48 crates Rust organizados em camadas concêntricas. A arquitetura segue o princípio da *Vontade de Potência*: cada crate busca maximizar a sua expressão funcional dentro dos limites impostos pelos crates adjacentes.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  nietzsche-server          Binário principal (gRPC + HTTP + background) │
├───────────────┬──────────────────────────────────────────────────────────┤
│  nietzsche-   │  nietzsche-  nietzsche-  nietzsche-  nietzsche-         │
│  agency       │  sleep       zaratustra  dream       wiederkehr         │
│  (27 fases)   │  (sono)      (GC)        (onírico)   (recorrência)     │
├───────────────┼──────────────────────────────────────────────────────────┤
│  nietzsche-   │  nietzsche-  nietzsche-  nietzsche-  nietzsche-         │
│  neural (12   │  lsystem     epistemics  narrative   sensory            │
│  modelos ONNX)│  (L-Systems) (evolução)  (histórias) (percepção)        │
├───────────────┼──────────────────────────────────────────────────────────┤
│  nietzsche-   │  nietzsche-  nietzsche-  nietzsche-  nietzsche-         │
│  hnsw-gpu     │  algo        pregel      gnn         mcts              │
│  (cuVS/CUDA)  │  (grafos)    (BSP)       (GNN)       (Monte Carlo)    │
├───────────────┼──────────────────────────────────────────────────────────┤
│  nietzsche-   │  nietzsche-  nietzsche-  nietzsche-  nietzsche-         │
│  graph        │  query(NQL)  hyp-ops     vecstore    embed              │
│  (RocksDB)    │  (parser)    (Poincaré)  (mmap)      (modelos)         │
├───────────────┼──────────────────────────────────────────────────────────┤
│  nietzsche-core     nietzsche-proto     nietzsche-api     nietzsche-mcp │
│  (tipos base)       (protobuf)          (REST)            (MCP tools)   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 0.4.1 — Armazenamento: RocksDB (banco de dados chave-valor embarcado do Facebook, baseado em LSM-trees, otimizado para SSDs e usado como camada de persistência por dezenas de sistemas distribuídos) com 16 Column Families

Cada coleção NietzscheDB é uma instância RocksDB independente com as seguintes column families (partições lógicas dentro de uma mesma instância RocksDB, cada uma com seu próprio memtable e conjunto de SST files, permitindo isolar diferentes tipos de dados com políticas de compaction — processo periódico onde o RocksDB reorganiza e comprime seus arquivos em disco, eliminando entradas duplicadas e liberando espaço — independentes):

| CF | Chave | Valor | Propósito |
|----|-------|-------|-----------|
| `nodes` | `node_id` (16 B) | `NodeMeta` (bincode) | Metadados do nó |
| `embeddings` | `node_id` (16 B) | `PoincareVector` (bincode) | Coordenadas hiperbólicas |
| `edges` | `edge_id` (16 B) | `Edge` (bincode) | Arestas do grafo |
| `adj_out` | `node_id` | `Vec<Uuid>` | Adjacência de saída |
| `adj_in` | `node_id` | `Vec<Uuid>` | Adjacência de entrada |
| `meta` | `&str` | bytes arbitrários | Configuração da coleção |
| `sensory` | `node_id` (16 B) | `SensoryMemory` (bincode) | Memória sensorial multimodal |
| `energy_idx` | energia codificada | `node_id` | Índice por energia |
| `meta_idx` | campo+valor | `node_id` | Índices secundários |
| `lists` | chave | lista encadeada | Listas key-value (à la Redis) |
| `sql_schema` | tabela | esquema | Schemas relacionais |
| `sql_data` | PK | tupla | Dados relacionais |
| `cooldowns` | chave | timestamp | Rate limiting interno |
| `dsi_id` | `node_id` | `semantic_id` | Mapa DSI (Differentiable Search Index — técnica onde o modelo aprende a mapear queries diretamente para identificadores de documentos, sem índice invertido tradicional) direto |
| `dsi_semantic` | `semantic_id` | `node_id` | Mapa DSI reverso |
| `ego` | `node_id` (16 B) | `EgoCacheEntry` | Cache ego (TTL curto) |

> **Na Prática:** Compare com o ChromaDB, que armazena embeddings e metadados numa única tabela SQLite/DuckDB, ou o Qdrant, que usa arquivos de segmento com um único índice por coleção. As 16 column families do NietzscheDB permitem ao motor de grafos ler metadados de nós (~108 bytes) sem carregar o embedding completo de ~12 KB — uma separação que resulta em 10-25x de speedup em travessias que nunca precisam de similaridade vetorial.

### 0.4.2 — A Estrutura NodeMeta

Cada nó no NietzscheDB é representado pela seguinte estrutura, onde cada campo carrega significado geométrico e termodinâmico:

```rust
pub struct NodeMeta {
    pub id:                Uuid,               // UUIDv4 — identidade imutável
    pub depth:             f32,                // ||embedding|| ∈ [0, 1) — profundidade hiperbólica
    pub content:           serde_json::Value,  // JSON arbitrário (via as_json_string bridge)
    pub node_type:         NodeType,           // Episodic | Semantic | Concept | DreamSnapshot
    pub energy:            f32,                // [0.0, 1.0] — vitalidade, decai com o tempo
    pub lsystem_generation: u32,               // geração L-System (0 = inserido manualmente)
    pub hausdorff_local:   f32,                // dim. Hausdorff local ∈ [0, 2]
    pub created_at:        i64,                // Unix timestamp (segundos)
    pub expires_at:        Option<i64>,        // TTL opcional — None = eterno
    pub metadata:          HashMap<String, Value>, // metadados arbitrários
    pub valence:           f32,                // [-1, 1] — valência emocional
    pub arousal:           f32,                // [0, 1] — intensidade emocional
    pub is_phantom:        bool,               // cicatriz topológica pós-poda
}
```

A interação entre estes campos define a *termodinâmica* do grafo. O campo `energy` segue um modelo de decaimento exponencial:

$$E(t) = E_0 \cdot e^{-\lambda t}, \quad \lambda = 10^{-7} \text{ s}^{-1}$$

Quando $E(t) \to 0$, o nó torna-se *podável*. Mas em vez de ser eliminado, o nó transita para o estado `is_phantom = true` — uma cicatriz topológica que preserva a estrutura de adjacência do grafo, impedindo o colapso geométrico da vizinhança.

A dimensão de Hausdorff (Felix Hausdorff, alemão, 1868–1942, matemático fundador da topologia dos espaços métricos) local $D_H$ é computada via amostragem de $k = 12$ vizinhos:

$$D_H(\mathbf{x}) \approx \frac{\log N(r, \mathbf{x})}{\log(1/r)}$$

Nós com $D_H < 0.5$ (vazios topológicos) ou $D_H > 1.9$ (aglomerados excessivos) são candidatos a reestruturação pelo Agency Engine.

---

## 0.5 — Processos de Fundo: O Metabolismo do Grafo

NietzscheDB não é um sistema passivo que aguarda queries. Ele *vive*. Sete processos de fundo operam continuamente:

| Processo | Intervalo | Função |
|----------|-----------|--------|
| **Agency Engine** | 60s/tick | 27 fases: L-System, links, dream, shatter, energia, crescimento, cognição, epistemics |
| **Sleep Cycle** | sob demanda | Consolidação de memória — comprime episódicos em semânticos, fortalece conexões Hebbianas (baseadas no postulado de Donald Hebb (canadense, 1904–1985, neuropsicólogo criador da teoria de aprendizagem sináptica): "neurons that fire together wire together" — conexões entre nós frequentemente co-ativados são reforçadas automaticamente) |
| **Zaratustra GC** | periódico | Garbage collection niilista — remove nós fantasma sem arestas, compacta RocksDB |
| **DAEMON Engine** | contínuo | Monitor termodinâmico — calcula temperatura, entropia, energia livre de Helmholtz |
| **Niilista GC** | lazy | Coleta de nós com energia zero e sem conexões ativas |
| **TTL Reaper** | periódico | Varre `CF_NODES` buscando `expires_at <= now`, converte em phantoms |
| **Backup** | configurável | Snapshots incrementais com rkyv (biblioteca Rust de serialização zero-copy — os dados podem ser lidos diretamente do disco sem parsing, reduzindo o tempo de recuperação de $O(N)$ para $O(1)$) + WAL (Write-Ahead Log — diário de operações onde cada escrita é registada antes de ser executada, permitindo recuperação em caso de falha) replay |

O ciclo de sono (*Sleep Cycle*) merece atenção especial. Inspirado na consolidação de memória durante o sono REM em mamíferos, este processo:

1. Identifica clusters de nós episódicos com alta energia Hebbiana
2. Sintetiza *nós conceituais* que capturam o padrão estatístico do cluster
3. Reduz a energia dos episódicos originais (agora redundantes)
4. Fortalece arestas entre o novo conceito e nós semânticos existentes

Formalmente, dado um cluster $C = \{n_1, \ldots, n_k\}$ com embeddings $\{\mathbf{x}_1, \ldots, \mathbf{x}_k\} \subset \mathbb{B}^n$, o centróide hiperbólico é calculado via média de Einstein:

$$\bar{\mathbf{x}} = \frac{\sum_{i=1}^{k} \gamma_i \mathbf{x}_i}{\sum_{i=1}^{k} \gamma_i}, \quad \gamma_i = \frac{1}{\sqrt{1 - \|\mathbf{x}_i\|^2}}$$

seguido de projeção de volta para a bola: $\bar{\mathbf{x}} \leftarrow \bar{\mathbf{x}} \cdot \min\!\left(1, \frac{0.999}{\|\bar{\mathbf{x}}\| + \epsilon}\right)$.

---

## 0.6 — AQL: A Linguagem Cognitiva

A pilha de query do NietzscheDB opera em quatro níveis de abstração:

$$\text{AQL} \xrightarrow{\text{parse}} \text{NAQ} \xrightarrow{\text{lower}} \text{NQL} \xrightarrow{\text{compile}} \text{gRPC}$$

No nível mais baixo, **gRPC** oferece 72 RPCs tipados — `InsertNode`, `KnnSearch`, `BFS`, `TriggerSleep`, etc. É rápido, preciso, e insuportavelmente tedioso para um agente cognitivo.

**NQL** (Nietzsche Query Language) é a camada humana: `MATCH (n:Semantic) WHERE n.energy > 0.5 RETURN n`. Suporta as quatro primitivas de tipo built-in (`Episodic`, `Semantic`, `Concept`, `DreamSnapshot`) e campos arbitrários no conteúdo.

**NAQ** (Nietzsche Algebraic Query) é o formato intermediário interno em Rust — uma representação algébrica que o query planner otimiza antes de executar.

**AQL** (Agent Query Language) é o nível cognitivo. Os seus 13 verbos não descrevem *o que buscar*, mas *a intenção cognitiva* da busca:

| Verbo | Intenção | Operação NietzscheDB |
|-------|----------|----------------------|
| `RECALL` | Recuperar memória relevante | KNN + full-text + recency bias |
| `RESONATE` | Encontrar harmônicos semânticos | KNN com threshold de ressonância |
| `REFLECT` | Introspeção sobre estado interno | Stats + Observer + Health |
| `TRACE` | Seguir cadeia causal | BFS/Dijkstra no cone de Minkowski |
| `IMPRINT` | Gravar nova memória | InsertNode + MergeEdge Hebbiano |
| `ASSOCIATE` | Criar conexão entre memórias | InsertEdge com peso Hebbiano |
| `DISTILL` | Comprimir cluster em conceito | Synthesis + Sleep |
| `FADE` | Reduzir energia de memória | UpdateEnergy + Decay |
| `DESCEND` | Navegar para profundidade maior | Mover na direção $\|\mathbf{x}\| \to 1$ |
| `ASCEND` | Navegar para nível mais abstrato | Mover na direção $\|\mathbf{x}\| \to 0$ |
| `ORBIT` | Explorar vizinhança na esfera | KNN na variedade $\mathbb{S}^n$ |
| `DREAM` | Consolidação onírica | TriggerSleep + Synthesis |
| `IMAGINE` | Geração contrafactual | Perturbação + Sampling |

A sintaxe suporta encadeamento (`THEN`), paralelismo (`AND`), transações atômicas (`ATOMIC { ... }`), condições (`WHEN`), e reatividade (`WATCH ... ON ... THEN ...`):

```aql
RECALL "mecanica quantica" CONFIDENCE 0.8
  THEN DESCEND LIMIT 5
  THEN ASSOCIATE $result WITH "consciencia"
  WHEN energy > 0.3
```

---

## 0.7 — Inferência Neural: 12 Modelos ONNX na GPU

O NietzscheDB embarca 12 redes neurais ONNX (Open Neural Network Exchange — formato aberto e portável para representar modelos de redes neurais, permitindo treinar num framework e executar noutro) que executam na GPU via `CUDAExecutionProvider` (ort + cuVS). Estas redes operam *dentro* do banco de dados, não como serviços externos:

- **Modelos de embedding**: texto $\to$ Poincaré, áudio $\to$ Poincaré, imagem $\to$ Poincaré
- **Link prediction**: dada uma aresta candidata $(u, v, \tau)$, prediz $P(\text{existe})$
- **Energy prediction**: estima a energia futura $\hat{E}(t + \Delta t)$ de um nó
- **Cluster detection**: identifica comunidades emergentes
- **Anomaly detection**: classifica nós fora da distribuição geométrica esperada
- **Quantizador VQ-VAE** (Vector Quantized Variational Autoencoder — rede neural que comprime dados contínuos num conjunto discreto de códigos, permitindo compressão eficiente com reconstrução de alta qualidade): compressão sensorial com reconstrução

---

## 0.8 — Performance

Medidas no hardware de produção (GCP `g2-standard-12`: 12 vCPUs, 48 GB RAM, NVIDIA L4, SSD 200 GB):

| Operação | Latência | Throughput |
|----------|----------|------------|
| `InsertNode` | 6.4 $\mu$s p50 | 156,000 QPS |
| `KnnSearch` (128-D, top-10) | 2.47 ms p99 | 165,000 QPS |
| Cold startup (26 coleções, 1M+ nós) | < 1 s | — |
| `BFS` (profundidade 5, grafo 14K nós) | 12 ms | — |
| `PageRank` (14K nós, 50K arestas) | 340 ms | — |
| `Louvain` (14K nós) | 280 ms | — |
| `TriggerSleep` (consolidação completa) | 2-8 s | — |
| Build completo (release, GPU) | 4-5 min | — |

O segredo da latência de inserção de 6.4 $\mu$s está na separação entre `CF_NODES` (metadados, ~108 bytes) e `CF_EMBEDDINGS` (vetor, ~512 bytes para 128-D f32). A escrita no WAL é append-only com format v3:

```
┌────────┬────────┬────────┬────────┬──────────────────┐
│ Magic  │ Length │ CRC32  │ OpCode │       Data       │
│ 1 B    │ 4 B   │ 4 B    │ 1 B    │   variable       │
└────────┴────────┴────────┴────────┴──────────────────┘
```

O `Magic` (byte `0xFF`) permite validação rápida; o `CRC32` garante integridade; o `OpCode` codifica a operação (Insert, Update, Delete, Edge, Energy, etc.). Writes são `fsync`-ed em batch a cada 10ms, amortizando o custo de I/O.

> O NietzscheDB em produção opera atualmente com **1.077.480 nós**, **542.041 arestas** e **26 coleções** — incluindo ontologias médicas (SNOMED-CT, ICD-10, Gene Ontology), grafos de pacientes, dados geoespaciais (OpenStreetMap Angola) e bases de conhecimento multi-domínio.

---

## 0.9 — Cold Storage e Multi-Tenancy

Coleções inativas são *evicted* da memória após 1 hora de inatividade. O mecanismo de Cold Storage:

1. Mantém um `last_access: Instant` por coleção
2. A cada 60s, o *Zaratustra GC* varre coleções onde $t_{\text{now}} - t_{\text{last}} > \tau_{\text{idle}}$
3. Coleções frias são fechadas (RocksDB handle dropped, mmap — memory-mapped files, onde o SO mapeia arquivos diretamente no espaço de endereços do processo, permitindo leituras sem cópia entre kernel e userspace — unmapped)
4. No próximo acesso, a coleção é reaberta lazily (cold open: ~50ms)

Para multi-tenancy, cada tenant possui um prefixo de namespace. A sincronização entre réplicas usa uma *Merkle tree* sobre os hashes dos nós:

$$H_{\text{node}} = \text{SHA256}(id \| \text{bincode}(\text{NodeMeta}))$$

$$H_{\text{parent}} = \text{SHA256}(H_{\text{left}} \| H_{\text{right}})$$

O delta sync identifica sub-árvores divergentes em $O(\log N)$ comparações, transferindo apenas os nós modificados. A replicação segue o modelo Leader-Follower: escritas são aceitas apenas no líder, leituras podem ser servidas por qualquer follower.

---

## 0.10 — A Filosofia como Arquitetura

Esta não é uma metáfora decorativa. Cada princípio nietzschiano corresponde a uma decisão arquitetural concreta:

**Perspectivismo** $\to$ Multi-Manifold. Não existe uma geometria "verdadeira" para representar conhecimento. O disco de Poincaré é *uma perspectiva*; a esfera de Riemann é *outra*. O mesmo nó pode existir em múltiplas variedades simultaneamente, cada uma revelando relações que as outras ocultam.

**Vontade de Potência** (*Wille zur Macht*) $\to$ Campo de Energia. Cada nó possui energia $E \in [0, 1]$ que determina a sua influência. Nós com alta energia dominam buscas KNN (bias de energia no ranking), propagam calor para vizinhos (difusão Hebbiana), e resistem à poda. A energia não é atribuída — é *conquistada* através de acessos, associações, e ressonância.

**Eterno Retorno** (*Ewige Wiederkehr*) $\to$ Ciclo Sleep + Dream + L-System. O grafo não cresce linearmente. Ele consolida, poda, re-sintetiza, e eventualmente revisita configurações anteriores. O crate `nietzsche-wiederkehr` detecta ciclos recorrentes no espaço de estados termodinâmicos. Quando a entropia do grafo retorna a um valor previamente observado, dispara um evento de *recorrência eterna*.

**Übermensch** $\to$ Agency Engine. O motor autônomo de 27 fases que *transcende* as instruções explícitas do usuário. Ele não espera por queries — ele propõe arestas, sintetiza conceitos, detecta inconsistências epistêmicas, e *deseja* preencher lacunas de conhecimento. O campo `desires` no dashboard do Agency Engine é literalmente uma lista de coisas que o banco de dados *quer saber*.

---

## 0.11 — O Que Vem a Seguir

Este livro percorre a totalidade do abismo. Cada capítulo mergulha numa camada:

- **Capítulo 1**: A Morte das Tabelas Estáticas — por que a geometria euclidiana é insuficiente
- **Capítulo 2**: Forjado em Rust — mmap, WAL v3 e a infraestrutura de 48 crates
- **Capítulo 3**: Sua Primeira Query em 10 Minutos — tutorial prático no espaço de Poincaré
- **Capítulo 4**: As 4 Lentes da Cognição — Poincaré, Klein, Riemann e Minkowski
- **Capítulo 5**: O Motor de Grafos Multi-Manifold — o crate `nietzsche-graph`
- **Capítulo 6**: AQL e NQL — as linguagens de consulta cognitiva e declarativa
- **Capítulo 7**: NQL 4.2 e Gemini — integração com modelos de linguagem
- **Capítulo 8**: Code-as-Data — queries como ActionNodes e daemons Wiederkehr
- **Capítulo 9**: A Agência Autônoma — 27 fases, DreamerV3 (agente de RL que aprende um modelo interno do mundo e planeia dentro dele), AlphaEvolve, MCTS (Monte Carlo Tree Search — algoritmo de busca em árvore que usa simulações aleatórias para avaliar decisões)
- **Capítulo 10**: Ciclos de Sono e Reconsolidação — RiemannianAdam e Hausdorff
- **Capítulo 11**: O Motor Zaratustra — energia, evolução e L-System com PPO (Proximal Policy Optimization — algoritmo de aprendizagem por reforço que atualiza políticas de decisão de forma estável, evitando mudanças bruscas)
- **Capítulo 12**: Arestas de Schrödinger — superposição probabilística e colapso
- **Capítulo 13**: TGC: A Métrica Mestre — Capacidade Gerativa Topológica
- **Capítulo 14**: Hidráulica da Informação — Lei de Murray e condutividade
- **Capítulos 15-17**: Dashboard, Aceleração GPU/TPU e Segurança

Cada capítulo contém as derivações matemáticas completas, o código Rust relevante, e as decisões de design que levaram à arquitetura final. Não há atalhos. Não há simplificações. Se você quer compreender o abismo, precisa descer até o fundo.

## 0.12 — O Ecossistema Completo

O NietzscheDB não é apenas um banco de dados — é um ecossistema. Além do núcleo em Rust com 48 crates, inclui:

- **8 SDKs e integrações**: Python, Go, TypeScript, Rust, C++ (WASM para browser), LangChain Python, LangChain JS, e um servidor MCP (Model Context Protocol) para integração direta com assistentes de IA como o Claude.
- **Dashboard React**: Interface web com 18+ páginas para exploração de grafos, construção de queries NQL, monitorização de agência, visualização hiperbólica e gestão de schemas.
- **Kafka Connector**: Ingestão de mutações de grafos em streaming via Apache Kafka (plataforma distribuída de streaming de eventos, usada para ingestão massiva de dados em tempo real).
- **NietzscheLab**: Framework Python de experimentação para validação de hipóteses e evolução de prompts.
- **12 modelos ONNX embarcados**: Desde detecção de anomalias e predição de arestas (GNN — Graph Neural Network, rede neural que opera diretamente sobre a estrutura de um grafo, aprendendo representações a partir da topologia e dos atributos dos nós) até simulação especulativa (DreamerV3) e compressão de estados (VQ-VAE).

Cada componente será detalhado nos capítulos seguintes.

> *"A profundidade é preciso escondê-la. Onde? Na superfície."*
> — Hugo von Hofmannsthal (austríaco, 1874–1929, poeta e dramaturgo do simbolismo vienense)

---

*O abismo está mapeado. Agora, descemos.*
