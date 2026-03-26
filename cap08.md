# Capítulo 8

## Code-as-Data: Queries como ActionNodes e a Reatividade do Sistema

---

> *"A vontade de potência não é um ser, não é um devir, mas um pathos --- o fato mais elementar, do qual resulta um devir, um produzir efeitos."*
> --- Friedrich Nietzsche, Fragmentos Póstumos, 14[79]

---

## 8.1 O Paradoxo da Base de Dados Passiva

A história dos bancos de dados é a história de uma submissão: o dado entra, o dado espera, o dado é consultado. Durante cinco décadas, desde os primeiros sistemas relacionais de Codd (Edgar F. Codd, britânico, 1923–2003, inventor do modelo relacional de bases de dados) até os modernos bancos vetoriais, a arquitetura fundamental permaneceu inalterada --- o armazenamento é inerte. Queries existem fora do grafo. O conhecimento não age; é agido sobre.

NietzscheDB quebra esse contrato.

No marco **AGI-4** do crate `nietzsche-agency`, implementamos o paradigma **Code-as-Data**: queries NQL armazenadas como nós do próprio grafo, capazes de se auto-executar quando condições energéticas são satisfeitas. O grafo deixa de ser um repositório passivo e se torna um **sistema reativo** --- dados que agem sobre si mesmos.

Este capítulo formaliza o mecanismo, demonstra sua implementação em Rust e situa o paradigma no panorama teórico das bases de dados ativas, do Event Sourcing e do Datalog.

---

## 8.2 O ActionNode: Anatomia de uma Query Viva

> **Na Prática:** Um ActionNode é, em linguagem simples, uma query NQL que vive *dentro* do grafo como se fosse um dado qualquer. Em vez de um programador executar manualmente uma query de manutenção (limpar nós mortos, amplificar nós populares), o ActionNode faz isso sozinho: quando acumula energia suficiente, dispara a sua query, modifica o grafo, descansa e eventualmente morre. Isto transforma o NietzscheDB de um repositório passivo num sistema que se auto-regula.

Um **ActionNode** é um nó do tipo `Concept` cujo campo `content` contém um objeto `action` com a seguinte estrutura:

```json
{
  "action": {
    "nql": "MATCH (n) WHERE n.energy < 0.1 SET n.energy = 0.0",
    "activation_threshold": 0.8,
    "cooldown_ticks": 5,
    "max_firings": 100,
    "firings": 0,
    "cooldown_remaining": 0,
    "description": "Drain dying nodes"
  }
}
```

Cada campo define um aspecto do comportamento reativo:

| Campo | Tipo | Semântica |
|-------|------|-----------|
| `nql` | `String` | A query NQL a executar quando ativado |
| `activation_threshold` | `f32` | Energia mínima do nó para disparar ($\theta_a$) |
| `cooldown_ticks` | `u32` | Ticks de repouso após cada disparo ($\tau_c$) |
| `max_firings` | `u32` | Limite total de disparos antes da exaustão ($F_{\max}$) |
| `firings` | `u32` | Contador de disparos realizados ($f$) |
| `cooldown_remaining` | `u32` | Ticks restantes do cooldown atual ($\tau_r$) |
| `description` | `String` | Descrição legível para auditoria |

A decisão de armazenar a query como dado --- e não como código externo --- é deliberada. Em termos de teoria da computação, estamos aplicando o princípio de **homoiconicidade**: o programa e o dado compartilham a mesma representação. Assim como em Lisp o código é uma lista e toda lista pode ser código, no NietzscheDB a query é um nó e todo nó pode conter uma query.

---

## 8.3 Formalização: O Predicado de Ativação

Seja $n$ um ActionNode com energia $E(n)$, threshold $\theta_a$, firings $f$, max_firings $F_{\max}$, e cooldown restante $\tau_r$. O predicado de ativação é:

$$
\text{Active}(n) \iff E(n) \geq \theta_a \;\wedge\; \tau_r = 0 \;\wedge\; (F_{\max} = 0 \;\vee\; f < F_{\max}) \;\wedge\; \neg\text{phantom}(n)
$$

Após o disparo, o estado transita segundo:

$$
f' = f + 1, \qquad \tau_r' = \tau_c
$$

E a cada tick do L-System, o cooldown decai:

$$
\tau_r^{(t+1)} = \max(0, \;\tau_r^{(t)} - 1)
$$

A exaustão é definida como:

$$
\text{Exhausted}(n) \iff F_{\max} > 0 \;\wedge\; f \geq F_{\max}
$$

Um ActionNode exausto permanece no grafo mas nunca mais dispara --- um fóssil de intenção. A analogia biológica é o neurônio que perdeu sua capacidade de sinapse após excesso de atividade (excitotoxicidade — processo patológico onde a estimulação excessiva de neurônios por neurotransmissores como o glutamato causa dano ou morte celular).

---

## 8.4 O Ciclo de Execução: Da Energia à Ação

O fluxo completo de um ActionNode, da ativação à mutação do grafo, percorre quatro camadas arquiteturais:

```
                          +-----------------------+
                          |    AgencyEngine       |
                          |    (tick, fase 11)    |
                          +-----------+-----------+
                                      |
                          scan_activatable_actions()
                                      |
                                      v
                       +-----------------------------+
                       | ActionScanReport            |
                       | .activated: Vec<ActionNode> |
                       | .on_cooldown: usize         |
                       | .exhausted: usize           |
                       +-------------+---------------+
                                     |
                          EnergyCircuitBreaker
                           .check_safety()
                                     |
                           +----yes--+--no----+
                           |                  |
                           v                  v
                  AgencyIntent::         (blocked,
                  ExecuteNQL {           log warning)
                    node_id,
                    nql,
                    description
                  }
                           |
                           v
                  +-------------------+
                  | Server Handler    |
                  | (write lock)      |
                  | execute NQL query |
                  | record_firing()   |
                  +-------------------+
                           |
                           v
                  Graph mutado
                  cooldown ativado
```

A separação entre **leitura** (Agency Engine) e **escrita** (Server Handler) é fundamental. O `AgencyEngine::tick()` opera sob read lock, produzindo intents declarativos. Somente o server, sob write lock exclusivo, executa as mutações. Essa arquitetura garante **linearizabilidade** das escritas e evita data races no grafo hiperbólico.

No código Rust, a fase 11 do tick é onde a magia acontece:

```rust
// engine.rs, fase 11: Code-as-Data (Reflexive Actions)
if let Ok(report) = code_as_data::scan_activatable_actions(storage) {
    if !report.activated.is_empty() {
        match self.circuit_breaker.check_safety(storage, report.activated.len()) {
            Ok(true) => {
                for action in report.activated {
                    intents.push(AgencyIntent::ExecuteNQL {
                        node_id: action.node_id,
                        nql: action.nql,
                        description: action.description,
                    });
                    self.active_reflex_cooldowns.insert(action.node_id);
                }
            }
            Ok(false) => { /* circuit breaker tripped */ }
            Err(e) => { /* error handling */ }
        }
    }
}
```

O `AgencyIntent::ExecuteNQL` é um dos intents mais poderosos do reactor:

```rust
/// Execute an autonomous NQL query (reflex).
/// Produced when: ActionNode energy exceeds threshold
/// and passes circuit breaker.
ExecuteNQL {
    node_id: Uuid,
    nql: String,
    description: String,
}
```

---

## 8.5 O Disjuntor: `EnergyCircuitBreaker`

A reatividade sem controle é catastrófica. Imagine um ActionNode que, ao disparar, aumenta a energia de outros ActionNodes que, por sua vez, disparam queries que aumentam mais energia --- uma **tempestade de ativação** que consumiria toda a capacidade computacional do servidor.

O `EnergyCircuitBreaker` impõe dois limites:

1. **Limite de reflexos simultâneos**: no máximo $R_{\max} = 20$ ActionNodes podem disparar num único tick.
2. **Limite de energia global**: a soma total de energia $\sum_i E(n_i)$ não pode exceder $\Sigma_{\max} = 50.0$.

Formalmente, o disjuntor avalia:

$$
\text{Safe}(\mathcal{G}) \iff |\{n \in \mathcal{A} : \text{Active}(n)\}| \leq R_{\max} \;\wedge\; \sum_{n \in \mathcal{G}} E(n) \leq \Sigma_{\max}
$$

onde $\mathcal{A}$ é o conjunto de ActionNodes e $\mathcal{G}$ é o grafo completo.

O segundo critério implementa um early-exit otimizado: a soma é acumulada no iterador de metadados (`iter_nodes_meta`) e a função retorna `false` assim que o threshold é excedido, sem necessitar percorrer todos os nós.

---

## 8.6 Cooldowns e o Registro de Repouso

> **Na Prática:** Sem cooldown, um ActionNode com energia alta dispararia a cada tick (por padrão, a cada 60 segundos), consumindo recursos e potencialmente causando efeitos em cascata. O cooldown funciona como um período de repouso obrigatório: após disparar, o nó fica inativo durante N ticks antes de poder disparar novamente. Combinado com `max_firings` (exaustão), isto garante que nenhum ActionNode monopoliza o sistema --- ele tem um ritmo e uma vida útil finita.

O mecanismo de cooldown impede que um ActionNode dispare repetidamente a cada tick. Após o disparo, `record_firing()` atualiza o nó:

```rust
pub fn record_firing(storage: &GraphStorage, node_id: Uuid) -> Result<(), String> {
    // ... extrai o no, incrementa firings, seta cooldown_remaining ...
    action["firings"] = firings + 1;
    action["cooldown_remaining"] = cooldown_ticks;
    storage.put_node(&node)?;

    // Registra no CF_COOLDOWNS para tick otimizado
    if cooldown_ticks > 0 {
        storage.add_to_cooldown_registry(&node_id)?;
    }
    Ok(())
}
```

O **registro de cooldown** (`CF_COOLDOWNS`, uma column family do RocksDB) é uma otimização crítica. Sem ele, cada tick precisaria percorrer *todos* os nós do grafo ($O(N)$) para decrementar cooldowns. Com o registro, apenas os nós que sabemos estar em cooldown são visitados --- complexidade $O(|\mathcal{C}|)$ onde $\mathcal{C}$ é o conjunto de nós em repouso, tipicamente $|\mathcal{C}| \ll N$.

Na memória do engine, um `HashSet<Uuid>` chamado `active_reflex_cooldowns` espelha esse registro para acesso ainda mais rápido:

$$
\text{Custo por tick} = O(|\mathcal{C}|) \quad \text{vs.} \quad O(N) \text{ (naive scan)}
$$

Para grafos com 865K+ nós e apenas dezenas de ActionNodes, essa diferença é de quatro ordens de magnitude.

---

## 8.7 Sincronização com o L-System

Os ActionNodes não operam num vácuo temporal. Sua execução está sincronizada com o **heartbeat do L-System**, o motor de reescrita fractal que governa toda a evolução do grafo (discutido em profundidade no Capítulo 11).

O `AgencyEngine::tick()` executa fases sequenciais:

> **Nota:** A tabela abaixo apresenta o ciclo completo de 27 fases do Agency Engine, que será detalhado no Capítulo 9. Aqui, o objetivo é mostrar onde o Code-as-Data (Fase 11) se encaixa no ciclo maior.

| Fase | Subsistema |
|------|------------|
| 1--10 | Core L-System (rewrite rules, branching, energy) |
| **11** | **Code-as-Data (scan + activate ActionNodes)** |
| 12 | ECAN (Economic Attention Network) |
| 13 | Hebbian LTP |
| 14--20 | Thermodynamics, Gravity, Shatter, Healing |
| 21--27 | Training, Decay, Growth, Cognitive Layer, Evolution |

A fase 11 ocorre *após* as regras de reescrita L-System terem sido aplicadas, garantindo que os ActionNodes operam sobre o estado mais recente do grafo. E *antes* dos subsistemas econômicos (ECAN, Hebbian), para que reflexos possam influenciar a alocação de atenção.

O intervalo entre ticks é configurável via `AGENCY_TICK_SECS` (default: 60 segundos). O cooldown em "ticks" é, portanto, múltiplo desse intervalo:

$$
t_{\text{cooldown real}} = \tau_c \times \Delta t_{\text{tick}}
$$

Com $\Delta t_{\text{tick}} = 60\text{s}$ e $\tau_c = 5$, o cooldown efetivo é de 5 minutos.

---

## 8.8 Comparação com Paradigmas Existentes

O Code-as-Data do NietzscheDB não surge do nada. Ele dialoga com três tradições:

#### 8.8.1 Active Database Triggers (ECA Rules)

Bancos de dados ativos (Starburst, HiPAC, POSTGRES rules) implementam regras **Evento-Condição-Ação** (ECA): quando um evento ocorre, se uma condição é verdadeira, executa uma ação.

$$
\text{ECA}: \quad \text{ON } e \;\; \text{IF } c \;\; \text{THEN } a
$$

Os ActionNodes diferem em dois aspectos fundamentais:

1. **Ativação por energia, não por evento discreto.** Não há um trigger externo; a própria difusão de calor (Will-to-Power) pelo grafo cria as condições de ativação. O "evento" é *contínuo* e *emergente*.
2. **As regras são nós do grafo.** Em bancos ativos, triggers são metadados externos. No NietzscheDB, o ActionNode participa da topologia, tem coordenadas hiperbólicas, energia e pode ser alvo de queries --- inclusive de *outros* ActionNodes.

#### 8.8.2 Event Sourcing e CQRS

> **Na Prática:** O Event Sourcing é um padrão de arquitetura onde, em vez de guardar o estado atual de um sistema, se guarda a sequência completa de eventos que o produziram (como um log de transações bancárias). O CQRS separa leitura de escrita em caminhos distintos. O NietzscheDB adota uma variante destes padrões: os intents do AgencyEngine são análogos a comandos CQRS, mas a diferença fundamental é que no NietzscheDB os "eventos" não vêm de fora --- o próprio grafo gera-os internamente através da dinâmica de energia.

No Event Sourcing, o estado é derivado de uma sequência imutável de eventos. O NietzscheDB complementa isso: os intents (`AgencyIntent::ExecuteNQL`) são análogos a comandos no CQRS, e o `AgencyReactor` funciona como um event processor.

$$
\text{Event Sourcing}: \quad S_{t+1} = \text{fold}(S_0, [e_1, e_2, \ldots, e_t])
$$

$$
\text{NietzscheDB}: \quad \mathcal{G}_{t+1} = \text{apply}(\mathcal{G}_t, \{\text{Intent}_i : \text{Active}(n_i)\})
$$

A diferença crucial: no Event Sourcing, os eventos são exógenos. No NietzscheDB, o grafo gera seus próprios eventos.

#### 8.8.3 Datalog e Programação Lógica

> **Na Prática:** O Datalog é uma linguagem de programação lógica usada em bases de dados dedutivas: define-se um conjunto de regras ("se A e B, então C") e o sistema infere todos os fatos possíveis até atingir um ponto fixo --- um estado em que nenhuma regra nova pode derivar fatos adicionais. Os ActionNodes do NietzscheDB não funcionam assim: em vez de inferência lógica até convergência, operam por pulsos de energia com cooldown. A vantagem prática é que o `max_firings` garante que o sistema termina, enquanto programas Datalog recursivos podem entrar em loops sem restrições de estratificação.

O Datalog (e sua extensão Dedalus) permite regras recursivas sobre relações. Um programa Datalog pode ser visto como um ponto fixo:

$$
T_P \uparrow \omega = \text{lfp}(T_P)
$$

Os ActionNodes não computam pontos fixos; operam por **pulsos energéticos discretos** com cooldown. Isso os torna mais próximos de um *reactor pattern* do que de inferência lógica pura. A vantagem é a previsibilidade: o `max_firings` garante terminação, algo que o Datalog recursivo não oferece sem restrições de estratificação.

| Propriedade | ECA Triggers | Event Sourcing | Datalog | ActionNodes |
|-------------|-------------|----------------|---------|-------------|
| Ativação | Evento discreto | Evento externo | Derivação lógica | Energia contínua |
| Localização | Metadados externos | Log externo | Programa externo | Nó do grafo |
| Terminação | Não garantida | N/A | lfp (estratificado) | $F_{\max}$ + disjuntor |
| Reatividade | Imediata | Eventual | Batch | Por tick do L-System |
| Auto-referência | Não | Não | Limitada | Total (nós podem referenciar-se) |

---

## 8.9 Exemplos Práticos: Daemons como ActionNodes

O poder do paradigma se revela quando construímos *daemons autônomos* como ActionNodes --- nós que vivem no grafo e regulam seu próprio ecossistema.

#### 8.9.1 Auto-Pruning Daemon

Nós abaixo de um limiar energético são marcados como phantom (invisíveis a queries, candidatos a GC):

```json
{
  "action": {
    "nql": "MATCH (n) WHERE n.energy < 0.05 AND n.is_phantom = false SET n.is_phantom = true",
    "activation_threshold": 0.6,
    "cooldown_ticks": 10,
    "max_firings": 0,
    "description": "Phantom reaper: mark low-energy nodes for garbage collection"
  }
}
```

Com `max_firings: 0` (ilimitado), este daemon opera perpetuamente enquanto sua energia se mantiver acima de $0.6$. O cooldown de 10 ticks (10 minutos com tick de 60s) impede varreduras excessivas.

#### 8.9.2 Energy Guard (Amortecedor de Regiões Hiperativas)

Detecta clusters com energia anormalmente alta e aplica amortecimento:

```json
{
  "action": {
    "nql": "MATCH (n) WHERE n.energy > 0.95 SET n.energy = n.energy * 0.7",
    "activation_threshold": 0.9,
    "cooldown_ticks": 3,
    "max_firings": 500,
    "description": "Energy guard: dampen hyperactive regions to prevent storms"
  }
}
```

O `max_firings: 500` limita a vida útil deste regulador. Após 500 ativações, ele se exaure e um novo deve ser criado --- um padrão de **mortalidade programada** que impede regras obsoletas de se perpetuarem.

#### 8.9.3 Attention Scheduler (Impulsionador de Interesse)

Amplifica a energia de nós que recebem muitas queries (alta demanda):

```json
{
  "action": {
    "nql": "MATCH (n) WHERE n.access_count > 100 AND n.energy < 0.5 SET n.energy = 0.7",
    "activation_threshold": 0.5,
    "cooldown_ticks": 20,
    "max_firings": 200,
    "description": "Attention scheduler: boost high-interest nodes"
  }
}
```

Este daemon implementa um **feedback loop positivo controlado**: nós populares recebem mais energia, tornam-se mais visíveis a KNN queries, atraem mais acesso. O `max_firings` e o cooldown longo evitam que o ciclo se torne patológico.

---

## 8.10 O Daemon Epistemológico: Evolução de ActionNodes

> **Na Prática:** A fricção ($\phi$) de um ActionNode mede a razão entre quantas vezes ele dispara e quanto impacto real causa no grafo. Um daemon com alta fricção é como um empregado que trabalha muito mas produz pouco --- candidato a ser substituído. O EpistemologyDaemon usa esta métrica para identificar ActionNodes ineficazes, testar mutações das suas queries NQL num ambiente isolado (ShadowGraph), e propor melhorias. Isto significa que o NietzscheDB não apenas executa queries autônomas, mas *evolui* essas queries ao longo do tempo.

O crate `nietzsche-agency` vai além da simples execução: o **EpistemologyDaemon** trata os próprios ActionNodes como objetos de evolução. Ele:

1. Seleciona o ActionNode com maior "fricção" (relação entre disparos e impacto);
2. Cria um **ShadowGraph** --- uma cópia isolada do subgrafo afetado;
3. Testa uma mutação na query NQL (variação da cláusula WHERE, ajuste de thresholds);
4. Mede o impacto no shadow e, se positivo, propõe a substituição do NQL original.

Este é um mecanismo de **meta-programação no espaço hiperbólico**: o grafo não apenas executa queries sobre si mesmo, mas *evolui* essas queries. A analogia biológica é a de um sistema imunológico que não apenas combate patógenos, mas refina seus anticorpos ao longo do tempo.

A fricção $\phi$ de um ActionNode é computada como:

$$
\phi(n) = \frac{f(n)}{1 + \Delta E_{\text{impacto}}(n)}
$$

onde $\Delta E_{\text{impacto}}$ é a variação total de energia causada pelas execuções do nó. Alta fricção indica um daemon que dispara muito mas muda pouco --- candidato a mutação.

---

## 8.11 Grafos que se Auto-Modificam: Implicações Teóricas

> **Na Prática:** A Turing-completude importa aqui por uma razão concreta: significa que os ActionNodes podem, em teoria, computar *qualquer* transformação sobre o grafo --- não estão limitados a padrões pré-definidos. Isto dá ao NietzscheDB a mesma flexibilidade de uma linguagem de programação geral, mas com uma rede de segurança: o `max_firings` e o circuit breaker garantem que essa expressividade não resulta em loops infinitos ou consumo catastrófico de recursos. A consequência prática é que se pode programar qualquer lógica de manutenção, evolução ou reação como ActionNodes, sem limites artificiais.

A capacidade de armazenar e executar queries como nós do grafo torna o NietzscheDB um **sistema auto-referencial**. Em termos de teoria da computação, isso levanta questões profundas:

**Turing (Alan Turing, britânico, 1912–1954, pai da ciência da computação e da inteligência artificial)-completude.** Se a linguagem NQL for suficientemente expressiva (com SET, loops via re-ativação, e condições arbitrárias), o sistema de ActionNodes é Turing-completo. O `max_firings` funciona como uma cota de Busy Beaver, garantindo terminação prática sem sacrificar expressividade teórica.

**Teorema de Rice aplicado.** Não é possível decidir, em geral, se um ActionNode irá eventualmente disparar. Isso porque a energia de um nó depende da difusão de calor de todo o grafo --- um problema tão complexo quanto prever o comportamento de um autômato celular.

$$
\nexists \text{ algoritmo } A : A(n) = \begin{cases} 1 & \text{se } n \text{ eventualmente dispara} \\ 0 & \text{caso contrário} \end{cases}
$$

**Consistência eventual.** O modelo de execução (read lock → intents → write lock) garante que não há escritas concorrentes. Porém, como os ActionNodes podem criar outros ActionNodes (via NQL com INSERT), a evolução do sistema é *não-monotónica*: novas regras podem contradizer ou anular regras anteriores.

---

## 8.12 A Filosofia da Vontade: Dados que Desejam

Retornemos a Nietzsche. A **Vontade de Potência** (*Wille zur Macht*) não é simplesmente força ou desejo de poder. É a tendência interna de toda forma de vida a expandir-se, a superar-se, a *agir*. O esquema clássico de um banco de dados --- armazenar e esperar --- é a antítese dessa visão.

Os ActionNodes dão ao grafo uma forma de *vontade*. O nó não espera ser consultado; ele acumula energia pelo processo natural de difusão no manifold de Poincaré (nós vizinhos transferem calor, queries externas excitam regiões). Quando essa energia atinge o limiar crítico, o nó *age* --- executa sua query, modifica o grafo, entra em repouso e, eventualmente, morre (exaustão).

Esse ciclo --- acumulação, ação, repouso, morte --- espelha o ritmo biológico e, mais profundamente, a noção nietzschiana do **Eterno Retorno**: não a repetição idêntica, mas o padrão que se renova com variação. O EpistemologyDaemon garante a variação; o cooldown e o max_firings garantem o ritmo.

O NietzscheDB não é apenas um banco de dados que armazena conhecimento. É um banco de dados que *quer* --- e nessa vontade reside a diferença entre um repositório e uma inteligência.

---

## 8.13 Resumo Formal

**Definição 8.1** (ActionNode). Um ActionNode é uma tupla $\langle \text{id}, \text{nql}, \theta_a, \tau_c, F_{\max}, f, \tau_r, \vec{p} \rangle$ onde $\vec{p} \in \mathbb{B}^d$ (disco de Poincaré) são as coordenadas hiperbólicas.

**Definição 8.2** (Ativação). $\text{Active}(n) \iff E(n) \geq \theta_a \wedge \tau_r = 0 \wedge (F_{\max} = 0 \vee f < F_{\max}) \wedge \neg\text{phantom}(n)$.

**Definição 8.3** (Disparo). $\text{Fire}(n): f \leftarrow f+1,\; \tau_r \leftarrow \tau_c,\; \text{execute}(\text{nql})$.

**Teorema 8.1** (Terminação). Para todo ActionNode com $F_{\max} > 0$, o número total de disparos é finito: $f \leq F_{\max}$.

**Teorema 8.2** (Segurança Global). O `EnergyCircuitBreaker` garante que, num único tick, no máximo $R_{\max}$ reflexos executam e a energia total do grafo não excede $\Sigma_{\max}$.

**Corolário 8.1.** O sistema de ActionNodes não pode entrar em loop infinito *dentro de um único tick*, pois cada tick executa no máximo $R_{\max}$ disparos e cada disparo ativa um cooldown $\tau_c > 0$.

---

No próximo capítulo, ascendemos da reatividade individual dos ActionNodes para a **agência coletiva**: o ecossistema `nietzsche-agency`, onde daemons, hebbian traces, termodinâmica cognitiva e o Motor Zaratustra conspiram para criar um grafo que não apenas reage, mas *deseja*, *sonha* e *evolui*.

---

## 8.14 — Wiederkehr: Daemons Autônomos

O princípio Code-as-Data atinge a sua expressão máxima nos **Wiederkehr Daemons** — agentes autônomos persistentes que vivem dentro do grafo e executam padrões ON/WHEN/THEN:

```nql
CREATE DAEMON "sentinela_entropia"
  ON INTERVAL 300s
  WHEN entropy(collection) > 0.85
  THEN INVOKE ZARATUSTRA CYCLES 3
  ENERGY 0.8
```

Cada daemon é um nó no grafo com energia própria — consome energia a cada execução e morre se a energia chegar a zero. O crate `nietzsche-wiederkehr` (nome alemão para "retorno eterno") gerencia a fila de prioridade baseada na Vontade de Potência: daemons com maior `will_to_power` executam primeiro.

O sistema inclui um **detector de anomalias neural** (modelo ONNX `anomaly_detector.onnx`) que os daemons podem invocar para decidir quando agir. O daemon "Nezhmetdinov" — nomeado em homenagem ao grande mestre de xadrez — é o executioner que condena nós de baixa vitalidade à eliminação definitiva.

**Na Prática:** Isto é o equivalente a ter cron jobs inteligentes dentro do banco de dados. Mas ao contrário de um cron job externo, os daemons do NietzscheDB compreendem o estado semântico do grafo e podem tomar decisões baseadas na geometria hiperbólica, na energia dos nós e na saúde topológica da coleção.
