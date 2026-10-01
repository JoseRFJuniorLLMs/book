# Relatório de Revisão — Resposta à checklist de Mariana Cerigatto

**Obra:** *NietzscheDB — O Abismo que Te Observa*
**Capítulos revisados:** cap00 a cap19 (20 arquivos, ~95.000 palavras)
**Data:** 18/06/2026
**Repositório:** `NietzscheDB-Book` (pasta `CAPITULOS/`), branch `main`

---

## Resumo para a Mariana

Olá, Mariana! Passei os 20 capítulos pelos cinco pontos que você pediu.
Segue o status item a item — três já estavam em conformidade e dois exigiram
ação, com destaque para o **item 3 (palavras estrangeiras em itálico)**, onde
padronizei o manuscrito inteiro. Tudo foi validado tecnicamente (os 20
capítulos convertem sem erro via `pandoc -f gfm`) e já está commitado.

| # | Item da checklist | Status |
|---|---|---|
| 1 | Conceitos e código corretos | ✅ **ok** — auditoria código-vs-fonte concluída; nada pendente |
| 2 | Imagens com resolução para impressão | ✅ **ok / N/A** — não há imagens embutidas no miolo (ver ressalva da capa) |
| 3 | Palavras estrangeiras em itálico (`* *`/`_ _`) | ✅ **ok — corrigido** (223 termos, 1º uso por capítulo) |
| 4 | Nomes técnicos padronizados (ex.: Docker) | ✅ **ok** — já em conformidade; nenhuma correção necessária |
| 5 | Imagens de terceiros com citação de fonte | ✅ **ok / N/A** — não há imagens de terceiros no miolo |

---

## Item 1 — Conceitos e código corretos ✅

**Status: ok.** A correção técnica do conteúdo foi tratada numa auditoria
dedicada que cruzou cada capítulo com o **código-fonte real do NietzscheDB**
(48 *crates* Rust, o `.proto` com os RPCs, a gramática NQL `.pest` e os modelos
ONNX físicos). Essa auditoria está registrada em `relatorio_codigo_vs_livro.md`
e teve **todos os itens fechados**, incluindo:

- número correto de RPCs (82) e de modelos ONNX (cap00, cap16);
- descrição correta do Pregel (heat-kernel/Chebyshev) (cap02, cap05);
- lista completa de algoritmos de grafo (cap05);
- inclusão do Capítulo 18 (produção) para cobrir observabilidade/deployment;
- correções de PQ *magnitude-preserving*, CDC, HybridSearch (BM25+ANN com RRF),
  transações NQL, *constraints* e arquétipos.

**Verificação adicional feita nesta passagem:**
- Os **20 capítulos convertem sem erro** com `pandoc -f gfm -t html` (markdown
  bem-formado; blocos de código, tabelas e fórmulas íntegros).
- As correções de itálico desta revisão **não tocaram em nenhum bloco de
  código, fórmula ou identificador** — apenas em texto corrido (detalhe no
  item 3).

> Observação honesta: "código correto" aqui significa *fiel ao sistema real e
> internamente consistente*. Os trechos de código são ilustrativos do
> NietzscheDB; não são um pacote compilável isolado dentro do livro (e nem se
> propõem a ser).

---

## Item 2 — Imagens com tamanho/resolução para impressão ✅ / N/A

**Status: ok, com uma ressalva sobre a capa.**

O miolo dos 20 capítulos **não contém nenhuma imagem rasterizada embutida**.
Por decisão editorial registrada (manter a obra reprodutível e versionável em
texto), **todos os diagramas são arte ASCII** dentro de blocos de código — não
há `.png`/`.jpg` inseridos via `![](...)` em nenhum capítulo. Portanto, não há
risco de imagem pixelada/serrilhada no miolo: o que escala é tipografia, não
*bitmap*.

As duas únicas imagens `.png` do repositório (`imagens/borda_ruim.png`,
`imagens/fonte_pequena.png`) **pertencem ao guia da editora** (são os exemplos
de "borda ruim" e "fonte pequena" usados em `02-exemplo.md`/`03-mais_coisas.md`)
— não são figuras do livro.

**Ressalva — a capa:** o único asset de imagem real da obra é
`cover.jpg` (**709 × 1000 px, 72 DPI**). Para impressão, isso fica **abaixo do
ideal de 300 DPI** (uma capa A5 a 300 DPI pediria ~1654 × 2480 px). Se a capa
final for gerada pelo template da Casa do Código (`THEME=cdc-tema`), o arquivo
atual serve apenas como prévia e isto é irrelevante. **Recomendo confirmar com
você** se a capa de impressão sai do template da editora ou se devo entregar
um `cover.jpg` em alta resolução.

---

## Item 3 — Palavras estrangeiras em minúsculo, em itálico (`* *`/`_ _`) ✅ CORRIGIDO

**Status: corrigido em toda a obra.**

### O que foi feito
Padronizei os termos técnicos em inglês para aparecerem em **itálico no
primeiro uso de cada capítulo**, com asteriscos (`*termo*`) — a mesma marcação
que o livro já usava. Foram **223 ocorrências** italicizadas, distribuídas
pelos 20 capítulos.

### Critério (alinhado ao guia da própria editora)
Segui literalmente `03-mais_coisas.md` e `05-nossos_padroes.md`:

> *"O itálico pode ser usado para termos em inglês que apareçam raramente... Se
> for um termo que aparece com frequência, pode utilizá-lo sem destaque algum."*
> — *"Itálico para palavras estrangeiras no primeiro uso... de forma
> consistente."*

Por isso a regra aplicada foi **itálico no 1º uso por capítulo, depois texto
normal** — assim cada palavra estrangeira é sinalizada ao leitor quando aparece,
sem encher uma obra técnica e densa de itálicos repetidos (um termo como
*embedding* ou *tick* aparece dezenas de vezes; grifá-lo toda vez prejudicaria
a leitura, contra a orientação da editora).

### Distribuição por capítulo

| Cap | itálicos | Cap | itálicos | Cap | itálicos | Cap | itálicos |
|---|---|---|---|---|---|---|---|
| 00 | 22 | 05 | 18 | 10 | 11 | 15 | 8 |
| 01 | 4  | 06 | 12 | 11 | 7  | 16 | 14 |
| 02 | 22 | 07 | 16 | 12 | 2  | 17 | 9 |
| 03 | 9  | 08 | 6  | 13 | 11 | 18 | 25 |
| 04 | 6  | 09 | 15 | 14 | 4  | 19 | 2 |

São mais densos os capítulos de infraestrutura (00, 02, 18) e mais raros os de
matemática pura (12, 14, 19), como esperado.

### Termos padronizados (inventário)
Os termos italicizados foram, entre outros:
*backend, frontend, framework, pipeline, parser, parsing, runtime, build,
release, deploy, deployment, dashboard, endpoint, container, crate, cache,
buffer, heap, pool, thread, lock, snapshot, rollback, replay, checkpoint,
fallback, batch, payload, schema, token, plugin, query, queries, embedding,
cluster, tick, hub, overhead, throughput, streaming, scrape, routing, gossip,
sharding, shard, pruning, tuning, default, timeout, feature, ranking, scoring,
seed, backup, benchmark, software, hardware, zero-copy, cold storage,
garbage collection, data warehouse, random walk*.

### Garantias de segurança da edição
A italicização foi **automatizada com mascaramento** das regiões onde NÃO se
deve mexer, depois validada:
- **não toca** em blocos de código (```` ``` ````), código *inline* (`` `...` ``),
  fórmulas matemáticas, URLs, títulos de seção, nem nas **referências
  bibliográficas** (evita italicizar palavras dentro de títulos de obras em
  inglês);
- **não duplica** itálicos já existentes (se a 1ª ocorrência já estava grifada,
  foi deixada como estava);
- **só minúsculas** (conforme você pediu) — nomes próprios capitalizados
  (`Docker`, `Python`) não foram afetados;
- singular/plural contam como **uma palavra** (italiciza só a 1ª das duas).

> **Decisão que registro para sua avaliação:** mantive *fora* do itálico os
> termos já **naturalizados** no português técnico brasileiro quando funcionam
> como vocabulário corrente (ex.: *site*, *web*, *online*, *status*, *bit*,
> *byte*, *log*) e os **nomes próprios/identificadores** (nomes de *crates*,
> comandos, variáveis — que já vivem em `código`). Se preferir uma política
> mais ou menos inclusiva (por exemplo, grifar *toda* ocorrência, ou poupar
> também *software*/*hardware* por já serem do cotidiano), é um ajuste de um
> parâmetro e eu re-rodo a padronização na hora.

---

## Item 4 — Nomes técnicos padronizados conforme a documentação ✅

**Status: ok — já estava em conformidade. Nenhuma correção foi necessária.**

Varri os 20 capítulos atrás de nomes próprios de tecnologia em caixa errada.
O manuscrito **já segue a grafia oficial** de cada projeto:

- **Maiúsculas/CamelCase corretos:** `Docker`, `Python`, `Rust`, `Tokio`,
  `Kafka`, `Prometheus`, `RocksDB`, `NVIDIA`, `CUDA`, `GraphQL`, `Cassandra`,
  `Postgres`, `WebAssembly`, `JavaScript`, `GitHub`, `Merkle`, `Matryoshka`.
- **Minúsculas que estão corretas porque a marca oficial é minúscula**
  (não são erros): `systemd`, `nginx` e `protobuf`. A documentação oficial
  desses projetos grafa o nome em caixa baixa — então mantê-los assim **é** a
  padronização correta. (No caso de `protobuf`, o livro inclusive já traz a
  tradução na 1ª aparição: *"protobuf (Protocol Buffers — formato binário... do
  Google)"*, cap06.)
- **Siglas** (`GPU`, `CPU`, `RAM`, `SSD`, `API`, `WAL`, `RPC`, `gRPC`, `HTTP`,
  `MCP`, `LLM`, `TGC`, `NQL`, `AQL`) em caixa alta, consistentes.

Conclusão: **0 correções** neste item — o ponto já estava resolvido.

---

## Item 5 — Imagens de terceiros precisam de citação de fonte ✅ / N/A

**Status: ok, não se aplica ao miolo.**

Como o item 2 detalha, **não há imagens de terceiros (livros, sites, blogs) no
miolo dos 20 capítulos** — não há figura rasterizada alguma a creditar. Todos os
diagramas são **arte ASCII autoral**, gerada para a própria obra; pela sua
própria regra ("imagens feitas por você / IA / capturas de tela não precisam de
fonte"), não há nada a citar.

As referências a sistemas e artigos de terceiros (Mem0, Zep, LoCoMo, RocksDB,
papers de geometria hiperbólica etc.) já aparecem como **citações
bibliográficas em texto**, nas seções `## Referências` dos capítulos
pertinentes (cap01, cap05, cap07, cap09, cap10, cap14) — e essas seções foram
**preservadas intactas** (a padronização do item 3 as ignora de propósito).

Se em alguma etapa futura forem inseridas figuras externas (um diagrama de um
paper, um screenshot de outra ferramenta), aí sim cada uma precisará da fonte no
formato AUTOR (ano, página) ou link — mas hoje **não existe esse caso na obra**.

---

## Metodologia e rastreabilidade

- A padronização de itálico foi feita por um script com mascaramento de
  código/fórmula/título/referência e revisada item a item antes de aplicar
  (223 edições conferidas).
- Validação pós-edição: **20/20 capítulos** passam em `pandoc -f gfm` sem erro;
  varredura confirmou que **nenhum** itálico novo caiu dentro de bloco de código.
- As alterações estão num único commit sobre os 20 arquivos `cap*.md`, na branch
  `main` — `git diff` mostra exclusivamente trocas de `palavra` → `*palavra*`
  em texto corrido.

**Pendência que depende de você (Mariana):**
1. Confirmar a política de itálico do item 3 (a regra "1º uso por capítulo" me
   parece a leitura correta do guia, mas é sua a palavra final).
2. Definir se a **capa** de impressão sai do template da Casa do Código ou se
   devo fornecer `cover.jpg` em 300 DPP.

Qualquer ajuste de política, eu re-rodo a padronização no mesmo dia.
