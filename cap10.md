# Capítulo 10 — Ciclos de Sono e Reconsolidação: Otimização RiemannianAdam e Identidade via Hausdorff

> *"Dormir é o ato mais corajoso da consciência: abandonar o controle para que o caos reorganize aquilo que a vigília cristalizou."*

---

## 10.1 O Sono como Necessidade Topológica

Todo sistema que acumula informação continuamente enfrenta um problema inevitável: a entropia local dos embeddings cresce, mínimos locais aprisionam nós em posições subótimas, e a estrutura global do grafo diverge lentamente da geometria que melhor representaria suas relações semânticas. Em sistemas biológicos, o sono resolve esse problema. No NietzscheDB, o crate `nietzsche-sleep` implementa uma solução análoga — um ciclo de reconsolidação periódica que re-otimiza os embeddings hiperbólicos sem destruir a identidade acumulada do grafo.

O sono não é um luxo. É uma necessidade topológica.

Quando o motor de agência executa ticks (detalhado no Capítulo 11) — criando arestas hebbianas, decaindo energia, promovendo nós — ele opera em modo *greedy*: cada decisão é localmente ótima mas globalmente míope. Após centenas de ticks, os embeddings no disco de Poincaré acumulam distorções. Nós que deveriam estar próximos (por compartilharem muitas arestas) encontram-se afastados. Nós que deveriam ocupar a periferia (conceitos especializados) invadem regiões centrais. A árvore hierárquica, que deveria emergir naturalmente da geometria hiperbólica, começa a parecer uma teia emaranhada.

O ciclo de sono do NietzscheDB executa cinco fases, nesta ordem:

1. **Perturbação** — ruído controlado para escapar de mínimos locais
2. **Re-otimização Riemanniana** — gradiente descendente no disco de Poincaré via RiemannianAdam
3. **Rebalanceamento de Murray** — equilíbrio fractal vascular
4. **Ajuste de Hausdorff** — monitoramento da dimensão fractal como métrica de identidade
5. **Checkpoint de embeddings** — snapshot para rollback seguro

Cada fase será derivada matematicamente nas seções seguintes.

---

## 10.2 Fase 1: Perturbação Controlada

> **Na Prática:** Perturbação Controlada é uma técnica de otimização onde se adiciona ruído intencional aos dados para escapar de soluções "presas" (mínimos locais). O NietzscheDB precisa disto porque, após muitas operações, os embeddings hiperbólicos podem ficar estagnados em posições subótimas — a perturbação "sacode" o sistema para que a re-otimização seguinte encontre posições melhores.

O primeiro passo do ciclo de sono é paradoxal: antes de otimizar, *pioramos* deliberadamente. Introduzimos ruído gaussiano nos embeddings para perturbar o estado atual e escapar de mínimos locais do landscape de perda.

Dado um embedding $x \in \mathbb{B}^d$ (o disco de Poincaré aberto de dimensão $d$), a perturbação é:

$$\tilde{x} = \exp_x(\epsilon \cdot \xi), \quad \xi \sim \mathcal{N}(0, I_d)$$

onde $\exp_x$ é o mapa exponencial no disco de Poincaré e $\epsilon > 0$ é a escala de perturbação. O uso do mapa exponencial garante que $\tilde{x}$ permaneça no disco — ao contrário de uma perturbação euclidiana ingênua $x + \epsilon\xi$, que poderia violar a restrição $\|x\| < 1$.

O mapa exponencial no modelo de Poincaré, para um ponto $x$ e um vetor tangente $v \in T_x\mathbb{B}^d$, é:

$$\exp_x(v) = x \oplus_M \left( \tanh\left(\frac{\lambda_x \|v\|}{2}\right) \cdot \frac{v}{\|v\|} \right)$$

onde $\lambda_x = \frac{2}{1 - \|x\|^2}$ é o fator conforme e $\oplus_M$ é a adição de Möbius:

$$x \oplus_M y = \frac{(1 + 2\langle x, y \rangle + \|y\|^2)x + (1 - \|x\|^2)y}{1 + 2\langle x, y \rangle + \|x\|^2\|y\|^2}$$

A escala $\epsilon$ é adaptativamente controlada pela energia do nó. Nós com energia alta (ativos, frequentemente acessados) recebem perturbações menores — eles provavelmente já estão bem posicionados. Nós com energia baixa recebem perturbações maiores — pouco a perder, muito a ganhar:

$$\epsilon(n) = \epsilon_{\max} \cdot \left(1 - \frac{E(n)}{E_{\max}}\right)^2$$

Essa estratégia é análoga ao *simulated annealing* com temperatura adaptativa por nó.

---

## 10.3 Fase 2: Re-otimização Riemanniana — O Otimizador RiemannianAdam

> **Na Prática:** O RiemannianAdam é uma versão do otimizador Adam (amplamente usado em deep learning) adaptada para funcionar em espaços curvos como o disco de Poincaré. O Adam clássico assume que o espaço é "plano" (euclidiano), mas os embeddings do NietzscheDB vivem numa superfície hiperbólica — por isso é preciso converter gradientes e atualizações para respeitar essa curvatura. Sem esta adaptação, os embeddings poderiam sair do disco de Poincaré ou mover-se em direções geometricamente incorretas.

### 10.3.1 O Problema com Adam Euclidiano

O otimizador Adam clássico opera no espaço euclidiano $\mathbb{R}^d$. Suas equações de atualização são:

$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$

$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2$$

$$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t}$$

$$x_{t+1} = x_t - \alpha \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

onde $g_t = \nabla f(x_t)$ é o gradiente euclidiano, $\beta_1 = 0.9$, $\beta_2 = 0.999$, e $\alpha$ é a taxa de aprendizado.

O problema fundamental: a atualização $x_{t+1} = x_t - \alpha(\ldots)$ é uma operação *aditiva* no espaço euclidiano. No disco de Poincaré, adição euclidiana viola a geometria do espaço. O resultado pode sair do disco ($\|x_{t+1}\| \geq 1$), e mesmo quando permanece dentro, a direção de atualização não respeita a curvatura do espaço hiperbólico.

### 10.3.2 Gradiente Riemanniano

Para adaptar Adam ao disco de Poincaré, precisamos de três ingredientes: o gradiente riemanniano, o mapa exponencial, e o transporte paralelo.

O disco de Poincaré $(\mathbb{B}^d, g^P)$ possui métrica riemanniana:

$$g^P_x = \lambda_x^2 \cdot g^E = \left(\frac{2}{1 - \|x\|^2}\right)^2 \cdot I_d$$

onde $g^E = I_d$ é a métrica euclidiana. A relação entre o gradiente riemanniano $\text{grad}_x f$ e o gradiente euclidiano $\nabla_E f(x)$ é derivada diretamente da definição:

$$\langle \text{grad}_x f, v \rangle_{g^P} = Df(x)[v] = \langle \nabla_E f(x), v \rangle_{g^E}$$

Expandindo o lado esquerdo:

$$\lambda_x^2 \langle \text{grad}_x f, v \rangle_{g^E} = \langle \nabla_E f(x), v \rangle_{g^E}$$

Como isso vale para todo $v \in T_x\mathbb{B}^d$:

$$\text{grad}_x f = \frac{1}{\lambda_x^2} \nabla_E f(x) = \frac{(1 - \|x\|^2)^2}{4} \nabla_E f(x)$$

Esta é a fórmula central do RiemannianAdam: o gradiente riemanniano é o gradiente euclidiano reescalado pelo fator conforme ao quadrado. Próximo da origem ($\|x\| \approx 0$), o fator é $\approx 1/4$ — o gradiente riemanniano é menor que o euclidiano. Próximo da borda ($\|x\| \to 1$), o fator tende a zero — os passos de otimização ficam cada vez menores, refletindo a expansão exponencial do espaço hiperbólico perto do horizonte.

### 10.3.3 Atualização Completa do RiemannianAdam

A atualização completa do RiemannianAdam no NietzscheDB procede assim:

**Passo 1.** Calcular o gradiente riemanniano:

$$\tilde{g}_t = \frac{(1 - \|x_t\|^2)^2}{4} \nabla_E f(x_t)$$

**Passo 2.** Atualizar os momentos (no espaço tangente, euclidianamente):

$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) \tilde{g}_t$$

$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) \tilde{g}_t \odot \tilde{g}_t$$

onde $\odot$ denota o produto elemento a elemento (Hadamard).

**Passo 3.** Corrigir o viés:

$$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t}$$

**Passo 4.** Calcular a direção de atualização no espaço tangente:

$$u_t = -\alpha \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

**Passo 5.** Aplicar o mapa exponencial para atualizar o embedding no disco:

$$x_{t+1} = \exp_{x_t}(u_t)$$

**Passo 6.** Retração de segurança — se por erro numérico $\|x_{t+1}\| \geq 1$, projetar de volta:

$$x_{t+1} \leftarrow \frac{x_{t+1}}{\|x_{t+1}\|} \cdot (1 - \delta), \quad \delta = 10^{-5}$$

### 10.3.4 Transporte Paralelo dos Momentos

Um detalhe sutil mas crucial: os momentos $m_t$ e $v_t$ vivem no espaço tangente $T_{x_t}\mathbb{B}^d$. Após a atualização $x_t \to x_{t+1}$, eles precisam ser transportados para $T_{x_{t+1}}\mathbb{B}^d$ antes do próximo passo. O transporte paralelo no disco de Poincaré de $x$ para $y$ é:

$$\Gamma_{x \to y}(v) = v \cdot \frac{\lambda_x}{\lambda_y} = v \cdot \frac{1 - \|y\|^2}{1 - \|x\|^2}$$

Na implementação do `nietzsche-sleep`, aplicamos o transporte paralelo aos momentos após cada atualização:

$$m_t \leftarrow \Gamma_{x_t \to x_{t+1}}(m_t), \quad v_t \leftarrow \Gamma_{x_t \to x_{t+1}}(v_t)$$

Sem o transporte paralelo, os momentos acumulados seriam vetores em espaços tangentes incompatíveis — como somar velocidades medidas em referenciais diferentes sem transformação de coordenadas.

### 10.3.5 Convergência

A convergência do RiemannianAdam herda as garantias do Adam euclidiano sob condições adicionais de curvatura limitada. No disco de Poincaré com curvatura constante $K = -1$, a condição de Lipschitz geodésica é:

$$\|\text{grad}_x f - \Gamma_{y \to x}(\text{grad}_y f)\|_{x} \leq L \cdot d_{\mathbb{B}}(x, y)$$

onde $d_{\mathbb{B}}$ é a distância geodésica:

$$d_{\mathbb{B}}(x, y) = \text{arcosh}\left(1 + 2\frac{\|x - y\|^2}{(1 - \|x\|^2)(1 - \|y\|^2)}\right)$$

Sob esta condição e com taxa de aprendizado $\alpha_t = O(1/\sqrt{t})$, o RiemannianAdam converge com taxa $O(\log T / \sqrt{T})$ para funções geodesicamente convexas. Na prática, rodamos um número fixo de épocas (tipicamente 5-10) por ciclo de sono, priorizando eficiência sobre convergência completa.

---

## 10.4 Aprendizado Contrastivo Hiperbólico

A função de perda que o RiemannianAdam minimiza durante o ciclo de sono é uma perda contrastiva adaptada ao espaço hiperbólico. A intuição: nós conectados por arestas devem estar a uma distância-alvo no disco de Poincaré, e nós não conectados devem estar separados por pelo menos uma margem mínima.

### 10.4.1 Formulação da Perda

Seja $\mathcal{E}^+$ o conjunto de pares de nós conectados por arestas e $\mathcal{E}^-$ o conjunto de pares negativos (amostrados aleatoriamente entre nós sem aresta direta). A perda contrastiva é:

$$\mathcal{L} = \underbrace{\sum_{(i,j) \in \mathcal{E}^+} \left[ d_{\mathbb{B}}(x_i, x_j) - d_{\text{target}}(i,j) \right]^2}_{\text{atração}} + \underbrace{\sum_{(i,k) \in \mathcal{E}^-} \max\left(0, \; m - d_{\mathbb{B}}(x_i, x_k)\right)}_{\text{repulsão}}$$

onde:
- $d_{\text{target}}(i,j)$ é a distância-alvo entre nós $i$ e $j$, derivada do peso da aresta e da hierarquia
- $m$ é a margem de separação para pares negativos

A distância-alvo incorpora a hierarquia hiperbólica:

$$d_{\text{target}}(i,j) = \alpha_d \cdot \left|r_i - r_j\right| + \beta_d \cdot \frac{1}{w_{ij}}$$

onde $r_i = \text{artanh}(\|x_i\|)$ é a "profundidade" hiperbólica do nó $i$ (quanto mais próximo da borda, mais profundo na hierarquia), $w_{ij}$ é o peso da aresta, e $\alpha_d, \beta_d$ são hiperparâmetros.

### 10.4.2 Gradiente Euclidiano da Perda

Para aplicar o RiemannianAdam, precisamos do gradiente euclidiano $\nabla_{x_i} \mathcal{L}$, que será depois convertido para o gradiente riemanniano via o fator conforme.

Para o termo de atração, com $D_{ij} = d_{\mathbb{B}}(x_i, x_j)$:

$$\frac{\partial}{\partial x_i} D_{ij}^2 = 2 D_{ij} \cdot \frac{\partial D_{ij}}{\partial x_i}$$

O gradiente da distância hiperbólica em relação a $x_i$ é:

$$\frac{\partial D_{ij}}{\partial x_i} = \frac{4}{\beta\sqrt{\alpha^2 - 1}} \left( \frac{\alpha - 1}{(1 - \|x_i\|^2)^2} x_i - \frac{1}{(1 - \|x_i\|^2)(1 - \|x_j\|^2)} x_j \right)$$

onde:

$$\alpha = 1 + \frac{2\|x_i - x_j\|^2}{(1 - \|x_i\|^2)(1 - \|x_j\|^2)}, \quad \beta = 1$$

Para o termo de repulsão com margem:

$$\frac{\partial}{\partial x_i} \max(0, m - D_{ik}) = \begin{cases} -\frac{\partial D_{ik}}{\partial x_i} & \text{se } D_{ik} < m \\ 0 & \text{caso contrário} \end{cases}$$

O gradiente riemanniano final é então:

$$\text{grad}_{x_i} \mathcal{L} = \frac{(1 - \|x_i\|^2)^2}{4} \nabla_{x_i} \mathcal{L}$$

### 10.4.3 Amostragem de Negativos

Na prática, não computamos a perda sobre todos os pares negativos possíveis (seria $O(n^2)$). Usamos *negative sampling* com razão fixa: para cada aresta positiva, amostramos $k = 5$ pares negativos uniformemente. A distribuição de amostragem é ponderada pela popularidade inversa:

$$P(\text{nó } i \text{ como negativo}) \propto \frac{1}{\deg(i)^{0.75}}$$

Nós com grau alto (hubs) são amostrados menos frequentemente como negativos, pois é mais provável que tenham conexões reais com o nó âncora que simplesmente não foram observadas.

---

## 10.5 Fase 3: Rebalanceamento de Murray

> **Na Prática:** A Lei de Murray vem da biologia: descreve como os vasos sanguíneos se ramificam de forma ótima para distribuir fluxo com mínimo desperdício de energia. No NietzscheDB, esta lei é aplicada ao grafo de conhecimento — a "energia" (importância/vitalidade) dos nós deve fluir hierarquicamente de pais para filhos de forma equilibrada, como sangue numa árvore vascular. O rebalanceamento redistribui energia de regiões supersaturadas para regiões deficitárias, mantendo a hierarquia saudável.

Após a re-otimização contrastiva, o grafo pode estar semanticamente correto mas vasculamente desequilibrado. A analogia biológica aqui vem das leis de Murray sobre ramificação vascular ótima.

> **Nota:** A Lei de Murray será derivada formalmente no Capítulo 14, com todo o contexto histórico e biológico. Aqui apresentamos a versão aplicada ao rebalanceamento do grafo durante o sono.

### 10.5.1 A Lei de Murray para Grafos

A lei de Murray (1926) estabelece que, em uma bifurcação vascular ótima, o cubo do raio do vaso pai iguala a soma dos cubos dos raios dos vasos filhos:

$$r_{\text{pai}}^3 = \sum_{i \in \text{filhos}} r_i^3$$

No contexto do NietzscheDB, traduzimos "raio" como "capacidade de fluxo", que medimos pela energia do nó:

$$E(\text{pai})^{3/d_H} = \sum_{i \in \text{filhos}} E(i)^{3/d_H}$$

onde $d_H$ é a dimensão de Hausdorff local (seção 10.6). O expoente $3/d_H$ generaliza a lei de Murray para geometrias fractais — quando $d_H = 3$, recuperamos a lei clássica.

### 10.5.2 Algoritmo de Rebalanceamento

O rebalanceamento de Murray é executado bottom-up na hierarquia do grafo:

1. Identificar nós-folha (grau de saída zero na árvore de hierarquia)
2. Para cada nó pai, calcular a energia-alvo pela lei de Murray generalizada
3. Redistribuir energia: se $E_{\text{atual}} > E_{\text{alvo}}$, transferir excesso para filhos proporcionalmente; se $E_{\text{atual}} < E_{\text{alvo}}$, absorver dos filhos
4. Propagar bottom-up até a raiz

A conservação de energia é garantida: a soma total $\sum_i E(i)$ permanece constante durante o rebalanceamento. Apenas a distribuição muda, fluindo de regiões supersaturadas para regiões deficitárias.

---

## 10.6 Fase 4: Dimensão de Hausdorff como Métrica de Identidade

> **Na Prática:** A dimensão de Hausdorff é uma medida de "complexidade fractal" — ela diz quão densamente e irregularmente os pontos preenchem um espaço. No NietzscheDB, esta medida serve como "impressão digital" estrutural do grafo: se a re-otimização durante o sono mudar drasticamente a dimensão de Hausdorff, isso significa que a identidade do grafo foi danificada (como uma lesão cerebral), e o sistema reverte automaticamente ao estado anterior.

### 10.6.1 Definição e Intuição

A dimensão de Hausdorff mede a "complexidade fractal" de um conjunto. Para o grafo do NietzscheDB, ela captura quão densamente os nós preenchem o espaço hiperbólico — uma assinatura da *identidade estrutural* do grafo.

A definição formal usa a medida de Hausdorff $\mathcal{H}^s$:

$$d_H = \inf\{s \geq 0 : \mathcal{H}^s(X) = 0\} = \sup\{s \geq 0 : \mathcal{H}^s(X) = \infty\}$$

Na prática, para conjuntos discretos em espaços métricos, estimamos a dimensão de Hausdorff local por contagem de vizinhos:

$$d_H(x) = \lim_{r \to 0} \frac{\log N(x, r)}{\log(1/r)}$$

onde $N(x, r)$ é o número de pontos dentro de uma bola geodésica de raio $r$ centrada em $x$.

### 10.6.2 Estimativa Prática no NietzscheDB

No NietzscheDB, a estimativa discreta usa $k$-vizinhos mais próximos. Para um nó $x$ com $k$-ésimo vizinho mais próximo a distância $r_k$:

$$\hat{d}_H(x) = \frac{\log k}{\log r_k}$$

Esta é a estimativa de Grassberger-Procaccia adaptada para espaço hiperbólico. Os parâmetros configuráveis são:

- `LSYSTEM_HAUSDORFF_SAMPLE = 8000` — número de nós amostrados por tick
- `LSYSTEM_K = 12` — número de vizinhos para estimativa local

A dimensão de Hausdorff global é a média das estimativas locais:

$$\hat{d}_H^{\text{global}} = \frac{1}{|\mathcal{S}|} \sum_{x \in \mathcal{S}} \hat{d}_H(x)$$

onde $\mathcal{S}$ é o conjunto amostrado de 8000 nós.

### 10.6.3 Hausdorff como Guardião da Identidade

A dimensão de Hausdorff serve como guardião da identidade do grafo. Se a re-otimização contrastiva for agressiva demais — colapsando clusters, destruindo hierarquia — a dimensão de Hausdorff mudará drasticamente. Definimos um limiar de tolerância:

$$|\hat{d}_H^{\text{após}} - \hat{d}_H^{\text{antes}}| > \tau_H$$

onde $\tau_H$ é tipicamente 0.15. Se a mudança exceder o limiar, o ciclo de sono é abortado e os embeddings são revertidos ao checkpoint (Fase 5).

A intuição: a dimensão de Hausdorff de um cérebro humano não muda drasticamente durante uma noite de sono. Se mudasse, não seria reconsolidação — seria lesão. O mesmo princípio se aplica ao NietzscheDB.

### 10.6.4 Análise Multi-escala

Para robustez, computamos a dimensão de Hausdorff em múltiplas escalas de raio $r_1 < r_2 < \ldots < r_m$ e analisamos o espectro resultante:

$$\hat{d}_H(x, r_j) = \frac{\log N(x, r_j)}{\log(1/r_j)}$$

O gráfico $\hat{d}_H$ vs. $\log(1/r)$ revela comportamento multi-fractal: se a dimensão varia com a escala, o grafo possui estrutura hierárquica rica. Um grafo com $\hat{d}_H$ constante em todas as escalas é geometricamente "chato" — sem hierarquia verdadeira.

O NietzscheDB monitora a variância do espectro de Hausdorff:

$$\sigma^2_H = \frac{1}{m} \sum_{j=1}^m \left(\hat{d}_H(r_j) - \bar{d}_H\right)^2$$

Uma variância alta indica multi-fractalidade saudável — a hierarquia hiperbólica está funcionando. Variância próxima de zero é um sinal de alerta: o grafo colapsou para uma estrutura euclidiana plana, e a geometria hiperbólica não está contribuindo.

---

## 10.7 Fase 5: Checkpoint e Rollback

> **Na Prática:** Checkpoint e Rollback é o mecanismo de segurança do ciclo de sono. Antes de qualquer re-otimização, o sistema tira uma "fotografia" completa de todos os embeddings (checkpoint). Se a verificação de Hausdorff detectar que a re-otimização causou danos, o sistema restaura atomicamente essa fotografia (rollback), garantindo que nenhum ciclo de sono pode corromper irreversivelmente o grafo.

Antes de iniciar a re-otimização (entre as Fases 1 e 2), o ciclo de sono salva um checkpoint completo dos embeddings:

$$\mathcal{C}_t = \{(n_i, x_i, E_i) : i = 1, \ldots, N\}$$

onde $n_i$ é o identificador do nó, $x_i$ é seu embedding e $E_i$ é sua energia.

Após a Fase 4 (monitoramento de Hausdorff), se a verificação de identidade falhar ($|\Delta d_H| > \tau_H$), o sistema executa rollback:

$$\forall i: \; x_i \leftarrow x_i^{(\mathcal{C}_t)}, \quad E_i \leftarrow E_i^{(\mathcal{C}_t)}$$

O rollback é atômico — ou todos os embeddings são restaurados, ou nenhum. Na implementação Rust, isso é garantido pelo sistema de write-ahead log do NietzscheDB, que permite reverter uma transação batch de atualizações de embeddings.

O custo de armazenamento do checkpoint é $O(N \cdot d)$, onde $N$ é o número de nós e $d$ é a dimensão dos embeddings (128 no NietzscheDB). Para 865.000 nós com embeddings de 128 dimensões em float32, o checkpoint ocupa aproximadamente:

$$865{,}000 \times 128 \times 4 \text{ bytes} \approx 423 \text{ MB}$$

Na prática, o checkpoint é comprimido com LZ4 e armazenado em memória durante o ciclo de sono, sendo descartado após a verificação de Hausdorff ser aprovada.

---

## 10.8 Reconsolidação: A Analogia Biológica

### 10.8.1 Do Hipocampo ao Neocórtex

Na neurociência, a teoria da consolidação de memórias propõe que o hipocampo funciona como buffer temporário: durante a vigília, memórias novas são armazenadas rapidamente no hipocampo. Durante o sono (especialmente o sono de ondas lentas), o hipocampo "replay" essas memórias para o neocórtex, onde são integradas ao conhecimento de longo prazo.

No NietzscheDB, a analogia é direta:

| Biológico | NietzscheDB |
|---|---|
| Hipocampo | Nós recentes (energia alta, embeddings iniciais) |
| Neocórtex | Nós antigos (energia estabilizada, embeddings consolidados) |
| Sono SWS | Ciclo de sono do L-System |
| Replay | Re-otimização contrastiva |
| Consolidação | Convergência de embeddings para posição ótima |

### 10.8.2 Reconsolidação Seletiva

Nem todos os nós participam igualmente da reconsolidação. O ciclo de sono usa um critério de seleção baseado em energia e "estresse" do embedding — a discrepância entre a posição atual e a posição ótima local:

$$\text{stress}(i) = \sum_{j \in \mathcal{N}(i)} \left| d_{\mathbb{B}}(x_i, x_j) - d_{\text{target}}(i,j) \right|$$

Nós com estresse alto são priorizados na re-otimização. Nós com estresse baixo — que já estão bem posicionados — são perturbados minimamente ou pulados inteiramente, preservando suas posições consolidadas.

---

## 10.9 Prevenção de Esquecimento Catastrófico

### 10.9.1 O Problema

O esquecimento catastrófico ocorre quando um sistema de aprendizado, ao aprender informação nova, destrói informação previamente aprendida. Em redes neurais, isso se manifesta quando o treinamento em uma tarefa nova apaga os pesos otimizados para tarefas anteriores. No NietzscheDB, o risco é que a re-otimização contrastiva — ao ajustar embeddings para refletir arestas recentes — destrua posicionamentos que codificavam relações antigas.

### 10.9.2 Mecanismos de Proteção

O NietzscheDB emprega três mecanismos contra o esquecimento catastrófico:

**Decaimento de energia com proteção de elite.** Durante o sono, nós com energia abaixo de um limiar decaem:

$$E_i^{(t+1)} = \begin{cases} E_i^{(t)} \cdot \gamma & \text{se } E_i^{(t)} < E_{\text{elite}} \\ E_i^{(t)} & \text{se } E_i^{(t)} \geq E_{\text{elite}} \end{cases}$$

onde $\gamma \in (0,1)$ é a taxa de decaimento (tipicamente 0.98) e $E_{\text{elite}}$ é o limiar de elite. Nós "Übermensch" — que foram promovidos pelo L-System por sua centralidade e utilidade persistente — resistem ao decaimento. O conhecimento fundamental persiste; o ruído informacional evapora.

**Regularização elástica dos embeddings (EWC adaptada).** Inspirada em Elastic Weight Consolidation (Kirkpatrick et al., 2017), a perda contrastiva inclui um termo de regularização que penaliza desvios dos embeddings consolidados:

$$\mathcal{L}_{\text{EWC}} = \mathcal{L}_{\text{contrastiva}} + \frac{\lambda}{2} \sum_{i} F_i \cdot d_{\mathbb{B}}(x_i, x_i^*)^2$$

onde $x_i^*$ é a posição consolidada anterior do nó $i$ e $F_i$ é a "importância" do nó (análoga à diagonal da matriz de informação de Fisher). Nós importantes são ancorados mais fortemente; nós periféricos têm mais liberdade para se mover.

A importância $F_i$ é estimada pela centralidade de PageRank do nó:

$$F_i = \text{PageRank}(i)^{1/2}$$

A raiz quadrada suaviza a distribuição, evitando que hubs dominem completamente a regularização.

**Limiar de Hausdorff (seção 10.6.3).** Como discutido, a dimensão de Hausdorff funciona como última linha de defesa: se a reconsolidação destruir a estrutura fractal do grafo, o rollback é acionado e toda a fase de sono é anulada.

### 10.9.3 Dinâmica de Longo Prazo

A combinação desses três mecanismos produz uma dinâmica de longo prazo elegante:

1. Nós novos entram com energia alta e embeddings ruidosos
2. Ciclos de sono progressivamente refinam seus embeddings via aprendizado contrastivo
3. Nós frequentemente acessados mantêm energia alta e posições estáveis
4. Nós raramente acessados decaem gradualmente, liberando "espaço" no disco de Poincaré
5. A dimensão de Hausdorff oscila dentro de uma faixa saudável, nunca mudando abruptamente

O resultado é um sistema que aprende continuamente sem esquecer — não porque nunca esquece, mas porque esquece *seletivamente*, preservando o essencial e deixando o efêmero dissipar-se na periferia do disco hiperbólico.

---

## 10.10 Análise de Complexidade e Performance

### 10.10.1 Custo Computacional por Fase

| Fase | Complexidade | Tempo típico (865K nós) |
|---|---|---|
| Perturbação | $O(N \cdot d)$ | ~200 ms |
| RiemannianAdam (1 época) | $O(|\mathcal{E}| \cdot d + k \cdot |\mathcal{E}| \cdot d)$ | ~8 s |
| Murray Rebalancing | $O(N \cdot \log N)$ | ~1.5 s |
| Hausdorff | $O(S \cdot k \cdot \log N)$ | ~3 s |
| Checkpoint (save/restore) | $O(N \cdot d)$ | ~500 ms |

onde $S = 8000$ é o tamanho da amostra de Hausdorff, $k = 12$ é o número de vizinhos, e $|\mathcal{E}|$ é o número de arestas.

### 10.10.2 Frequência Ótima de Sono

Ciclos de sono muito frequentes desperdiçam computação em re-otimizações desnecessárias. Ciclos muito raros permitem acúmulo excessivo de distorção. A frequência ótima depende da taxa de inserção de novos nós e arestas.

Empiricamente, o NietzscheDB usa uma heurística adaptativa: o ciclo de sono é disparado quando o "estresse acumulado" do grafo excede um limiar:

$$\sum_{i} \text{stress}(i) > \tau_{\text{sleep}} \cdot N$$

onde $\tau_{\text{sleep}}$ é calibrado para disparar aproximadamente a cada 40 ticks do L-System em condições normais de carga.

---

## 10.11 Considerações Finais

O ciclo de sono do NietzscheDB é mais do que uma otimização periódica — é o mecanismo pelo qual o grafo mantém sua *coerência ontológica*. Sem ele, os embeddings derivariam lentamente para o caos: nós em posições arbitrárias, hierarquia corrompida, distâncias sem significado semântico.

A combinação de cinco fases — perturbação, re-otimização riemanniana, rebalanceamento vascular, monitoramento fractal e checkpoint seguro — cria um ciclo que é simultaneamente agressivo o suficiente para corrigir distorções e conservador o suficiente para preservar identidade. O RiemannianAdam garante que a otimização respeita a geometria hiperbólica. O Hausdorff garante que a identidade fractal sobrevive. O checkpoint garante que erros são reversíveis.

O sono biológico permanece, até hoje, incompletamente compreendido pela neurociência. Não sabemos por que dormimos — sabemos apenas que sem sono, morremos. O NietzscheDB adota essa humildade epistemológica: o ciclo de sono funciona não porque entendemos completamente por que ele é necessário, mas porque sem ele, o grafo colapsa.

E nesse colapso, Nietzsche talvez reconhecesse algo familiar: o eterno retorno de um sistema que se recusa a dormir é não a imortalidade, mas a insanidade.

---

**Variáveis de ambiente do ciclo de sono:**

| Variável | Default | Descrição |
|---|---|---|
| `LSYSTEM_SLEEP_ENABLED` | `true` | Habilita/desabilita o ciclo de sono |
| `LSYSTEM_SLEEP_INTERVAL` | `40` | Ticks entre ciclos de sono |
| `LSYSTEM_SLEEP_LR` | `0.01` | Taxa de aprendizado do RiemannianAdam |
| `LSYSTEM_SLEEP_EPOCHS` | `5` | Épocas de re-otimização por ciclo |
| `LSYSTEM_SLEEP_PERTURB` | `0.05` | Escala máxima de perturbação ($\epsilon_{\max}$) |
| `LSYSTEM_HAUSDORFF_SAMPLE` | `8000` | Nós amostrados para Hausdorff |
| `LSYSTEM_K` | `12` | Vizinhos para Hausdorff local |
| `LSYSTEM_HAUSDORFF_THRESHOLD` | `0.15` | Limiar de mudança para rollback ($\tau_H$) |
| `LSYSTEM_SLEEP_BETA1` | `0.9` | $\beta_1$ do RiemannianAdam |
| `LSYSTEM_SLEEP_BETA2` | `0.999` | $\beta_2$ do RiemannianAdam |
| `LSYSTEM_SLEEP_DECAY` | `0.98` | Taxa de decaimento de energia ($\gamma$) |
| `LSYSTEM_SLEEP_MARGIN` | `2.0` | Margem contrastiva ($m$) |
| `LSYSTEM_SLEEP_NEG_RATIO` | `5` | Razão de negative sampling |
| `LSYSTEM_SLEEP_EWC_LAMBDA` | `0.1` | Peso da regularização EWC ($\lambda$) |
