# Como o LLM Gera Personas no FUTUR.IA

Este documento explica o pipeline de geração de personas de Agentes no FUTUR.IA — do grafo de conhecimento Zep até o formato consumido pelo motor de simulação OASIS. O foco está na arquitetura, nas decisões de design e nos trade-offs envolvidos na transformação de entidades estáticas em agentes comportamentais realistas.

---

## 1. O Problema: De Entidades do Grafo a Agentes de Simulação

### 1.1. O que é uma Entidade Zep

No FUTUR.IA, o grafo de conhecimento é construído sobre a plataforma Zep. Cada **entidade** é um nó tipado que representa algo extraído dos documentos-fonte do usuário. Uma entidade Zep carrega:

- **`name`**: o nome canônico (ex.: "Greenpeace", "Maria Silva").
- **`entity_type`**: uma etiqueta tipada (ex.: `Organization`, `Person`, `MediaOutlet`).
- **`summary`**: um parágrafo textual sintetizado pelo LLM durante a ingestão do documento.
- **`attributes`**: pares chave-valor opcionais (ex.: `{"foundation_year": 1971}`).
- **`related_edges`**: arestas diretas que ligam esta entidade a outras (ex.: `Greenpeace --[OPPOSES]--> OilCompany`).
- **`related_nodes`**: nós vizinhos com seus próprios sumários e tipos.

Essa estrutura é excelente para raciocínio simbólico e busca semântica, mas é fundamentalmente **estática**. Ela descreve *quem* é a entidade, não *como* ela se comporta em uma rede social.

### 1.2. O Gap Semântico

A simulação OASIS exige agentes que publiquem, comentem, reajam e interajam em plataformas digitais. Para isso, cada agente precisa de uma **persona** — uma descrição rica de personalidade, histórico, estilo de comunicação e posicionamento ideológico.

O gap entre os dois mundos é grande:

| Dado Zep (estático) | Persona OASIS (comportamental) |
|---|---|
| `summary`: "ONG ambientalista" | `persona`: "Ativista veterano que adota tom urgente, menciona dados científicos e responde a críticas com sarcasmo intelectual" |
| `attributes`: `{"country": "Brasil"}` | `active_hours`: [9, 10, 11, 12, 13, 18, 19, 20, 21, 22] |
| `related_edges`: fatos sobre campanhas | `interested_topics`: ["Mudanças Climáticas", "Direitos Indígenas", "Política Energética"] |

Sem preencher esse gap, a simulação produziria agentes genéricos e previsíveis, incapazes de gerar dinâmica de grupo realista.

### 1.3. Por que Regras Determinísticas Falham

Uma abordagem inicial poderia ser usar templates estáticos: "Se o tipo é `Organization`, use bio X e persona Y". Isso funciona para protótipos, mas colapsa em cenários reais por três razões:

1. **Falta de variação contextual**: uma `University` em uma simulação sobre reforma educacional deve ter persona diferente da mesma `University` em uma simulação sobre violência no campus.
2. **Densidade informacional desperdiçada**: o grafo Zep contém dezenas de fatos e relações sobre cada entidade. Templates ignoram esse contexto.
3. **Comportamento robótico**: agentes com personas idênticas dentro de um mesmo tipo não geram atrito, alianças ou mudanças de opinião — ingredientes essenciais para uma simulação de opinião pública.

A solução adotada foi usar um LLM para **sintetizar** a persona a partir do contexto rico do grafo, respeitando o tema da simulação e o tipo da entidade.

---

## 2. Visão Arquitetural do Pipeline

### 2.1. Diagrama Conceitual End-to-End

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Zep GraphRAG  │────▶│  ZepEntityReader     │────▶│ OasisProfile    │
│   (entidades)   │     │  (filtragem + fetch) │     │ Generator       │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                              │
                                   ┌──────────────────────────┼──────────────────────────┐
                                   │                          │                          │
                                   ▼                          ▼                          ▼
                         ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
                         │ Context Builder │        │ LLM Client      │        │ Profile         │
                         │ (_build_entity_  │        │ (OpenAI API     │        │ Validator &     │
                         │  context)         │        │  com retry)     │        │ Serializer      │
                         └─────────────────┘        └─────────────────┘        └─────────────────┘
                                   │                          │                          │
                                   │                          │                          ▼
                                   │                          │                   ┌─────────────────┐
                                   │                          │                   │  OASIS Sandbox  │
                                   │                          │                   │  (reddit.json / │
                                   │                          │                   │   twitter.csv)  │
                                   │                          │                   └─────────────────┘
                                   │                          │
                                   └──────────────────────────┘
                                              (rich prompt)
```

### 2.2. O Papel do `OasisProfileGenerator`

A classe `OasisProfileGenerator` é o orquestrador central. Suas responsabilidades são:

1. **Enriquecimento**: coletar e estruturar o máximo de contexto possível sobre cada entidade.
2. **Geração**: invocar o LLM com prompts otimizados por tipo de entidade.
3. **Resiliência**: reparar ou substituir saídas corrompidas do LLM.
4. **Normalização**: converter campos para os formatos exigidos pelo OASIS.
5. **Serialização**: persistir os profiles em JSON (Reddit) ou CSV (Twitter).

A decisão de concentrar toda a lógica em uma única classe, em vez de distribuí-la por microserviços, foi deliberada: o pipeline é síncrono em relação à preparação da simulação, e a latência dominante é a chamada ao LLM. Adicionar camadas de rede não melhoraria a performance e complicaria o retry e o fallback.

### 2.3. Separação de Responsabilidades

Dentro do gerador, as funções são segregadas por estágio:

| Função | Responsabilidade |
|---|---|
| `_build_entity_context()` | Engenharia de contexto: o que entra no prompt |
| `_search_zep_for_entity()` | Busca híbrida no grafo para enriquecer o contexto |
| `_generate_profile_with_llm()` | Interação com o modelo: construção de mensagens, parsing de resposta |
| `_generate_profile_rule_based()` | Fallback determinístico quando o LLM falha |
| `_normalize_gender()` | Adaptação de campos para o schema do OASIS |
| `_save_reddit_json()` / `_save_twitter_csv()` | Serialização de acordo com a plataforma alvo |

Essa separação permite testar cada estágio isoladamente e substituir a implementação de um sem afetar os outros.

---

## 3. Enriquecimento de Contexto: Construindo a Janela de Contexto

### 3.1. As Quatro Camadas de Contexto

O prompt enviado ao LLM não contém apenas o nome e o tipo da entidade. Ele é construído em quatro camadas progressivas de riqueza:

#### Camada 1 — Atributos da Entidade
Os pares chave-valor do nó Zep são listados como uma seção de "Atributos da Entidade". Atributos vazios ou nulos são filtrados para não poluir a janela de contexto.

#### Camada 2 — Fatos e Relacionamentos
As `related_edges` da entidade são convertidas em bullets de fatos. Se uma aresta tem um campo `fact` (texto descritivo da relação), ele é usado diretamente. Caso contrário, é inferido a partir do `edge_name` e da direção (`incoming`/`outgoing`).

#### Camada 3 — Entidades Relacionadas
Os nós vizinhos (`related_nodes`) são listados com nome, tipo customizado (excluindo labels genéricas como `Entity` e `Node`) e sumário. Isso dá ao LLM uma noção do *ecossistema* em que a entidade está inserida.

#### Camada 4 — Busca Híbrida Zep
Além das conexões diretas, o gerador executa uma busca semântica no grafo Zep usando o nome da entidade como query. A busca é dividida em dois escopos:

- **`scope="edges"`**: retorna fatos que mencionam ou envolvem a entidade, mesmo que não sejam arestas diretamente conectadas ao nó.
- **`scope="nodes"`**: retorna outros nós semanticamente próximos.

As duas buscas rodam em paralelo via `ThreadPoolExecutor(max_workers=2)` com timeout de 30 segundos. Os resultados são deduplicados contra os fatos já coletados na Camada 2 para evitar repetição.

### 3.2. Busca Híbrida em Detalhe

A busca híbrida é um ponto crítico de design. O Zep não possui uma API nativa de busca híbrida unificada, então o sistema simula essa capacidade:

```python
# Pseudocódigo do fluxo real
def search_edges():
    return zep_client.graph.search(
        query=f"Tudo sobre {entity_name}",
        scope="edges",
        reranker="rrf",
        limit=30
    )

def search_nodes():
    return zep_client.graph.search(
        query=f"Tudo sobre {entity_name}",
        scope="nodes",
        reranker="rrf",
        limit=20
    )

# Execução paralela
with ThreadPoolExecutor(max_workers=2) as executor:
    edges_future = executor.submit(search_edges)
    nodes_future = executor.submit(search_nodes)
```

O **reranker RRF** (Reciprocal Rank Fusion) combina resultados de múltiplas estratégias de ranking, melhorando a relevância sem depender de um único sinal de similaridade.

### 3.3. Truncamento e Gestão de Janela

O contexto final é truncado em **3000 caracteres** antes de ser injetado no prompt. Esse limite foi escolhido por experimentação empírica:

- **Acima de 3000**: o LLM tende a perder o foco na estrutura JSON e a omitir campos obrigatórios.
- **Abaixo de 3000**: informações valiosas do grafo são descartadas, reduzindo a especificidade da persona.

O truncamento é feito por corte simples (`context[:3000]`). Não há resumo adaptativo — isso seria uma melhoria futura, mas adicionaria uma chamada LLM extra por entidade, dobrando o custo.

**Trade-off**: sacrificamos a profundidade máxima de contexto em favor da confiabilidade estrutural da resposta.

---

## 4. O Prompt Engineering por Tipo de Entidade

### 4.1. Distinção Individual vs. Grupo/Instituição

O sistema classifica entidades em dois buckets:

```python
INDIVIDUAL_ENTITY_TYPES = [
    "student", "alumni", "professor", "person", "publicfigure",
    "expert", "faculty", "official", "journalist", "activist"
]

GROUP_ENTITY_TYPES = [
    "university", "governmentagency", "organization", "ngo",
    "mediaoutlet", "company", "institution", "group", "community"
]
```

Essa distinção não é meramente taxonômica — ela determina **qual prompt** o LLM recebe:

- **Individuais** recebem um prompt que pede: idade, gênero, histórico pessoal, traços de personalidade, memórias individuais sobre o evento.
- **Grupos/Instituições** recebem um prompt que pede: posicionamento oficial, estilo de comunicação institucional, horários de atividade corporativa, memórias institucionais.

Um `Student` e uma `University` podem estar no mesmo ecossistema temático, mas suas personas devem ser arquiteturalmente diferentes: o primeiro é um agente emocional e pessoal; o segundo, um agente institucional com restrições de tom e horário.

### 4.2. Estrutura do System Prompt

O system prompt tem três partes:

1. **Identidade do modelo**: "Você é um especialista em geração de personas para mídias sociais..."
2. **Regras técnicas**: JSON válido, sem quebras de linha não escapadas, campos obrigatórios.
3. **Enforcement de idioma**: via `get_language_instruction()`.

A função `get_language_instruction()` merece atenção especial. Ela não apenas pede português brasileiro — ela impõe uma regra absoluta:

> "Você está rigorosamente programado para produzir output EXCLUSIVAMENTE em português brasileiro. ZERO tolerância para caracteres em chinês, japonês, coreano, russo..."

Esse enforcement foi adicionado após observar que modelos baseados em instruções multilíngues, quando expostos a contexto predominantemente em inglês ou chinês, tendem a "vazar" para esses idiomas. A instrução agressiva funciona como um guard-rail psicolinguístico.

### 4.3. O User Prompt Estruturado

O user prompt é dividido em três seções:

1. **Metadados da entidade**: nome, tipo, resumo, atributos.
2. **Contexto enriquecido**: as quatro camadas descritas na Seção 3.
3. **Especificação de saída**: schema JSON detalhado, com descrição de cada campo e restrições.

O campo mais importante é `persona` — um texto corrido de até 2000 caracteres que descreve:

- Informações básicas (idade, profissão, localidade)
- Histórico pessoal/institucional
- Traços de personalidade (MBTI, tom emocional)
- Comportamento em redes sociais
- Posicionamento e opiniões
- Características únicas (bordões, hobbies)
- **Memórias**: como esta entidade já interagiu com o evento central da simulação

As memórias são cruciais: elas ancoram o agente no passado do cenário simulado, evitando que ele se comporte como se o evento tivesse começado no turno 1.

### 4.4. Controle de Formato via `response_format`

O sistema usa a API `chat.completions.create` da OpenAI com o parâmetro:

```python
response_format={"type": "json_object"}
```

Isso instrui o modelo a validar a saída como JSON antes de retorná-la, reduzindo drasticamente a taxa de respostas malformadas. No entanto, não é uma garantia absoluta: o modelo ainda pode:

- Truncar o JSON se o `max_tokens` for atingido (não definimos `max_tokens` para evitar isso, mas provedores alternativos podem impor limites).
- Omitir campos obrigatórios.
- Inserir quebras de linha não escapadas dentro de strings.

Por isso, o pipeline inclui camadas de reparo (Seção 6).

---

## 5. Geração em Lotes e Paralelismo

### 5.1. Por que Não Geramos Tudo de Uma Vez

Duas razões técnicas impedem a geração de todas as personas em uma única chamada LLM:

1. **Context Window**: 165 entidades excederiam a janela de contexto da maioria dos modelos, forçando truncamento massivo de informações.
2. **Custo de falha**: se uma única chamada falhasse (timeout, JSON inválido, rate limit), todo o lote de 165 personas seria perdido. Com geração individual, apenas uma entidade é afetada.

### 5.2. Modelo de Concorrência

A geração usa `ThreadPoolExecutor` com `max_workers=5` por padrão:

```python
with ThreadPoolExecutor(max_workers=parallel_count) as executor:
    futures = {
        executor.submit(generate_single_profile, idx, entity): (idx, entity)
        for idx, entity in enumerate(entities)
    }
```

**Por que threads e não processos?**

O gargalo é I/O (chamadas de rede para a API do LLM), não CPU. Threads são mais leves e compartilham o estado do gerador sem necessidade de serialização. O único estado mutável compartilhado é o contador de progresso (`completed_count`), protegido por `threading.Lock`.

**Isolamento de locale:**

Cada worker seta seu próprio locale antes de processar:

```python
def generate_single_profile(idx, entity):
    set_locale(current_locale)  # herda do thread pai
    # ... resto da lógica
```

Isso é necessário porque o Flask armazena o locale no `request` (thread-local), e workers do pool não têm acesso ao contexto da requisição original. Esquecer de chamar `set_locale()` resultaria em mensagens de log em inglês ou chinês, dependendo do default do sistema.

### 5.3. Persistência em Tempo Real

A cada profile concluído, o sistema escreve o arquivo de saída (JSON ou CSV) em disco:

```python
def save_profiles_realtime():
    with lock:
        existing = [p for p in profiles if p is not None]
        # escreve no disco
```

**Motivação**: se o processo de preparação for interrompido (crash, kill, timeout), os profiles já gerados não são perdidos. Na retomada, o sistema pode reutilizar o arquivo parcial em vez de recomeçar do zero.

---

## 6. Resiliência: Quando o LLM Falha

### 6.1. Estratégia de Retry com Degradação Controlada

Cada entidade tem até **3 tentativas** de geração:

```python
for attempt in range(max_attempts):
    response = client.chat.completions.create(
        ...,
        temperature=0.7 - (attempt * 0.1)  # 0.7 → 0.6 → 0.5
    )
```

A temperatura decresce a cada retry. A lógica é:

- **Tentativa 1 (0.7)**: máxima criatividade. Ideal para personas ricas e variadas.
- **Tentativa 2 (0.6)**: levemente mais conservador. Se o JSON falhou por estrutura malformada, menor temperação aumenta a aderência ao schema.
- **Tentativa 3 (0.5)**: quase determinístico. Última chance de obter um JSON válido.

### 6.2. Reparo de JSON Truncado

Se o modelo retornar `finish_reason == 'length'`, o JSON pode estar truncado. O sistema aplica dois níveis de reparo:

**Nível 1 — Fechamento de estrutura (`_fix_truncated_json`)**:

Conta parênteses e colchetes abertos vs. fechados. Adiciona o fechamento necessário:

```python
open_braces = content.count('{') - content.count('}')
content += '}' * open_braces
```

Se o último caractere não for um terminador JSON (`"`, `,`, `]`, `}`), assume que uma string foi cortada e adiciona aspas de fechamento.

**Nível 2 — Sanitização agressiva (`_try_fix_json`)**:

- Extrai o maior bloco `{...}` por regex.
- Substitui quebras de linha dentro de strings JSON por espaços.
- Remove caracteres de controle (`\x00-\x1f`).
- Tenta fazer parse; se falhar, tenta novamente com whitespace normalizado.

### 6.3. Extração Parcial de Informações

Se o JSON estiver irremediavelmente corrompido, o sistema tenta extrair pelo menos os campos críticos via regex:

```python
bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)
```

Se conseguir extrair `bio` ou `persona`, cria um profile mínimo e marca como `_fixed`. Se nem isso for possível, cai no fallback determinístico.

### 6.4. Detecção de Contaminação de Idioma

Mesmo com instruções fortes de idioma, alguns modelos (especialmente variantes menores ou quantizadas) ocasionalmente respondem com caracteres CJK. O sistema detecta isso no campo `reasoning`:

```python
def _normalize_reasoning_text(self, reasoning, fallback):
    if re.search(r'[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]', reasoning):
        return fallback
    return reasoning
```

Se o reasoning contiver qualquer caractere chinês, japonês ou coreano, é substituído por um texto padrão em português: *"Configuração ajustada ao público e ao ritmo esperado da discussão."*

---

## 7. Integração com o OASIS

### 7.1. Normalização de Campos

O OASIS espera valores específicos para certos campos. O mais crítico é `gender`:

```python
def _normalize_gender(self, gender: Optional[str]) -> str:
    gender_map = {
        "masculino": "male",
        "feminino": "female",
        "outro": "other",
        "male": "male",
        "female": "female",
        "other": "other",
        # Fallbacks defensivos contra alucinação do LLM
        "男": "male",
        "女": "female",
        "机构": "other",
        "其他": "other",
    }
    return gender_map.get(gender_lower, "other")
```

A inclusão de mapeamentos chineses (`男`, `女`) pode parecer estranha em um sistema PT-BR, mas é uma **defesa defensiva**: se o LLM alucinar e responder `gender: "男"`, a simulação não quebra — o valor é normalizado silenciosamente para `"male"`.

### 7.2. Dupla Saída: Reddit vs. Twitter

O OASIS suporta duas plataformas com schemas diferentes:

**Reddit (JSON)**:
```json
{
  "user_id": 0,
  "username": "greenpeace_123",
  "name": "Greenpeace",
  "bio": "Conta oficial...",
  "persona": "Ativista veterano...",
  "age": 30,
  "gender": "other",
  "mbti": "ISTJ",
  "country": "Brasil"
}
```

**Twitter (CSV)**:
```csv
user_id,name,username,user_char,description
0,Greenpeace,greenpeace_123,Conta oficial... Ativista veterano...,Conta oficial...
```

A diferença crucial é `user_char` vs. `description`:

- **`user_char`**: a persona completa (`bio + persona`), usada internamente pelo OASIS como parte do system prompt do agente. Determina *como* o agente pensa e fala.
- **`description`**: apenas a `bio`, visível publicamente no perfil do agente. Determina *o que* outros agentes veem sobre ele.

### 7.3. O Campo `user_id` como Chave de Matching

O OASIS vincula posts iniciais a agentes através do campo `poster_agent_id`. Esse valor **deve corresponder exatamente** ao `user_id` do profile. Se houver divergência — por exemplo, se o `user_id` for omitido ou duplicado — o post inicial ficará órfão ou será atribuído ao agente errado.

O gerador garante isso mantendo o `user_id` como índice ordinal da lista de entidades:

```python
"user_id": profile.user_id if profile.user_id is not None else idx
```

---

## 8. Decisões de Arquitetura e Trade-offs

### 8.1. Por que Não Usamos Few-Shot Prompting

Few-shot prompting (incluir 2-3 exemplos de personas no prompt) melhoraria a qualidade da saída, mas foi deliberadamente evitado por três razões:

1. **Custo**: com 165 entidades, cada exemplo adiciona ~500 tokens ao prompt. Few-shot triplicaria o custo de inferência.
2. **Manutenção**: exemplos ficam obsoletos quando o schema evolui. A equipe teria que manter uma biblioteca de exemplos atualizada.
3. **Generalidade**: exemplos bons para `Student` podem prejudicar `MediaOutlet`. Teríamos que manter exemplos por tipo, aumentando ainda mais a complexidade.

A escolha foi usar **prompts descritivos extensos** com especificação rigorosa de schema, que são mais baratos e mais fáceis de versionar.

### 8.2. Custo vs. Qualidade: Uma Chamada por Entidade

O pipeline faz **uma chamada LLM por entidade**. Para uma simulação média de 100-165 entidades, isso representa ~165 chamadas. A alternativa seria gerar em lote (ex.: 15 entidades por chamada), reduzindo o custo em ~80%.

**Por que mantemos 1:1?**

| Dimensão | 1 chamada/entidade | Lote (15/vez) |
|---|---|---|
| Custo | Alto | Baixo |
| Latência total | Similar (paralelismo) | Similar |
| Granularidade de retry | Entidade individual | Lote inteiro |
| Debuggabilidade | Fácil: log por entidade | Difícil: identificar qual falhou |
| Qualidade de contexto | Máximo: janela inteira dedicada | Reduzido: contexto dividido |

Para o FUTUR.IA, a prioridade é **confiabilidade e debuggabilidade**, não custo mínimo. Se o custo se tornar um gargalo no futuro, o loteamento pode ser introduzido como otimização, não como default.

### 8.3. O Locale como Estado Global por Thread

O gerenciamento de idioma no Flask é baseado no header `Accept-Language` da requisição HTTP. No entanto, os workers do `ThreadPoolExecutor` não herdam o contexto da requisição original.

A solução foi capturar o locale **antes** de iniciar o pool e propagá-lo manualmente:

```python
current_locale = get_locale()  # lê do request ou do thread-local

def worker():
    set_locale(current_locale)  # define no thread-local do worker
```

**Risco**: se um desenvolvedor esquecer de chamar `set_locale()` em um novo worker, todas as mensagens de log daquele worker cairão para o default do sistema (geralmente inglês). Isso já aconteceu em ambientes de teste e foi a razão pela qual o `set_locale()` foi adicionado explicitamente no closure do worker.

### 8.4. Manutenção do Mapeamento Chinês em `_normalize_gender`

Como observado na Seção 7.1, mantemos mapeamentos de caracteres chineses para gênero mesmo após traduzir todo o sistema para PT-BR. Isso não é um resquício — é uma **camada de defesa**.

LLMs, especialmente modelos open-source ou quantizados, ocasionalmente "vazam" para o chinês em campos curtos como gênero, mesmo quando o resto da resposta está em português. Em vez de deixar a simulação quebrar com `gender: "男"`, o sistema normaliza silenciosamente. O overhead é zero (lookup em dict), e o benefício de robustez é significativo.

---

## 9. Fluxo de Dados Ilustrado

### 9.1. Exemplo Completo: De Entidade a Profile

**Entrada no Zep:**
```python
EntityNode(
    name="Greenpeace",
    entity_type="Organization",
    summary="ONG ambientalista internacional...",
    attributes={"founded": 1971, "hq": "Amsterdam"},
    related_edges=[
        {"fact": "Greenpeace campanhou contra exploração de petróleo no Ártico"},
        {"fact": "Greenpeace tem presença ativa no Brasil desde 1994"}
    ],
    related_nodes=[
        {"name": "Petróleo", "summary": "Recurso natural...", "labels": ["Resource"]},
        {"name": "Mudanças Climáticas", "summary": "Aquecimento global...", "labels": ["Topic"]}
    ]
)
```

**Passo 1 — Context Builder:**
As quatro camadas são montadas em um texto de ~2500 caracteres:

```markdown
### Atributos da Entidade
- founded: 1971
- hq: Amsterdam

### Fatos e Relacionamentos Relacionados
- Greenpeace campanhou contra exploração de petróleo no Ártico
- Greenpeace tem presença ativa no Brasil desde 1994

### Informações de Entidades Relacionadas
- **Petróleo** (Resource): Recurso natural...
- **Mudanças Climáticas** (Topic): Aquecimento global...

### Informações Factuais Encontradas pela Busca Zep
- Greenpeace bloqueou navios-tanque em protestos...
```

**Passo 2 — LLM Prompt:**
O prompt (em português) instrui o LLM a gerar um JSON com bio, persona detalhada (2000 chars), age=30, gender="other", MBTI="ISTJ", etc.

**Passo 3 — Profile Gerado:**
```json
{
  "bio": "ONG ambientalista internacional com atuação no Brasil desde 1994.",
  "persona": "A conta do Greenpeace adota tom institucional mas engajado...",
  "age": 30,
  "gender": "other",
  "mbti": "ISTJ",
  "country": "Brasil",
  "profession": "ONG Ambientalista",
  "interested_topics": ["Mudanças Climáticas", "Petróleo", "Direitos Indígenas"]
}
```

**Passo 4 — Normalização e Serialização:**
- Gender normalizado para `"other"` (já estava correto).
- Convertido para formato Reddit JSON com `user_id: 42`.
- Salvo em `reddit_profiles.json`.

---

## 10. Extensões e Pontos de Customização

### 10.1. Como Adicionar Novos Tipos de Entidade

Para introduzir um novo tipo (ex.: `Influencer`):

1. Adicione `"influencer"` a `INDIVIDUAL_ENTITY_TYPES` ou `GROUP_ENTITY_TYPES`.
2. Adicione um caso no `_generate_profile_rule_based()` para definir fallback quando o LLM falha.
3. Opcional: ajuste o prompt para mencionar características específicas de `Influencer` (ex.: alta frequência de posts, tom informal, alta base de seguidores).

O roteamento de prompt (`_is_individual_entity` / `_is_group_entity`) se encarrega do resto automaticamente.

### 10.2. Ajuste de Temperatura e Modelo

O modelo e a temperatura são controlados via variáveis de ambiente:

```python
model = Config.LLM_MODEL_NAME       # ex.: "gpt-4o", "claude-3-sonnet"
temperature = 0.7 - (attempt * 0.1) # decresce em retries
```

**Impacto da temperatura:**
- **0.3-0.5**: personas mais previsíveis, menor variação entre entidades do mesmo tipo. Útil para simulações focadas em consistência.
- **0.7-0.9**: personas mais criativas e distintas. Risco de JSON malformado ligeiramente maior.

### 10.3. Observability e Debugging

Cada chamada ao LLM é rastreada via spans de observabilidade (Langfuse-compatible):

```python
span = observation.start_span(
    name="profile_generation",
    metadata={
        "entity_name": name,
        "entity_type": entity_type,
        "attempt": attempt + 1,
        "model": self.model_name,
    },
)
span.update(output=result, latency_ms=latency_ms, usage={...})
```

Métricas capturadas:
- **Latência por entidade**: identifica outliers (entidades com contexto excessivamente longo).
- **Taxa de retry**: se uma entidade específica consistentemente falha nos 3 attempts, pode indicar problema no contexto (ex.: caracteres de controle no sumário).
- **Uso de tokens**: permite estimar custo por simulação e otimizar truncamento.

---

## Considerações Finais

O pipeline de geração de personas é, em essência, um **tradutor de semântica**: converte conhecimento estruturado (grafo) em comportamento simulado (persona). A escolha do LLM como núcleo desse tradutor foi motivada pela necessidade de **contextualidade** — cada persona deve refletir não apenas o tipo da entidade, mas seu papel específico no cenário simulado.

As camadas de resiliência (retry, reparo de JSON, fallback, detecção de idioma) não são adornos: elas refletem a realidade de operar LLMs em escala, onde falhas parciais são inevitáveis. O design prioriza **degradar graciosamente** — uma persona genérica é preferível a uma simulação interrompida.

Para desenvolvedores que desejam estender este sistema, os pontos de entrada mais naturais são:

1. **`_build_entity_context()`**: para enriquecer ainda mais a janela de contexto (ex.: embeddings semânticos, busca Wikipedia).
2. **`_build_individual_persona_prompt()` / `_build_group_persona_prompt()`**: para alterar o tom ou adicionar campos à persona.
3. **`_generate_profile_rule_based()`**: para melhorar a qualidade do fallback quando o LLM está indisponível.
