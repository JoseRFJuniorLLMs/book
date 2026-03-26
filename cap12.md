# Capítulo 12 — Arestas de Schrödinger: Superposição probabilística e colapso de contexto

> *"Deus está morto; mas, considerando o estado em que se encontra a espécie humana, talvez ainda existam cavernas durante milênios nas quais a sombra dele será exibida."*
> — Friedrich Nietzsche, *A Gaia Ciência*

Em mecânica quântica, o gato de Schrödinger existe simultaneamente vivo e morto até que uma observação force a realidade a escolher. No NietzscheDB, uma aresta entre "Maçã" e "Isaac Newton" pode existir ou não — depende de quem pergunta e em que contexto. Este capítulo disseca o **Quantum-Inspired Cognitive Kernel**: cinco camadas de emulação estocástica que transformam um grafo estático em um organismo que muda de forma a cada consulta.

**Aviso fundamental**: nada aqui é computação quântica real. Não há coerência física, não há emaranhamento de partículas, não há qubits de silício. O NietzscheDB roda em hardware clássico com uma GPU NVIDIA. O que fizemos foi tomar emprestado o *formalismo matemático* — superposição, colapso Bayesiano, propagação de emaranhamento — como modelo computacional efetivo para gerir incerteza em um grafo semântico. A inspiração teórica vem da **Orchestrated Objective Reduction (Orch-OR)** de Roger Penrose (britânico, 1931–, Nobel de Física, teórico dos buracos negros e da consciência quântica) e Stuart Hameroff (americano, 1947–, anestesiologista e teórico da consciência em microtúbulos), que propõe que a consciência emerge de processos quânticos em microtúbulos neuronais. Nós não fazemos afirmações sobre consciência. Fazemos grafos que mudam quando você olha para eles.

---

## 12.1 Arquitetura de Cinco Camadas

**Na Prática:** Antes de mergulhar na arquitetura, eis a ideia central: num banco de grafos tradicional (Neo4j, Neptune), cada aresta ou existe ou não existe. Uma query vê sempre o mesmo grafo. No NietzscheDB, as arestas têm probabilidades que mudam com o contexto. Quando você pesquisa sobre física, a aresta de "Maçã" para "Newton" se torna forte. Quando você pesquisa sobre culinária, enfraquece. As cinco camadas abaixo são a maquinaria que faz esta topologia sensível ao contexto funcionar.

Antes de mergulhar na matemática, veja a torre completa. Cada camada constrói sobre a anterior:

```
┌─────────────────────────────────────────────────────────────────┐
│  Camada 5 — DeliberationCoordinator                             │
│  Gatilhos: ambiguidade semantica, conflito de valencia,         │
│  saturacao de cascata, inconsistencia historica                  │
│  Max 4 deliberacoes concorrentes                                │
├─────────────────────────────────────────────────────────────────┤
│  Camada 4 — CognitiveSuperpositionGraph                         │
│  Beam search sobre topologia hiperbolica com poda Bayesiana     │
│  Multiplas "realidades cognitivas" competindo                   │
│  Vencedor → grafo permanente; perdedores → residuo probabilist. │
├─────────────────────────────────────────────────────────────────┤
│  Camada 3 — CoherenceEvaluator                                  │
│  C(r) = lambda_g*G(r) + lambda_s*S(r) + lambda_t*T(r)          │
│  Geometrica (Poincare) + Semantica (cosseno) + Topologica (grau)│
├─────────────────────────────────────────────────────────────────┤
│  Camada 2.1 — Semantic Entanglement                             │
│  Propagacao de colapso: I(A→B) = w_AB * mu_type * gamma^d       │
│  Anti-cascata: decay=0.5, max_depth=3, min_influence=0.05       │
├─────────────────────────────────────────────────────────────────┤
│  Camada 2 — QuantumMicrotubuleManager                           │
│  Registro por-no de estados probabilisticos (SemanticQudits)    │
│  Pipeline lock-free: detect → collapse → emit → propagate       │
├─────────────────────────────────────────────────────────────────┤
│  Camada 1 — SemanticQudit                                       │
│  Unidade atomica: N hipoteses em superposicao                   │
│  |psi> = sum c_i |i>  com sum |c_i|^2 = 1                      │
│  Entropia de Shannon normalizada como metrica de decisao        │
├─────────────────────────────────────────────────────────────────┤
│  Camada 0 — Schrodinger Edges                                   │
│  Arestas probabilisticas com decaimento e boost de contexto     │
│  Colapso em tempo de MATCH via amostragem estocastica           │
└─────────────────────────────────────────────────────────────────┘
```

O fluxo é ascendente: arestas de Schrödinger colapsam individualmente (Camada 0), qudits semânticos acumulam evidência e colapsam (Camadas 1-2), o colapso propaga via emaranhamento (Camada 2.1), subgrafos são avaliados por coerência (Camada 3), múltiplas interpretações competem (Camada 4), e gatilhos de deliberação coordenam quando o sistema inteiro deve reavaliar suas crenças (Camada 5).

---

## 12.2 Camada 0 — Arestas de Schrödinger

### O Problema da Associação Fixa

Em bancos de grafos tradicionais, uma aresta existe ou não. A relação `(Maçã) --[ASSOCIATED]--> (Isaac Newton)` é binária: 1 ou 0. Mas em cognição humana, essa associação tem probabilidade variável. Se você está pensando em física, a maçã de Newton aparece imediatamente. Se está pensando em culinária, a maçã é ingrediente de torta. O contexto muda a topologia.

**Na Prática:** Como é que os bancos existentes lidam com relações dependentes de contexto? O Neo4j usa múltiplos tipos de aresta e filtros de propriedade — você cria arestas separadas RELACIONADO_FISICA e RELACIONADO_CULINARIA, depois filtra em query time. O Weaviate usa cross-references com filtragem de metadados. O Qdrant oferece filtragem baseada em payload. Todas estas abordagens exigem que o programador pré-defina categorias de contexto. As arestas de Schrödinger do NietzscheDB aprendem contexto automaticamente através de padrões de uso: arestas acessadas em contextos de física auto-reforçam-se para física, sem nenhuma alteração de schema.

### Definição Formal

Uma **aresta de Schrödinger** é um wrapper probabilístico sobre uma aresta convencional:

```rust
pub struct SchrodingerEdge {
    pub edge: Edge,
    pub probability: f32,    // p ∈ [0.0, 1.0], base
    pub decay_rate: f32,     // decaimento por tick
    pub context_boost: Option<String>,  // tag de contexto
    pub boost_factor: f32,   // multiplicador quando contexto bate
}
```

Os parâmetros são armazenados como metadados JSON na própria aresta:

```json
{
  "probability": 0.7,
  "decay_rate": 0.01,
  "context_boost": "physics",
  "boost_factor": 1.5
}
```

**Na Prática:** Cenário concreto. A aresta (Maçã)--[ASSOCIADA]-->(Newton) está armazenada com probabilidade base 0.7, context_boost "física" e boost_factor 1.5. O usuário pergunta: "Fala-me das descobertas de Newton." O contexto contém "física," então a probabilidade efetiva se torna min(0.7 × 1.5, 1.0) = 1.0 — a aresta é certa. Mas se o usuário pergunta "Melhor receita de torta de maçã," sem contexto de física, a probabilidade fica em 0.7. Um sorteio aleatório pode excluir Newton (30% das vezes). No Pinecone ou no Weaviate, esta aresta estaria sempre lá ou nunca estaria. No NietzscheDB, existe em superposição.

### Probabilidade Efetiva

Dado um contexto de consulta $q$, a probabilidade efetiva de uma aresta $e$ é:

$$p_{\text{eff}}(e, q) = \min\!\Big(p_{\text{base}}(e) \times \beta(e, q),\; 1.0\Big)$$

onde o fator de boost $\beta$ é:

$$\beta(e, q) = \begin{cases} b_e & \text{se } q \supseteq \text{context\_boost}(e) \\ 1.0 & \text{caso contrário} \end{cases}$$

Aqui, $b_e$ é o `boost_factor` da aresta (default: 1.5) e $q \supseteq c$ significa que a string de contexto da consulta contém a tag de boost.

### Colapso

No momento do `MATCH` ou traversal, cada aresta de Schrödinger é colapsada:

$$\text{existe}(e, q) = \mathbb{1}\!\big[\text{rand}() < p_{\text{eff}}(e, q)\big]$$

onde $\text{rand}() \sim \mathcal{U}(0, 1)$. Se o número aleatório cai abaixo da probabilidade efetiva, a aresta materializa para esta consulta. Caso contrário, ela simplesmente não existe.

**Consequência fundamental**: a mesma query, executada duas vezes no mesmo instante, pode retornar topologias diferentes. O grafo é não-determinístico por design.

### Decaimento Temporal

Arestas não utilizadas enfraquecem a cada tick do Agency Engine:

$$p_{t+1} = \max\!\big(p_t - \delta,\; 0\big)$$

onde $\delta$ é a `decay_rate`. Uma aresta com $p = 0.5$ e $\delta = 0.01$ desaparece completamente após 50 ticks de inatividade. Inversamente, o uso bem-sucedido de uma aresta a reforça:

$$p' = \min\!\big(p + r,\; 1.0\big)$$

Esse mecanismo implementa a **lei de Hebb** no nível das conexões: arestas que participam de respostas bem-sucedidas se fortalecem; arestas ignoradas definham.

### Colapso por Emaranhamento

Além do colapso clássico baseado em probabilidade, o NietzscheDB suporta colapso forçado via **proxy de emaranhamento** (fenômeno quântico onde o estado de duas partículas fica correlacionado de tal forma que medir uma determina instantaneamente o estado da outra — aqui emulado como correlação semântica entre nós). Cada nó possui um estado na esfera de Bloch (representação geométrica de um estado quântico como ponto na superfície de uma esfera unitária — Seção 12.3), e a fidelidade quântica entre estados determina o acoplamento:

$$\mathcal{E}(A, B) = \frac{1}{|A| \cdot |B|} \sum_{a \in A} \sum_{b \in B} F(a, b)$$

onde a fidelidade entre dois estados de Bloch é:

$$F(\vec{r}_a, \vec{r}_b) = \frac{1 + \cos\alpha}{2}, \qquad \cos\alpha = \frac{\vec{r}_a \cdot \vec{r}_b}{\|\vec{r}_a\| \, \|\vec{r}_b\|}$$

Se $\mathcal{E} > \tau_{\text{emaranhamento}}$, a aresta materializa independentemente de sua probabilidade base — observar um lado de um par emaranhado força o outro a colapsar. Os thresholds são configuráveis por contexto:

| Contexto | Threshold $\tau$ | Descrição |
|----------|:---------:|-----------|
| Default | 0.85 | Uso geral |
| Strict | 0.90 | Segurança crítica (ex: dosagem médica) |
| Relaxed | 0.65 | Exploratório (ex: suporte psicológico) |

---

## 12.3 A Ponte Poincaré-Bloch

Antes de entrar nas camadas superiores, precisamos entender como o espaço hiperbólico do NietzscheDB se conecta ao formalismo quântico. A ponte é um **mapeamento conformal** do disco de Poincaré para a esfera de Bloch.

### Mapeamento

Dado um ponto $\vec{p}$ no disco de Poincaré (embedding de um nó) com norma $r = \|\vec{p}\|$ e energia $E \in [0, 1]$:

$$\theta = 2 \arctan(r), \qquad \phi = \text{atan2}(p_1, p_0)$$

$$\vec{v}_{\text{Bloch}} = E \begin{pmatrix} \sin\theta \cos\phi \\ \sin\theta \sin\phi \\ \cos\theta \end{pmatrix}$$

onde:
- $\theta \in [0, \pi)$ é o ângulo polar (coordenada radial → latitude na esfera)
- $\phi \in [0, 2\pi)$ é o ângulo azimutal (direção no disco → longitude)
- $E$ é a energia do nó, mapeada para **pureza** do estado quântico

**Na Prática:** A ponte Poincaré-Bloch permite ao NietzscheDB usar dois "vocabulários geométricos" para o mesmo nó. No disco de Poincaré, o nó tem posição hierárquica (profundidade) e direção semântica. Na esfera de Bloch, o mesmo nó tem um estado de "pureza" que determina a sua influência no colapso de arestas vizinhas. Nós abstratos perto da origem (ex: "ciência") mapeiam para estados puros com forte poder de decisão; nós periféricos específicos (ex: "teorema de Banach-Tarski") mapeiam para estados mistos, mais suscetíveis a serem influenciados por evidência externa.

O mapeamento é **conformal** (preserva ângulos): distâncias hiperbólicas no disco de Poincaré correspondem aproximadamente a fidelidades quânticas na esfera de Bloch. Um nó na origem ($r \approx 0$) mapeia para o polo norte ($\theta \approx 0$, estado $|0\rangle$). Um nó próximo à fronteira ($r \to 1$) mapeia para o equador ($\theta \to \pi/2$).

A operação inversa recupera o ponto original:

$$r = \tan(\theta/2), \qquad p_0 = r\cos\phi, \qquad p_1 = r\sin\phi$$

### Gates Quânticos

O NietzscheDB define quatro portas lógicas que operam sobre estados de Bloch:

- **$R_x(\alpha)$**: rotação em torno do eixo X por ângulo $\alpha$
- **$R_y(\alpha)$**: rotação em torno do eixo Y
- **$R_z(\alpha)$**: rotação em torno do eixo Z (muda longitude sem alterar latitude)
- **Hadamard**: $|0\rangle \to |+\rangle$, move o polo norte para o equador — $(x, y, z) \to (z, -y, x)$

**Na Prática:** A porta Hadamard é particularmente importante: ela move um nó do polo norte (estado decidido, "isto é X") para o equador (superposição máxima, "isto pode ser X ou Y"). No NietzscheDB, aplicar Hadamard a uma aresta significa forçar incerteza — útil quando o sistema detecta que uma relação foi classificada prematuramente e precisa ser reaberta para reavaliação. As rotações $R_x$, $R_y$, $R_z$ permitem ajustes mais finos: "girar a perspectiva" de um conceito sem destruir a informação acumulada.

Essas portas permitem manipular estados semânticos sem sair do formalismo quântico. Uma rotação $R_z(\pi/2)$ sobre um conceito é equivalente a girar sua perspectiva semântica em 90 graus.

---

## 12.4 Camada 1 — SemanticQudit

**Na Prática:** No NietzscheDB, um qudit resolve o problema de nós ambíguos. Considere o nó "banco" — pode significar instituição financeira, assento de parque, ou banco de dados. Em vez de forçar uma escolha no momento da inserção, o qudit mantém as três hipóteses em superposição simultânea com probabilidades que evoluem conforme o contexto de uso. Quando evidência suficiente se acumula (a entropia de Shannon cai abaixo do limiar), o qudit colapsa para a interpretação mais provável naquele contexto — e o NietzscheDB "decide" sem intervenção humana.

### De Qubits a Qudits

Um qubit (a unidade fundamental de informação quântica, análoga ao bit clássico mas capaz de existir em superposição de 0 e 1 simultaneamente) sustenta dois estados simultâneos: $|0\rangle$ e $|1\rangle$. Um **qudit** (generalização do qubit para $N$ estados em vez de apenas 2) generaliza para $N$ dimensões. No NietzscheDB, o `SemanticQudit` é a unidade atômica de superposição cognitiva — capaz de sustentar $N$ hipóteses concorrentes até que evidência suficiente force um colapso.

O nome é uma homenagem ao modelo de tubulina de **Stuart Hameroff**, onde cada proteína de tubulina sustenta superposições quânticas.

### Vetor de Estado

O estado de um qudit com $N$ hipóteses é uma distribuição categórica normalizada:

$$|\psi\rangle = \sum_{i=1}^{N} c_i |i\rangle, \qquad \sum_{i=1}^{N} |c_i|^2 = 1$$

onde cada $|c_i|^2$ é a probabilidade da hipótese $i$ ser verdadeira. O qudit é inicializado em superposição uniforme: $|c_i|^2 = 1/N$ para todo $i$.

### Invariantes

O `SemanticQudit` mantém quatro invariantes invioláveis:

1. $\sum |c_i|^2 = 1$ (normalização) — vale após qualquer operação
2. $|c_i|^2 \geq 0$ para todo $i$
3. Após colapso (`is_collapsed = true`), gravidade semântica não tem efeito
4. O RNG nunca é instanciado internamente — sempre injetado pelo caller

### Entropia de Shannon Normalizada

Para medir o grau de incerteza do qudit, usamos a entropia de Shannon normalizada, em homenagem a **Claude Shannon** (1916-2001):

$$H_{\text{norm}} = \frac{-\sum_{i=1}^{N} p_i \ln(p_i)}{\ln(N)}$$

onde $p_i = |c_i|^2$. O valor está sempre em $[0, 1]$:

- $H_{\text{norm}} = 0.0$: totalmente decidido (uma hipótese com $P = 1$)
- $H_{\text{norm}} = 1.0$: incerteza máxima (distribuição uniforme)

Esta métrica responde à pergunta fundamental: *quando colapsar?* Quando a entropia cai abaixo de um limiar configurável, o qudit acumulou evidência suficiente para tomar uma decisão principiada.

### Gravidade Semântica (Penrose)

A acumulação de evidência segue o teorema de Bayes. O método `penrose_gravity` — nomeado em homenagem a **Roger Penrose** (Nobel de Física 2020) — implementa:

$$P(H_i \mid E) = \frac{P(E \mid H_i) \cdot P(H_i)}{\sum_{j=1}^{N} P(E \mid H_j) \cdot P(H_j)}$$

onde:
- $P(H_i)$ é o prior: o valor atual de $|c_i|^2$
- $P(E \mid H_i)$ é a likelihood: o vetor de evidência fornecido pelo contexto do grafo
- $P(H_i \mid E)$ é o posterior: a nova distribuição após absorver a evidência

Na teoria Orch-OR de Penrose, a auto-energia gravitacional determina quando uma superposição quântica se torna instável e deve colapsar. Aqui, a "gravidade" é a evidência contextual do grafo semântico que puxa a distribuição em direção a certas hipóteses.

**Segurança**: se toda a evidência for zero (aniquilação total), a distribuição reseta para uniforme em vez de deixar pesos nulos — prevenindo um panic fatal no colapso subsequente.

### Redução Objetiva (Penrose)

Quando as condições de colapso são satisfeitas, `penrose_reduction` executa a **redução objetiva** — uma amostragem categórica ponderada (análogo da regra de Born):

$$P(\text{selecionar } i) = |c_i|^2$$

A hipótese $i$ é selecionada com probabilidade proporcional ao seu peso na distribuição. O colapso é **irreversível**: chamadas subsequentes retornam o mesmo resultado sem re-amostrar. Isso é fisicamente correto no framework Orch-OR — a observação não pode ser desfeita.

**Na Prática:** O colapso pela regra de Born é o momento em que o NietzscheDB "toma uma decisão." Se o nó "mercúrio" tinha 60% de probabilidade para "planeta" e 40% para "elemento químico," o colapso seleciona uma das hipóteses proporcionalmente a esses pesos. Após colapsar, essa decisão fica registrada como um CollapseEvent imutável — o sistema sabe que decidiu, quando decidiu, e com que nível de certeza. A re-superposição de Hameroff permite que o ciclo recomece com um ligeiro viés para a resposta anterior, modelando o fato de que experiências passadas influenciam decisões futuras.

### Re-superposição (Hameroff)

Após o colapso, o ciclo não termina. `hameroff_resuperpose` — nomeado em homenagem a **Stuart Hameroff** — reinicializa o qudit em superposição, mas com um **prior cognitivo**:

$$P(i) = \frac{\frac{1}{N} + b \cdot \delta(i, w)}{\sum_{j=1}^{N} \big(\frac{1}{N} + b \cdot \delta(j, w)\big)}$$

onde $w$ é o vencedor do colapso anterior e $b$ é o `prior_boost` (tipicamente 0.1 a 0.3). O sistema "lembra" o que funcionou antes sem ficar preso a isso.

Isso modela a proposta de Hameroff de que a re-coerência dos microtúbulos não é um reset em branco, mas carrega informação estrutural do momento consciente anterior.

### Ciclo de Vida Completo

```
  ┌──────────────────────────────────────────────┐
  │ 1. Inicializacao: superposicao uniforme      │
  │    P(i) = 1/N,  H_norm = 1.0                │
  └──────────┬───────────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────┐
  │ 2. Gravidade Semantica (Bayesiano iterativo) │
  │    P(H|E) ∝ P(E|H) · P(H)                   │
  │    H_norm decresce a cada rodada             │
  └──────────┬───────────────────────────────────┘
             │  H_norm < threshold?
             ▼
  ┌──────────────────────────────────────────────┐
  │ 3. Reducao Objetiva (Born rule)              │
  │    Amostragem categorica ponderada           │
  │    Colapso irreversivel                      │
  └──────────┬───────────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────┐
  │ 4. Re-superposicao (Hameroff)                │
  │    Reset com prior boost no vencedor         │
  │    Volta para passo 2                        │
  └──────────────────────────────────────────────┘
```

---

## 12.5 Camada 2 — Quantum Microtubule Manager

O `SemanticQudit` é a unidade atômica. O `QuantumMicrotubuleManager` é o registro que associa um qudit a cada nó do grafo que sustenta ambiguidade.

### Modelo Conceitual

Na biologia de Hameroff, microtúbulos são cilindros proteicos dentro dos neurônios. Cada tubulina é um bit quântico. O conjunto de microtúbulos de um neurônio sustenta uma superposição coletiva.

No NietzscheDB, cada **nó** com múltiplas interpretações possíveis recebe um `SemanticQudit`. O `QuantumMicrotubuleManager` gerencia a coleção desses qudits e orquestra seu ciclo de vida.

### Pipeline Lock-Free

O processamento de estimulação segue um pipeline de quatro estágios sem locks globais:

```
detect → collapse → emit → propagate
```

1. **Detect**: identifica nós cuja entropia caiu abaixo do limiar de colapso
2. **Collapse**: executa `penrose_reduction` em cada qudit pronto
3. **Emit**: gera `CollapseEvent` para cada colapso ocorrido
4. **Propagate**: alimenta a Camada 2.1 (emaranhamento semântico)

### Estimulação e Resultado

Quando o Agency Engine fornece nova evidência a um nó, o manager processa:

$$\text{StimulationResult} = \begin{cases} \text{Evolving}(H_{\text{norm}}) & \text{se } H_{\text{norm}} \geq \tau_{\text{collapse}} \\ \text{Collapsed}(\text{CollapseEvent}) & \text{se } H_{\text{norm}} < \tau_{\text{collapse}} \\ \text{Error}(e) & \text{em caso de falha} \end{cases}$$

### CollapseEvent

Cada colapso gera um evento estruturado:

```rust
CollapseEvent {
    node_id: Uuid,
    selected_hypothesis: usize,
    entropy: f64,                    // H_norm no momento do colapso
    probabilities_snapshot: Vec<f64> // distribuicao congelada
}
```

Este evento é imutável e constitui o registro histórico de cada decisão tomada pelo sistema. A sequência de `CollapseEvent`s forma a **narrativa de decisões** do grafo — um log de como a incerteza foi resolvida ao longo do tempo.

---

## 12.6 Camada 2.1 — Emaranhamento Semântico

**Na Prática:** O emaranhamento semântico significa que decisões não acontecem isoladamente no NietzscheDB. Se o nó "vírus" colapsa para a hipótese "agente patogênico" (em vez de "vírus informático"), essa decisão se propaga para vizinhos: "infecção" se torna mais provável de colapsar como biológica, "transmissão" segue na mesma direção. Mas a propagação é controlada — decai pela metade a cada hop e morre após 3 saltos, evitando que uma única decisão force todo o grafo a uma interpretação uniforme.

### Propagação de Colapso

Quando um nó $A$ colapsa, nós vizinhos devem ser influenciados — mas não de forma irrestrita. A **influência de colapso** de $A$ sobre $B$ é:

$$I(A \to B) = w_{AB} \cdot \mu_{\text{type}} \cdot \gamma^d$$

onde:
- $w_{AB}$ é o peso da aresta entre $A$ e $B$
- $\mu_{\text{type}}$ é o multiplicador do tipo de aresta
- $\gamma$ é o fator de decaimento por profundidade (default: 0.5)
- $d$ é a distância em hops a partir do nó que colapsou originalmente

### Multiplicadores por Tipo de Aresta

Nem todas as relações propagam influência igualmente:

| Tipo de Aresta | $\mu_{\text{type}}$ | Justificativa |
|:---------------|:-------------------:|:--------------|
| `CONTAINS` | 1.0 | Composição: colapso do todo afeta as partes |
| `HAS` | 0.9 | Propriedade: quase tão forte quanto composição |
| `CAUSES` | 0.8 | Causalidade: efeito segue causa, mas com incerteza |
| `RELATED_TO` | 0.5 | Associação genérica: influência moderada |

### Mecanismo Anti-Cascata

Sem restrições, um único colapso poderia propagar indefinidamente e colapsar o grafo inteiro — o equivalente de um ataque epiléptico em um cérebro artificial. O NietzscheDB implementa quatro mecanismos de contenção:

1. **Fator de decaimento**: $\gamma = 0.5$ — a influência cai pela metade a cada hop
2. **Profundidade máxima**: $d_{\max} = 3$ — nenhuma propagação além de 3 hops
3. **Influência mínima**: $I_{\min} = 0.05$ — influências abaixo desse limiar são descartadas
4. **Período refratário**: um nó recém-colapsado não pode ser re-colapsado por propagação durante um número configurável de ticks

A influência efetiva após $d$ hops com decaimento:

$$I_{\text{eff}}(d) = w \cdot \mu \cdot \gamma^d = w \cdot \mu \cdot 0.5^d$$

Para $d = 3$: $I_{\text{eff}} = w \cdot \mu \cdot 0.125$. Com $w = 1.0$ e $\mu = 0.5$ (RELATED_TO): $I_{\text{eff}} = 0.0625$ — já próximo ao limiar de corte.

### Exemplo Concreto

Considere a cadeia:

```
Neuronio [CONTAINS] → Microtubulo [CAUSES] → Superposicao [RELATED_TO] → Consciencia
```

Se "Neurônio" colapsa para a hipótese "excitatória":

| Hop | Nó | $\mu$ | $\gamma^d$ | $I$ |
|:---:|:---|:-----:|:----------:|:---:|
| 1 | Microtúbulo | 1.0 (CONTAINS) | 0.5 | $w \cdot 0.50$ |
| 2 | Superposição | 0.8 (CAUSES) | 0.25 | $w \cdot 0.20$ |
| 3 | Consciência | 0.5 (RELATED_TO) | 0.125 | $w \cdot 0.0625$ |

A influência chega até "Consciência" mas com força residual. Se $w = 0.7$, a influência final é $0.7 \times 0.0625 = 0.044 < I_{\min}$ — o sinal morre antes de chegar.

---

## 12.7 Camada 3 — Avaliador de Coerência

### Motivação

Após propagação de colapsos, como saber se a região resultante do grafo "faz sentido"? O `CoherenceEvaluator` pontua subgrafos combinando três dimensões ortogonais.

### Fórmula Composta

A coerência de uma região $r$ do grafo é:

$$C(r) = \lambda_g \cdot G(r) + \lambda_s \cdot S(r) + \lambda_t \cdot T(r)$$

onde $\lambda_g + \lambda_s + \lambda_t = 1$ e:

**$G(r)$ — Coerência Geométrica (Poincaré)**:

$$G(r) = 1 - \frac{\sigma_d}{\bar{d}}$$

onde $\bar{d}$ é a profundidade média dos nós na região (norma do embedding no disco de Poincaré) e $\sigma_d$ é o desvio padrão. Valores altos indicam que os nós estão em níveis hierárquicos similares — uma região coerente geometricamente.

**$S(r)$ — Coerência Semântica (Cosseno)**:

$$S(r) = \frac{2}{|r|(|r|-1)} \sum_{i < j} \frac{\vec{v}_i \cdot \vec{v}_j}{\|\vec{v}_i\| \, \|\vec{v}_j\|}$$

A similaridade de cosseno média entre todos os pares de embeddings na região. Regiões onde os nós apontam na mesma direção semântica recebem pontuação alta.

**$T(r)$ — Coerência Topológica (Grau)**:

$$T(r) = 1 - \frac{\text{Var}(\deg(v) : v \in r)}{(\max \deg - \min \deg)^2 + \epsilon}$$

Mede a homogeneidade da conectividade. Uma região onde todos os nós têm grau semelhante é topologicamente coerente; uma região com um hub de grau 500 ao lado de folhas de grau 1 não é.

### Integração com a Camada 2.1

O avaliador de coerência é chamado *após* a propagação de emaranhamento para validar o resultado. Se $C(r) < C_{\min}$, a propagação é revertida — o sistema reconhece que o colapso produziu uma configuração incoerente e restaura os qudits afetados ao estado anterior.

---

## 12.8 Camada 4 — Grafo de Superposição Cognitiva

### Beam Search Bayesiano

A Camada 4 é onde a metáfora quântica atinge seu ápice. O `CognitiveSuperpositionGraph` mantém **múltiplas realidades cognitivas competindo** — interpretações alternativas do mesmo subgrafo, cada uma com sua própria topologia colapsada.

O algoritmo é um **beam search sobre topologia hiperbólica com poda Bayesiana**:

1. **Inicialização**: a partir de uma consulta, gera $k$ interpretações iniciais colapsando arestas de Schrödinger com sementes aleatórias diferentes
2. **Expansão**: cada interpretação propaga colapsos pela Camada 2.1 e expande nós vizinhos
3. **Avaliação**: cada interpretação recebe uma pontuação de coerência $C(r)$ da Camada 3
4. **Poda Bayesiana**: interpretações com $C(r)$ abaixo de um limiar adaptativo são descartadas

$$P(\text{manter } r_i) \propto C(r_i) \cdot \prod_{e \in r_i} p_{\text{eff}}(e)$$

5. **Iteração**: os $k$ melhores candidatos sobrevivem para a próxima rodada de expansão
6. **Terminação**: quando o beam converge (todas as interpretações levam a topologias equivalentes) ou o budget de exploração se esgota

### Destino dos Vencedores e Perdedores

O resultado é assimétrico:

- **Vencedor**: a interpretação com maior $C(r)$ é fundida no grafo permanente. Arestas de Schrödinger que participaram têm sua probabilidade base reforçada.
- **Perdedores**: não são descartados completamente. Deixam um **resíduo probabilístico** — suas arestas de Schrödinger têm probabilidades ligeiramente reduzidas, mas não zeradas. Em consultas futuras com contexto diferente, essas interpretações "fantasma" podem ressurgir.

Isso modela o fenômeno cognitivo de **priming negativo**: ideias rejeitadas conscientemente ainda influenciam decisões futuras de forma subliminar.

---

## 12.9 Camada 5 — Coordenador de Deliberação

**Na Prática:** O Deliberation Coordinator é o "sistema judicial" do NietzscheDB — só intervém quando há conflito que as camadas inferiores não conseguem resolver sozinhas. Na maioria das queries, arestas colapsam, emaranhamento propaga, e o resultado é coerente. Mas quando o sistema detecta que está "mudando de ideia" repetidamente sobre o mesmo nó, ou que um colapso gerou uma cascata que foi cortada prematuramente, a Camada 5 ativa um beam search dedicado para resolver a ambiguidade com mais recursos computacionais. O limite de 4 deliberações simultâneas evita que o sistema gaste toda a CPU em resolução de conflitos.

### Gatilhos

A Camada 5 não opera continuamente. Ela é ativada por quatro condições específicas:

**1. Ambiguidade Semântica**: um nó recebe evidência contraditória — sua entropia de Shannon sobe em vez de descer após uma rodada de `penrose_gravity`. Formalmente:

$$H_{\text{norm}}^{(t)} > H_{\text{norm}}^{(t-1)} + \epsilon_{\text{ambiguidade}}$$

**2. Conflito de Valência**: dois nós emaranhados tentam colapsar para hipóteses mutuamente exclusivas. A fidelidade quântica entre os estados colapsados cai abaixo de um limiar crítico:

$$F(\vec{r}_A, \vec{r}_B) < \tau_{\text{conflito}}$$

**3. Saturação de Cascata**: a propagação de colapso pela Camada 2.1 atingiu o limite de profundidade ($d_{\max} = 3$) e ainda havia influências acima de $I_{\min}$ sendo cortadas. Isso indica que a decisão tinha ramificações que não puderam ser totalmente avaliadas.

**4. Inconsistência Histórica**: o `CollapseEvent` atual contradiz colapsos anteriores do mesmo nó. O sistema detecta que está "mudando de ideia" repetidamente:

$$|\{e \in \text{history}(n) : e.\text{hypothesis} \neq e_{\text{atual}}.\text{hypothesis}\}| > k_{\text{flip}}$$

### Restrições

O coordenador impõe um limite estrito de **4 deliberações concorrentes**. Cada deliberação é uma instância completa da Camada 4 (beam search) com budget dedicado. Se um quinto gatilho dispara enquanto quatro deliberações estão ativas, ele entra em fila de espera.

### Ciclo de Deliberação

```
Gatilho detectado
    │
    ▼
Alocacao de deliberacao (1 de 4 slots)
    │
    ▼
CognitiveSuperpositionGraph.beam_search(subgrafo relevante)
    │
    ▼
Avaliacao de coerencia (Camada 3)
    │
    ▼
Fusao do vencedor + residuo dos perdedores
    │
    ▼
Liberacao do slot
```

---

## 12.10 A Matemática Completa: Unificando as Camadas

Para referência, aqui estão todas as fórmulas do Quantum-Inspired Cognitive Kernel em sequência.

### Camada 0 — Schrödinger Edges

$$p_{\text{eff}}(e, q) = \min\!\big(p_{\text{base}} \cdot \beta(e, q),\; 1\big)$$

$$\text{existe}(e, q) = \mathbb{1}\!\big[\mathcal{U}(0,1) < p_{\text{eff}}(e, q)\big]$$

$$p_{t+1} = \max(p_t - \delta, 0) \quad \text{(decaimento)}$$

### Ponte Poincaré-Bloch

$$\theta = 2\arctan(\|\vec{p}\|), \quad \phi = \text{atan2}(p_1, p_0), \quad \text{pureza} = E$$

$$F(\vec{r}_a, \vec{r}_b) = \frac{1 + \hat{r}_a \cdot \hat{r}_b}{2}, \quad \mathcal{E}(A,B) = \frac{1}{|A||B|}\sum_{a,b} F(a,b)$$

### Camada 1 — SemanticQudit

$$|\psi\rangle = \sum_{i=1}^{N} c_i |i\rangle, \quad \sum_i |c_i|^2 = 1$$

$$H_{\text{norm}} = \frac{-\sum_i p_i \ln p_i}{\ln N}$$

$$P(H_i \mid E) = \frac{P(E \mid H_i) \cdot P(H_i)}{\sum_j P(E \mid H_j) \cdot P(H_j)} \quad \text{(gravidade)}$$

$$P(\text{selecionar } i) = |c_i|^2 \quad \text{(redução)}$$

$$P_{\text{re-sup}}(i) = \frac{\frac{1}{N} + b \cdot \delta_{i,w}}{\sum_j \big(\frac{1}{N} + b \cdot \delta_{j,w}\big)} \quad \text{(re-superposição)}$$

### Camada 2.1 — Emaranhamento

$$I(A \to B) = w_{AB} \cdot \mu_{\text{type}} \cdot \gamma^d$$

$$I_{\text{eff}} = 0 \quad \text{se } d > 3 \text{ ou } I < 0.05$$

### Camada 3 — Coerência

$$C(r) = \lambda_g \cdot G(r) + \lambda_s \cdot S(r) + \lambda_t \cdot T(r)$$

### Camada 4 — Beam Search

$$P(\text{manter } r_i) \propto C(r_i) \cdot \prod_{e \in r_i} p_{\text{eff}}(e)$$

---

## 12.11 Implicações Práticas

### Consistência Eventual, Não Imediata

O modelo de Schrödinger implica que **não há topologia canônica**. Dois clientes consultando o mesmo grafo no mesmo instante podem obter resultados diferentes. Isso é uma feature, não um bug. Cada consulta é uma "observação" que colapsa o grafo de forma única.

Para cenários que exigem determinismo, o NietzscheDB permite fixar a semente do RNG por consulta:

```python
# Consulta deterministica: mesma semente → mesma topologia
response = stub.QueryNodes(
    pb.QueryNodesRequest(
        collection="brain",
        nql="MATCH (n:Concept) -[r]-> (m) RETURN n, r, m",
        context_hint="physics",
        rng_seed=42  # fixa o colapso
    )
)
```

### Performance

O overhead das arestas de Schrödinger é mínimo: uma multiplicação extra e uma comparação por aresta durante o traversal. O custo real está nas camadas superiores — o beam search da Camada 4 é $O(k \cdot |E_{\text{subgrafo}}|)$ onde $k$ é o tamanho do beam. Na prática, $k \leq 8$ é suficiente para a maioria dos cenários.

### Debugging

Debugar um sistema não-determinístico exige ferramentas específicas:

1. **CollapseEvent log**: registro imutável de cada decisão, com entropy e snapshot de probabilidades
2. **Semente fixa**: reproduzir uma consulta com a mesma semente produz o mesmo colapso
3. **Entropy heatmap**: visualização no dashboard HTTP dos nós por nível de incerteza
4. **Deliberation trace**: log detalhado de cada sessão de beam search

---

## 12.12 Schrödinger na Prática: Um Exemplo Completo

Considere um grafo de conhecimento médico. O nó "Aspirina" tem arestas para "Dor de Cabeça" (CAUSES, $p = 0.9$), "Hemorragia" (CAUSES, $p = 0.3$, context_boost: "hematologia"), e "Willow Tree" (RELATED_TO, $p = 0.2$, context_boost: "botânica").

**Consulta 1**: contexto = "dor de cabeça"
- Aspirina → Dor de Cabeça: $p_{\text{eff}} = 0.9$ (sem boost, contexto não bate)
- Aspirina → Hemorragia: $p_{\text{eff}} = 0.3$ (sem boost)
- Aspirina → Willow Tree: $p_{\text{eff}} = 0.2$ (sem boost)
- Resultado provável: o grafo mostra Aspirina ligada a Dor de Cabeça.

**Consulta 2**: contexto = "hematologia clínica"
- Aspirina → Dor de Cabeça: $p_{\text{eff}} = 0.9$
- Aspirina → Hemorragia: $p_{\text{eff}} = \min(0.3 \times 1.5, 1.0) = 0.45$ (boost ativado)
- Aspirina → Willow Tree: $p_{\text{eff}} = 0.2$
- Resultado provável: o grafo mostra Aspirina ligada a Hemorragia *e* Dor de Cabeça.

**Consulta 3**: contexto = "botânica histórica"
- Aspirina → Willow Tree: $p_{\text{eff}} = \min(0.2 \times 1.5, 1.0) = 0.3$ (boost ativado)
- A relação etimológica entre aspirina e o salgueiro emerge.

O mesmo nó, três consultas, três topologias. O grafo se reorganiza em torno do observador.

---

## 12.13 Conexão com o Modelo Hiperbólico

O Quantum-Inspired Cognitive Kernel não existe isolado — ele se integra profundamente com a geometria hiperbólica do NietzscheDB. A ponte Poincaré-Bloch (Seção 12.3) garante que:

1. **Hierarquia preservada**: nós próximos da origem (conceitos abstratos, alta na hierarquia) mapeiam para o polo norte da esfera de Bloch — estados de alta pureza com forte influência no colapso de vizinhos.

2. **Distância = incerteza**: nós próximos da fronteira do disco ($r \to 1$) mapeiam para o equador — estados de menor pureza, mais suscetíveis a mudança por evidência externa.

3. **Emaranhamento reflete vizinhança hiperbólica**: nós com alta fidelidade quântica são necessariamente próximos no espaço hiperbólico. O emaranhamento semântico respeita a geometria.

A curvatura negativa do espaço hiperbólico é um aliado natural da superposição: a exponencial expansão de área com a distância significa que há "espaço" para um número exponencial de interpretações coexistirem sem interferir entre si — até que uma observação force o colapso.

---

> *"É preciso ter caos dentro de si para dar à luz a uma estrela dançarina."*
> — Friedrich Nietzsche, *Assim Falou Zaratustra*

O próximo capítulo examina o TGC — Thermodynamic Graph Completeness — a métrica-mestre que quantifica a saúde generativa do grafo, integrando energia, entropia, curvatura e criticalidade num único indicador de vitalidade cognitiva.
