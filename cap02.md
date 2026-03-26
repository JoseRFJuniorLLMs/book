# Capítulo 2 — Forjado em Rust: mmap, WAL v3 e a Infraestrutura de 48 Crates

> *"O que não me mata, fortalece-me."*
> — Friedrich Nietzsche, *Crepúsculo dos Ídolos*

---

## 2.1 Por Que Rust para um Banco Cognitivo

A escolha de Rust como linguagem fundamental do NietzscheDB não foi estética — foi uma exigência matemática. Um banco de dados que opera no disco de Poincaré requer garantias que nenhum garbage collector pode oferecer: latência determinística na ordem de microsegundos, acesso zero-copy a vetores mapeados em memória e a certeza formal de que nenhuma thread corrompe o estado hiperbólico de outra.

### 2.1.1 Ownership como Invariante Topológico

O sistema de ownership de Rust impõe uma restrição que espelha a topologia do espaço hiperbólico: cada recurso tem exatamente um dono em cada instante. Quando um vetor $\mathbf{x} \in \mathbb{B}^n$ (o Poincaré ball aberto) é inserido no índice HNSW, o ownership transfere-se da thread de ingestão para o `VectorStore`. Não há cópia, não há compartilhamento implícito — há uma única transferência de posse, verificada em tempo de compilação.

Considere a operação fundamental de inserção:

```rust
pub fn append(&self, vector_bytes: &[u8]) -> Result<u32, String> {
    if vector_bytes.len() != self.element_size {
        return Err(format!(
            "Vector size mismatch: {} vs {}",
            vector_bytes.len(), self.element_size
        ));
    }
    let id = self.count.fetch_add(1, Ordering::SeqCst);
    let segment_idx = id >> CHUNK_SHIFT;
    let local_idx = id & CHUNK_MASK;
    // ...
}
```

A chamada `fetch_add` com `Ordering::SeqCst` garante sequencialidade total — cada vetor recebe um ID monotonicamente crescente. O custo desta garantia é medido pela barreira de memória:

$$T_{\text{insert}} = T_{\text{mmap\_write}} + T_{\text{fence}} \approx 200\text{ns} + 50\text{ns} = 250\text{ns}$$

Em Java ou Go, o equivalente exigiria uma alocação no heap ($\sim 1\mu s$), sincronização via mutex ($\sim 500\text{ns}$) e eventual pausa de GC ($\sim 10\text{ms}$ nos piores casos). A diferença acumula: para $10^6$ inserções consecutivas, Rust completa em $\sim 250\text{ms}$ onde Java gastaria $\sim 1.5\text{s}$ sem contar pausas do GC.

### 2.1.2 Abstrações de Custo Zero

O trait `Metric<N>` exemplifica as abstrações de custo zero (*zero-cost abstractions*) que permitem ao NietzscheDB suportar múltiplas geometrias sem overhead de runtime:

```rust
pub trait Metric<const N: usize>: Send + Sync + 'static {
    fn name() -> &'static str;
    fn distance(a: &[f64; N], b: &[f64; N]) -> f64;
    fn validate(vector: &[f64; N]) -> Result<(), String> {
        let _ = vector;
        Ok(())
    }
}
```

O parâmetro `const N: usize` é resolvido em tempo de compilação — o compilador gera uma instância monomorphizada para cada dimensionalidade. Para uma coleção de 128 dimensões com métrica de Poincaré, o código resultante é idêntico a uma implementação manual com arrays `[f64; 128]`. O compilador elimina a camada de abstração, produzindo SIMD vetorizado:

$$d_{\mathbb{B}}(\mathbf{x}, \mathbf{y}) = \operatorname{arcosh}\!\left(1 + 2\,\frac{\|\mathbf{x} - \mathbf{y}\|^2}{(1 - \|\mathbf{x}\|^2)(1 - \|\mathbf{y}\|^2)}\right)$$

O `Metric` trait também abrange a geometria lorentziana, usada internamente pelo motor causal:

$$d_{\mathbb{H}}(\mathbf{x}, \mathbf{y}) = \operatorname{arcosh}\!\bigl(-\langle \mathbf{x}, \mathbf{y} \rangle_L\bigr)$$

onde $\langle \mathbf{x}, \mathbf{y} \rangle_L = -x_0 y_0 + \sum_{i=1}^{n-1} x_i y_i$ é o produto interno de Minkowski.

### 2.1.3 Concorrência Sem Medo

O NietzscheDB opera com dezenas de threads simultâneas: o Agency Engine executa o L-System, o motor de sonhos processa consolidação, o Pregel computa PageRank, e queries KNN chegam via gRPC. A "fearless concurrency" de Rust garante, em tempo de compilação, que nenhuma destas threads produz data races.

As primitivas são escolhidas cirurgicamente:

| Primitiva | Crate | Uso no NietzscheDB |
|-----------|-------|--------------------|
| `DashMap` (tabela hash concorrente para Rust, equivalente a um ConcurrentHashMap do Java — permite leituras e escritas simultâneas sem lock global) | dashmap 5.5 | Metadata index (inverted + numeric) |
| `RwLock` (parking_lot) | parking_lot 0.12 | Topologia HNSW, bitmap de deletados |
| `ArcSwap` (primitiva atômica para trocar ponteiros compartilhados sem lock — permite atualizar estruturas de dados em tempo constante enquanto leitores continuam acessando a versão anterior) | arc-swap | Segmentos mmap (hot-swap sem lock) |
| `AtomicU32` | std | Entry point e max_layer do HNSW |
| `AtomicUsize` | std | Contador de vetores no VectorStore |

A combinação de `ArcSwap` para os segmentos mmap com `Mutex` apenas para escrita significa que leituras — a operação dominante numa busca KNN — são *completamente lock-free*:

$$\text{Throughput}_{\text{read}} = \frac{N_{\text{cores}} \cdot f_{\text{read}}}{T_{\text{atomic\_load}}} \approx \frac{12 \times 0.95}{5\text{ns}} = 2.28 \times 10^9 \text{ ops/s}$$

---

## 2.2 Arquitetura de 48 Crates

O workspace do NietzscheDB contém 48 crates organizados em dez camadas funcionais. Cada crate compila independentemente, com fronteiras de dependência definidas por `Cargo.toml`. A arquitetura segue o princípio de *acyclic dependencies* — o grafo de dependências é um DAG, e a compilação paralela explora maximamente o paralelismo de 12 vCPUs da VM.

### 2.2.1 Mapa Completo

```
NietzscheDB Workspace (48 crates)
=================================

FOUNDATION (9)          ENGINE (6)           AGI (3)
  core                    graph                agi (14.7K LOC)
  hnsw                    query                agency (20.9K LOC)
  vecstore                lsystem              dream
  baseserver              pregel
  proto                   sleep             EVOLUTION (1)
  cli                     api                  zaratustra
  embed
  wasm                  ANALYTICS (2)        VISIONARY (2)
  rsdk                    algo                 narrative
                          sensory              wiederkehr

ACCELERATION (3)        SEARCH (3)           NEURAL (6)
  hnsw-gpu (cuVS)        filtered-knn         neural
  tpu (PJRT)             named-vectors        gnn
  cugraph                 pq                   mcts
                                               rl
INFRASTRUCTURE (11)                            vqvae
  server     kafka        mcp                  dsi
  cluster    metrics      secondary-idx
  media      swartz       sdk
  hyp-ops    naq
```

A profundidade máxima do DAG de dependências é 5:

$$\text{proto} \to \text{core} \to \text{hnsw} \to \text{graph} \to \text{agency} \to \text{server}$$

O tempo de compilação incremental, após modificar um único crate de folha como `nietzsche-algo`, é:

$$T_{\text{incremental}} \approx T_{\text{parse}} + T_{\text{codegen}}(1) + T_{\text{link}} \approx 2\text{s} + 8\text{s} + 5\text{s} = 15\text{s}$$

O build completo em modo release, com LTO (*Link-Time Optimization*) e `codegen-units = 1`:

$$T_{\text{release}} \approx 4\text{--}5 \text{ min}$$

### 2.2.2 Foundation: Os 9 Pilares

O crate `nietzsche-core` define os tipos fundamentais — `HyperVector`, `QuantizationMode`, `FilterExpr`, `Durability`, e o trait `Collection` que todo backend de armazenamento deve implementar. O `Metric` trait vive aqui, com três implementações concretas: `PoincareMetric`, `EuclideanMetric` e `LorentzMetric`.

O `nietzsche-vecstore` oferece duas implementações de `VectorStore` selecionadas por feature flag: `mmap_impl` (produção, memmap2) e `ram_impl` (testes, Vec em heap). O `nietzsche-hnsw` constrói o índice multi-camada sobre o `VectorStore`, usando `rkyv` para snapshots zero-copy. O `nietzsche-proto` gera os stubs gRPC via `prost` + `tonic`.

### 2.2.3 AGI: O Cérebro do Banco

O crate `nietzsche-agi` (14.711 linhas em 23 módulos) implementa seis camadas de raciocínio:

| Camada | Módulos | Função |
|--------|---------|--------|
| 1. Perception | `representation`, `inference_engine` | Codificação sensorial |
| 2. Metabolism | `metabolism`, `homeostasis` | Regulação energética |
| 3. Reasoning | `reasoning`, `dialectic`, `synthesis` | Inferência formal |
| 4. Evolution | `evolution`, `genome`, `innovation` | Adaptação genética |
| 5. Identity | `identity`, `certification`, `trajectory` | Auto-modelo |
| 6. Meta | `spectral`, `criticality`, `sandbox` | Auto-reflexão |

O `nietzsche-agency` (20.907 linhas) é o motor executivo que orquestra o L-System, o temporal decay, o crescimento de grafo, as camadas cognitivas e a evolução epistêmica. Cada tick produz `AgencyIntent` — objetos imutáveis de leitura que o server handler converte em mutações sob write lock, garantindo linearizabilidade.

---

## 2.3 WAL v3: O Diário da Persistência

> **Na Prática:** Um WAL (Write-Ahead Log) é um "diário" onde o banco de dados anota cada operação *antes* de executá-la. Se o sistema falhar (queda de energia, crash), basta reler o diário para reconstruir o estado. É o mesmo princípio de um diário contábil: primeiro registra, depois executa. O NietzscheDB usa WAL v3 com checksums CRC32 para garantir que nenhuma inserção de nó ou aresta se perde, mesmo em falhas catastróficas.

O Write-Ahead Log (WAL) do NietzscheDB garante que nenhuma operação confirmada se perde, mesmo durante falhas de energia. O formato V3 introduz checksums CRC32 e um cabeçalho estruturado que permite recuperação parcial.

### 2.3.1 Formato Binário

Cada entrada no WAL v3 segue o layout:

```
+--------+----------+----------+--------+---------+
| Magic  | Length   | CRC32    | OpCode | Data... |
| 1 byte | 4 bytes  | 4 bytes  | 1 byte | N bytes |
| 0xFF   | LE u32   | LE u32   |  0x03  | payload |
+--------+----------+----------+--------+---------+
         |<-------- header -------->|<--- payload -->|
```

O byte mágico `0xFF` distingue entradas V3 das entradas legadas V1/V2 (cujos opcodes são `0x01` e `0x02`). O CRC32 é calculado sobre o payload completo (OpCode + Data) usando o algoritmo CRC32 via `crc32fast`:

$$\text{CRC32}(P) = \bigoplus_{i=0}^{|P|-1} \text{poly\_mod}(P[i] \cdot x^{8(|P|-1-i)})$$

onde $\text{poly\_mod}$ opera sobre o polinômio gerador $G(x) = x^{32} + x^{26} + x^{23} + x^{22} + x^{16} + x^{12} + x^{11} + x^{10} + x^8 + x^7 + x^5 + x^4 + x^2 + x + 1$.

O payload de uma inserção V3 (OpCode 3) tem a estrutura:

```
OpCode(u8=3) | ID(u32) | Clock(u64) | VecLen(u32) | Vec[f64 x VecLen]
             | MetaLen(u32) | [KeyLen(u32) Key(bytes) ValLen(u32) Val(bytes)] x MetaLen
```

O tamanho total de uma entrada para um vetor de dimensão $d$ com $m$ pares de metadados é:

$$S_{\text{entry}} = \underbrace{9}_{\text{header}} + \underbrace{1 + 4 + 8}_{\text{op+id+clock}} + \underbrace{4 + 8d}_{\text{vetor}} + \underbrace{4 + \sum_{i=1}^{m}(8 + |k_i| + |v_i|)}_{\text{metadados}}$$

Para $d = 128$ e $m = 3$ pares de metadados típicos ($\sim 40$ bytes cada):

$$S_{\text{entry}} \approx 9 + 13 + 1028 + 124 = 1174 \text{ bytes}$$

### 2.3.2 Três Modos de Durabilidade

```rust
pub enum WalSyncMode {
    Strict, // fsync a cada escrita — D_max, V_min
    Batch,  // sync_data periodico — D_alta, V_alta
    Async,  // flush ao OS cache — D_media, V_max
}
```

A relação entre durabilidade $D$ e velocidade $V$ segue um trade-off clássico:

| Modo | Operação | Durabilidade | Latência por escrita |
|------|----------|-------------|---------------------|
| **Strict** | `sync_all()` (dados + metadados FS) | $D = 1.0$ | $\sim 2\text{ms}$ |
| **Batch** | `sync_data()` (apenas dados) | $D \approx 0.99$ | $\sim 200\mu\text{s}$ |
| **Async** | `flush()` (buffer userspace → OS cache) | $D \approx 0.95$ | $\sim 5\mu\text{s}$ |

A probabilidade de perda de dados no modo Async, dado um MTBF (*Mean Time Between Failures*) de $F$ horas e uma janela de flush do OS de $\Delta t$ segundos:

$$P_{\text{loss}} = \frac{\Delta t}{F \times 3600} \approx \frac{30}{8760 \times 3600} \approx 9.5 \times 10^{-7}$$

No modo Batch, a janela reduz-se ao intervalo de `sync_data`:

$$P_{\text{loss}}^{\text{batch}} = \frac{t_{\text{sync}}}{F \times 3600} \approx \frac{0.1}{8760 \times 3600} \approx 3.2 \times 10^{-9}$$

### 2.3.3 Recovery: Replay e Truncamento

A função `replay()` percorre o arquivo WAL sequencialmente. Para cada entrada:

1. Lê o byte mágico. Se `0xFF` → V3; senão → legado (V1/V2).
2. Para V3: lê `Length` e `CRC32` do cabeçalho, lê `Length` bytes de payload.
3. Recalcula o CRC32 do payload e compara com o armazenado.
4. Se CRC diverge: **trunca** o WAL na última posição válida.

```rust
if hasher.finalize() != stored_crc {
    eprintln!("WAL Corruption detected at offset {valid_pos}. Truncating.");
    break;
}
```

Após o replay, se a posição válida `valid_pos` for menor que o tamanho do arquivo, o WAL é truncado:

$$\text{WAL}_{\text{healed}} = \text{WAL}[0..\text{valid\_pos}]$$

Este mecanismo garante que entradas parcialmente escritas (e.g., crash durante `write_all`) são automaticamente descartadas. A integridade do prefixo válido é garantida pela propriedade do CRC32: a probabilidade de uma corrupção não detectada é $2^{-32} \approx 2.3 \times 10^{-10}$.

---

## 2.4 Vetores Mapeados em Memória

> **Na Prática:** Memory-mapped files (mmap) permitem ao sistema operacional tratar arquivos em disco como se fossem memória RAM. Em vez de copiar dados do disco para a memória do programa, o SO "mapeia" o arquivo diretamente no espaço de endereços — o programa lê e escreve nele como se fosse um array em memória, e o kernel trata da paginação transparentemente. O NietzscheDB usa mmap para acessar os vetores hiperbólicos sem cópias intermediárias, atingindo latências de ~200ns por leitura.

O `VectorStore` usa `memmap2` para mapear arquivos diretamente no espaço de endereçamento virtual, eliminando cópias entre kernel e userspace.

### 2.4.1 Arquitetura Segmentada

Os vetores são armazenados em segmentos de tamanho fixo chamados `chunk_N.hyp`. Cada segmento contém exatamente $2^{16} = 65536$ vetores:

```rust
const CHUNK_SIZE: usize = 65536;  // 2^16 vetores por segmento
const CHUNK_SHIFT: usize = 16;     // bits para indice do segmento
const CHUNK_MASK: usize = 0xFFFF;  // mascara para offset local
```

A conversão de ID global para coordenadas (segmento, offset) usa aritmética de bits:

$$\text{segment} = \text{id} \gg 16, \quad \text{offset} = \text{id} \mathbin{\&} \texttt{0xFFFF}$$

Para um vetor de dimensão $d$ em `f64` (8 bytes), cada segmento ocupa:

$$S_{\text{chunk}} = 65536 \times 8d = 65536 \times 8 \times 128 = 64 \text{ MiB (para } d=128\text{)}$$

O endereço físico de um vetor é calculado em $O(1)$:

$$\text{addr}(\text{id}) = \text{base}[\text{id} \gg 16] + (\text{id} \mathbin{\&} \texttt{0xFFFF}) \times \text{element\_size}$$

### 2.4.2 Dualidade Read/Write

Cada segmento mantém dois mapeamentos simultâneos do mesmo arquivo:

```rust
struct Segment {
    read_mmap: Mmap,           // leitura lock-free (imutavel)
    write_mmap: Mutex<MmapMut>, // escrita serializada
    file: File,
}
```

A `read_mmap` (imutável) permite que múltiplas threads de busca KNN leiam vetores simultaneamente sem qualquer sincronização — o kernel do OS garante coerência via page cache. A `write_mmap` (mutável) é protegida por `Mutex`, mas como escritas são tipicamente batched, a contenção é mínima.

O hot-swap de segmentos é feito via `ArcSwap`:

```rust
segments: ArcSwap<Vec<Arc<Segment>>>,
```

Quando um novo segmento é necessário (o segmento atual está cheio), a thread de crescimento cria o arquivo, mapeia-o, e substitui o vetor de segmentos atomicamente. Leituras em progresso continuam com a referência antiga (via `Arc`); novas leituras veem o segmento adicionado. Não há pausa, não há lock global.

### 2.4.3 Layout no Disco

A estrutura de diretório de uma coleção com $N$ vetores:

```
/var/lib/nietzsche/collections/<nome>/
  vectors/
    chunk_0.hyp    # vetores 0..65535
    chunk_1.hyp    # vetores 65536..131071
    ...
    chunk_k.hyp    # k = ceil(N / 65536) - 1
  index.snapshot   # HNSW serializado via rkyv
  wal.bin          # Write-Ahead Log (V3)
  rocksdb/         # RocksDB para grafos
    MANIFEST-*
    *.sst
    *.log
```

O número de segmentos para uma coleção de $N$ vetores:

$$k = \left\lceil \frac{N}{65536} \right\rceil$$

Para a coleção `science_galaxies` com 721 nós: $k = 1$ segmento, 64 MiB no disco. Para uma coleção hipotética de $10^6$ nós: $k = 16$ segmentos, 1 GiB.

---

## 2.5 Serialização: bincode, rkyv e o Problema do V0

> **Na Prática:** Serialização é o processo de converter estruturas de dados em memória (structs, objetos) numa sequência de bytes que pode ser gravada em disco ou enviada pela rede. O `rkyv` é especialmente importante porque oferece deserialização "zero-copy" — em vez de parsear bytes e construir novos objetos em memória, ele acessa diretamente os bytes no arquivo mmap como se já fossem a struct final. No NietzscheDB, isto permite recuperar snapshots HNSW com centenas de milhares de nós em ~1ms, versus ~500ms com métodos convencionais.

O NietzscheDB usa três formatos de serialização, cada um otimizado para um caso de uso distinto.

### 2.5.1 bincode 1.3.3 para RocksDB

O `bincode` serializa structs Rust em formato binário compacto e posicional. Para o `NodeMeta`:

```rust
struct NodeMeta {
    id: Uuid,                          // 16 bytes
    depth: f32,                        //  4 bytes
    content: serde_json::Value,        // variavel (via as_json_string)
    node_type: NodeType,               //  4 bytes (u32 enum tag)
    energy: f32,                       //  4 bytes
    lsystem_generation: u32,           //  4 bytes
    hausdorff_local: f32,              //  4 bytes
    created_at: i64,                   //  8 bytes
    expires_at: Option<i64>,           //  1+8 bytes (tag + valor)
    metadata: HashMap<String, Value>,  // variavel (via as_json_string)
    valence: f32,                      //  4 bytes
    arousal: f32,                      //  4 bytes
    is_phantom: bool,                  //  1 byte
}
```

**Limitação crítica**: o bincode 1.3.3 usa formato posicional. O atributo `#[serde(default)]` **não tem efeito** — se um campo é adicionado ao final da struct, dados antigos falham na desserialização porque o bincode espera exatamente $n$ bytes na posição correta. Esta limitação forçou a criação de structs legadas explícitas (`NodeMetaV1`, `NodeMetaV15`).

A segunda limitação é mais sutil: o bincode **não consegue desserializar `serde_json::Value`** porque o `Deserialize` impl do `Value` chama `deserialize_any()`, que o bincode rejeita com `DeserializeAnyNotSupported`. A serialização funciona (o `Serialize` do `Value` chama métodos concretos como `serialize_map`), mas a ida-e-volta está quebrada. A solução é o wrapper `as_json_string` que serializa o `Value` como string JSON primeiro, e depois serializa a string via bincode.

### 2.5.2 As Quatro Versões de Storage

A migração transparente entre formatos é feita por `deserialize_node_meta_compat()`:

$$\text{V2} \xrightarrow{\text{falha}} \text{V1.5} \xrightarrow{\text{falha}} \text{V1} \xrightarrow{\text{falha}} \text{V0 (parser manual)}$$

| Versão | Campos | content/metadata | Período |
|--------|--------|-----------------|---------|
| **V0** | Node completo (com embedding) | bincode raw `Value` | Pré-570a6ba |
| **V1** | NodeMeta (sem embedding) | `as_json_string` | 570a6ba -- 755036f |
| **V1.5** | V1 + `expires_at` | `as_json_string` | 755036f -- b8c5e11 |
| **V2** | V1.5 + `valence`, `arousal`, `is_phantom` | `as_json_string` | Atual |

O parser V0 é um analisador byte-a-byte que reconstrói o `NodeMeta` a partir do layout binário conhecido:

```
UUID(u64_len=16 + 16B) | Embedding(u64_len + coords*f64 + u64_dim)
| depth(f32) | content(bincode Value) | node_type(u32) | energy(f32)
| lsystem_gen(u32) | hausdorff(f32) | created_at(i64) | metadata(...)
```

O parser varre o sufixo fixo (24 bytes: `node_type` + `energy` + `lsystem_gen` + `hausdorff` + `created_at`) validando intervalos físicos: $\text{energy} \in [0, 2]$, $\text{hausdorff} \in [0, 5]$, $\text{created\_at} \in [1.7\times10^9, 2.0\times10^9]$. Esta heurística baseada em restrições físicas do domínio funciona porque valores fora desses intervalos são estruturalmente impossíveis no NietzscheDB.

### 2.5.3 rkyv para Snapshots HNSW

O `rkyv` (crate versão 0.7) oferece desserialização zero-copy: o snapshot é mapeado em memória e acessado diretamente, sem parsing. O custo de "desserialização" é $O(1)$ — uma simples verificação de alinhamento:

```rust
#[derive(Archive, Deserialize, Serialize)]
#[archive(check_bytes)]
pub struct SnapshotData {
    pub max_layer: u32,
    pub entry_point: u32,
    pub nodes: Vec<SnapshotNode>,
    pub metadata: SnapshotMetadata,
}
```

O tempo de recuperação de um snapshot com $N$ nós:

$$T_{\text{rkyv}} = T_{\text{mmap}} + T_{\text{validate}} \approx O(1) + O(N) \cdot \epsilon$$

onde $\epsilon$ é o custo de `check_bytes` por nó ($\sim 10\text{ns}$). Para $N = 100\text{K}$: $T_{\text{rkyv}} \approx 1\text{ms}$, versus $\sim 500\text{ms}$ para desserialização convencional via bincode.

---

## 2.6 RocksDB: 16 Column Families

O NietzscheDB usa RocksDB como motor de armazenamento para dados estruturados (nós, arestas, adjacências, metadados). Os dados são particionados em 16 column families, cada uma com configuração de compressão e cache otimizada:

| CF | Chave | Valor | Propósito |
|----|-------|-------|-----------|
| `nodes` | `node_id` (16B UUID) | `NodeMeta` (bincode, ~100B) | Metadados dos nós |
| `embeddings` | `node_id` (16B) | `PoincareVector` (bincode, ~$8d$B) | Vetores hiperbólicos |
| `edges` | `edge_id` (16B) | `Edge` (bincode) | Arestas com peso e causalidade |
| `adj_out` | `node_id` (16B) | `Vec<Uuid>` (arestas saindo) | Índice de adjacência (saída) |
| `adj_in` | `node_id` (16B) | `Vec<Uuid>` (arestas entrando) | Índice de adjacência (entrada) |
| `meta` | `&str` (nome) | bytes arbitrários | Contadores, configuração |
| `sensory` | `node_id` (16B) | `SensoryMemory` (bincode) | Memória sensorial |
| `energy_idx` | `[energy_be(4B) \| node_id(16B)]` | vazio | Índice secundário de energia |
| `meta_idx` | `[hash(8B) \| val(8B) \| node_id(16B)]` | vazio | Índice secundário de metadados |
| `lists` | `[node_id(16B) \| hash(8B) \| seq(8B)]` | value bytes | Listas ordenadas por nó |
| `sql_schema` | `table_name` (UTF-8) | Schema serializado | Camada SQL (Swartz) |
| `sql_data` | `row_key` | Row data | Dados tabulares SQL |
| `cooldowns` | `node_id` (16B) | vazio | Registro de cooldowns ativos |
| `dsi_id` | `node_id` (16B) | `semantic_id` (bincode) | DSI: nó → ID semântico |
| `dsi_semantic` | `semantic_id` | `node_id` | DSI: ID semântico → nó |
| `ego` | `node_id` (16B) | `EgoCacheEntry` (bincode) | Cache ego-cêntrico |

A separação entre `nodes` (~100 bytes por entrada) e `embeddings` (~$8d$ bytes) é uma otimização crítica. Operações que precisam apenas de metadados — BFS com gate de energia, `update_energy()`, filtros NQL — leem apenas da CF `nodes`, economizando $\sim 24$ KiB por acesso (para $d = 3072$):

$$\text{Speedup} = \frac{S_{\text{node+embedding}}}{S_{\text{node}}} = \frac{24\,576 + 100}{100} \approx 246\times$$

O índice de energia (`energy_idx`) usa chaves compostas com o valor de energia em big-endian (para preservar a ordem lexicográfica do RocksDB), permitindo range scans em $O(\log N + k)$:

$$\text{SCAN} : \text{energy} \in [e_{\min}, e_{\max}] \Rightarrow \text{Seek}([e_{\min}^{\text{BE}}]) \to \text{Next}^k$$

---

## 2.7 Índice HNSW: Grafo de Proximidade Multi-Camada

> **Na Prática:** O HNSW (Hierarchical Navigable Small World) é uma estrutura de índice para busca aproximada de vizinhos mais próximos. Imagine um mapa com vários níveis de zoom: no nível mais alto (poucas cidades), você localiza a região geral; em níveis mais baixos (mais detalhe), refina a busca até encontrar o ponto exato. O HNSW faz o mesmo com vetores — camadas superiores com poucos nós servem de "atalho" para navegar rapidamente, e a camada 0 contém todos os nós para refinar o resultado. No NietzscheDB, o HNSW é adaptado para usar a distância de Poincaré em vez da euclidiana, permitindo buscas $O(\log n)$ no espaço hiperbólico.

O HNSW (*Hierarchical Navigable Small World*) é o índice vetorial principal do NietzscheDB. A estrutura consiste em múltiplas camadas de grafos de vizinhança, onde cada camada superior contém um subconjunto exponencialmente menor de nós.

### 2.7.1 Distribuição de Camadas

A camada de cada nó é sorteada geometricamente:

$$\ell = \left\lfloor -\ln(\text{uniform}(0,1)) \cdot m_L \right\rfloor$$

onde $m_L = \frac{1}{\ln(M)}$ e $M$ é o grau máximo por camada. O número esperado de nós na camada $\ell$:

$$\mathbb{E}[N_\ell] = N \cdot \left(\frac{1}{M}\right)^\ell$$

A complexidade de busca é:

$$O\!\left(\log N \cdot M \cdot \log\frac{1}{\epsilon}\right)$$

onde $\epsilon$ é a precisão desejada do recall.

### 2.7.2 Busca em Duas Fases

A inserção segue o algoritmo HNSW original com adaptações para o espaço de Poincaré:

**Fase 1 — Greedy Descent** (camadas superiores): Da camada máxima até à camada do novo nó, faz busca gulosa mantendo um único candidato:

$$q_{\ell+1} = \arg\min_{v \in \mathcal{N}_\ell(q_\ell)} d_{\mathbb{B}}(v, \mathbf{x}_{\text{new}})$$

**Fase 2 — Expansão** (camada 0 até à camada do nó): Busca com `ef_construction` candidatos, seleção de vizinhos com heurística, com $M_{\max}$ diferenciado:

$$M_{\max}(\ell) = \begin{cases} 2M & \text{se } \ell = 0 \\ M & \text{se } \ell > 0 \end{cases}$$

A camada 0 é duplamente densa para maximizar o recall. Os parâmetros `entry_point` e `max_layer` são armazenados em `AtomicU32` separados — uma simplificação que aceita uma rara condição de corrida (comentada no código como TODO) em troca de performance:

```rust
// Update entry_point FIRST so that any reader seeing
// the new max_layer will also see the new entry_point.
if (new_level as u32) > max_layer {
    self.entry_point.store(id, Ordering::SeqCst);
    self.max_layer.store(new_level as u32, Ordering::SeqCst);
}
```

A solução ideal seria combinar ambos num único `AtomicU64`:

$$\text{packed} = (\text{max\_layer} \mathbin{\text{<<}} 32) \,|\, \text{entry\_point}$$

---

## 2.8 Árvore de Merkle para Replicação Delta

> **Na Prática:** Uma árvore de Merkle é uma estrutura onde cada "balde" de dados tem um hash (resumo criptográfico). Comparando apenas os hashes entre duas réplicas, o sistema identifica rapidamente *quais* baldes divergem, sem precisar comparar todos os dados. O NietzscheDB usa isto para sincronizar réplicas de forma eficiente — em vez de transferir todos os vetores (~1 GiB), transfere apenas os baldes que mudaram (~11 MiB para modificações típicas).

O NietzscheDB usa uma árvore de Merkle com 256 buckets para sincronização anti-entropia entre réplicas. Cada vetor é atribuído a um bucket determinístico:

$$\text{bucket}(\text{id}) = \text{id} \bmod 256$$

O digest de cada bucket agrega os hashes dos vetores nele contidos:

$$h_b = \bigoplus_{i \,:\, \text{bucket}(i) = b} \text{hash}(\mathbf{x}_i)$$

O hash raiz da coleção é a agregação dos 256 buckets:

$$h_{\text{root}} = H(h_0 \| h_1 \| \cdots \| h_{255})$$

A sincronização delta entre duas réplicas $A$ e $B$ requer apenas a comparação dos 256 hashes de bucket. Se $k$ buckets divergem, o custo de sincronização é:

$$C_{\text{sync}} = O(256) + O\!\left(k \cdot \frac{N}{256}\right)$$

Para $N = 10^6$ e $k = 3$ buckets modificados:

$$C_{\text{sync}} \approx 256 \times 8 + 3 \times 3906 \times S_{\text{vec}} \approx 2\text{ KiB} + 3 \times 3906 \times 1\text{ KiB} \approx 11.4 \text{ MiB}$$

Versus uma sincronização total que transferiria $\sim 1$ GiB.

---

## 2.9 O Sistema de Build

O build do NietzscheDB é um processo que combina o ecossistema Rust nightly com CUDA 12.x e a biblioteca cuVS da NVIDIA para aceleração GPU.

### 2.9.1 Cadeia de Compilação

```
Rust nightly 1.96.0
  + CUDA 12.x toolkit
  + cuVS 24.6 (via conda, miniforge3/envs/cuvs/)
  + libclang (para bindgen FFI)
  → cargo build --release -p nietzsche-server
  → ~45 MiB binary em /usr/local/bin/nietzsche-server
```

O perfil de release é agressivamente otimizado:

```toml
[profile.release]
lto = true          # Link-Time Optimization (monolitica)
codegen-units = 1   # maximo de otimizacao intra-crate
strip = true        # remove simbolos de debug
panic = "abort"     # sem stack unwinding
opt-level = 3       # otimizacao maxima (-O3)
```

O LTO monolítico (`lto = true`) com `codegen-units = 1` permite ao LLVM otimizar *através das fronteiras de crate*: uma chamada de `nietzsche-core::PoincareMetric::distance()` a partir de `nietzsche-hnsw` é inlined diretamente no loop de busca, eliminando o overhead de chamada de função. O custo é o tempo de compilação — ~4-5 minutos em release versus ~90 segundos sem LTO.

### 2.9.2 Variáveis de Ambiente Críticas

A compilação com GPU exige que o linker encontre as bibliotecas cuVS:

```bash
export CUVS_ROOT=/home/web2a/miniforge3/envs/cuvs
export LIBRARY_PATH=$CUVS_ROOT/lib       # compilacao
export LD_LIBRARY_PATH=$CUVS_ROOT/lib    # runtime
export CPATH=$CUVS_ROOT/include          # headers C/C++
```

Sem estas variáveis, o `build.rs` do `cuvs-sys` falha com `cuvs/core/c_api.h not found`. A feature `gpu` (habilitada por default no `Cargo.toml` do server) ativa o crate `nietzsche-hnsw-gpu` que implementa o índice CAGRA (*Cuda Approximate Graph-based Nearest-neighbor search*) via cuVS, e `nietzsche-neural/cuda` que habilita `ort/cuda` para os 12 modelos ONNX com `CUDAExecutionProvider`.

### 2.9.3 Perfis Adicionais

```toml
[profile.bench-fast]
inherits = "release"
lto = "thin"         # LTO parcial (mais rapido)
codegen-units = 4    # paralelismo de codegen

[profile.perf]
inherits = "release"
lto = "fat"          # LTO maxima
codegen-units = 1
opt-level = 3
# Usar com: RUSTFLAGS="-C target-cpu=native"
```

O perfil `perf` com `target-cpu=native` habilita instruções AVX-512 (quando disponíveis) para o cálculo de distâncias:

$$d(\mathbf{x}, \mathbf{y}) = \sum_{i=0}^{d/8} \text{vfmadd231pd}(\Delta_i, \Delta_i, \text{acc}_i)$$

processando 8 `f64` por ciclo de clock, um speedup de $\sim 4\times$ sobre o fallback escalar.

---

## 2.10 Síntese Arquitetural

A infraestrutura do NietzscheDB pode ser resumida numa equação de performance composta:

$$\text{Latência}_{\text{query}} = \underbrace{T_{\text{mmap\_access}}}_{\sim 200\text{ns}} + \underbrace{T_{\text{HNSW\_per\_layer}} \cdot \log N}_{\sim 50\mu\text{s} \times 17} + \underbrace{T_{\text{Poincaré\_dist}} \cdot k \cdot \text{ef}}_{\sim 100\mu\text{s}} + \underbrace{T_{\text{RocksDB\_join}}}_{\sim 20\mu\text{s}}$$

Para uma coleção de $N = 100\text{K}$ vetores com $\text{ef} = 128$ e $k = 10$, onde $50\mu\text{s}$ é o custo por camada e $\log N \approx 17$ é o número de camadas atravessadas:

$$\text{Latência}_{\text{query}} \approx 0.2 + 50 \cdot 17 + 100 + 20 \approx 970 \,\mu\text{s} \approx 1\text{ms}$$

A arquitetura de 48 crates não é um acidente de crescimento orgânico — é uma decisão de engenharia que explora o modelo de compilação de Rust. Cada crate é uma unidade de compilação independente, com cache incremental. Uma modificação no `nietzsche-narrative` não recompila o `nietzsche-hnsw`. A granularidade fina permite que o CI valide crates individuais (`cargo check -p nietzsche-agency`) em segundos, enquanto o build completo é reservado para deploy.

O binário final de ~45 MiB contém: o motor de grafo hiperbólico, o índice HNSW com aceleração GPU, o Agency Engine com L-System e sonhos, a camada gRPC com 72 RPCs, o dashboard HTTP, o motor SQL (Swartz), a camada de replicação com Merkle tree, e seis camadas de raciocínio AGI. Tudo compilado num único executável, sem dependências de runtime além da libc e das bibliotecas CUDA.

A tabela seguinte resume a responsabilidade de cada camada no pipeline de uma query KNN típica:

| Camada | Crate(s) | Operação | Complexidade |
|--------|----------|----------|-------------|
| Rede | server, proto | Deserializar gRPC request | $O(d)$ |
| Índice | hnsw (ou hnsw-gpu) | Travessia multi-camada | $O(\log N \cdot M)$ |
| Vetores | vecstore (mmap) | Leitura zero-copy | $O(1)$ por vetor |
| Distância | core (Metric trait) | Poincaré ou Lorentz | $O(d)$ por par |
| Metadados | graph (RocksDB) | Join CF_NODES + filtros | $O(k \cdot \log N)$ |
| Filtros | filtered-knn, query | Pré/pós-filtragem NQL | $O(k \cdot |F|)$ |
| Resposta | server, proto | Serializar gRPC response | $O(k \cdot d)$ |

O throughput agregado do sistema, considerando $C$ cores dedicados a queries e uma taxa de cache hit do page cache de $\alpha$:

$$Q_{\text{max}} = \frac{C \cdot \alpha}{T_{\text{query}}} + \frac{C \cdot (1-\alpha)}{T_{\text{query}} + T_{\text{page\_fault}}}$$

Para $C = 10$ (dos 12 vCPUs, 2 reservados ao Agency), $\alpha = 0.98$ (working set cabe em RAM), $T_{\text{query}} = 1\text{ms}$ e $T_{\text{page\_fault}} = 100\mu\text{s}$:

$$Q_{\text{max}} \approx \frac{10 \times 0.98}{0.001} + \frac{10 \times 0.02}{0.0011} \approx 9800 + 182 \approx 9982 \text{ queries/s}$$

Nas palavras do próprio Zaratustra: *"Es muss noch ein Chaos in sich haben, um einen tanzenden Stern gebären zu können."* Este é o caos controlado — 48 crates, 16 column families, três formatos de WAL, quatro versões de storage — do qual nasce a estrela dançante de um banco de dados que pensa.
