<!-- generated-by: plan-38-01-T1 -->

# Onboarding Beta — FUTUR.IA

Bem-vindo ao programa de testes beta do FUTUR.IA! Este guia vai te levar do clone até a primeira simulação em 15 minutos.

---

## Primeiros 15 minutos

Siga o checklist abaixo na ordem para garantir que tudo está funcionando:

1. **Clone o repositório**
   ```bash
   git clone <repository-url> futuria-v2-refatorado
   cd futuria-v2-refatorado
   ```

2. **Instale todas as dependências**
   ```bash
   npm run setup:all
   ```
   Isso instala as dependências do Node.js, do frontend e sincroniza o ambiente Python no backend.

3. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   ```
   Abra o arquivo `.env` e preencha obrigatoriamente:
   ```env
   LLM_API_KEY=your_api_key_here
   ZEP_API_KEY=your_zep_api_key_here
   ```

4. **Inicie o ambiente de desenvolvimento**
   ```bash
   npm run dev
   ```

5. **Verifique se o backend está saudável**
   ```bash
   curl http://localhost:5001/health
   ```

Se tudo estiver correto, você verá uma resposta JSON indicando que o serviço está no ar.

---

## Roteiro de primeiro uso

Recomendamos começar pelo cenário didático de **Saúde**, que foi calibrado para introduzir todos os conceitos do pipeline sem sobrecarga cognitiva.

### Passo a passo

1. Acesse o frontend em [http://localhost:4000](http://localhost:4000).
2. Na tela inicial, clique em **"Novo cenário"**.
3. Selecione o template **"Saúde (didático)"**.
4. No painel de configuração, defina:
   - `chunkSize = 300`
   - `maxRounds = 3`
   - `minutesPerRound = 10`
5. Clique em **"Gerar grafo"** e aguarde o grafo de entidades ser construído.
6. Com o grafo pronto, clique em **"Iniciar simulação"**.
7. Aguarde as 3 rodadas serem executadas (cada uma leva aproximadamente o tempo configurado).
8. Ao final, clique em **"Gerar relatório"** e visualize o resultado.
9. Explore a aba **"Inspeção"** para navegar pelas entidades do grafo e verificar a rastreabilidade das fontes.

> **Dica:** o cenário Saúde usa documentos de domínio conhecido, então o grafo tende a ter menos nós "Unknown" e é ideal para validar se o pipeline está saudável.

---

## Tarefas por persona

Cada persona tem **3 tarefas obrigatórias** e **2 tarefas opcionais**. Execute as obrigatórias antes de explorar as opcionais.

### Persona: Pesquisador
*Prioridade: qualidade do grafo e rastreabilidade de fontes.*

**Obrigatórias:**
1. Gerar o grafo do cenário Saúde e inspecionar pelo menos 5 nós, verificando se cada um possui `source_uri` preenchido.
2. Comparar os nós "Unknown" de duas execuções do mesmo cenário e anotar se há variação significativa.
3. Validar se os relacionamentos do grafo refletem as conexões lógicas esperadas no domínio.

**Opcionais:**
4. Exportar o grafo em formato JSON e verificar se a estrutura está consistente com o schema documentado.
5. Testar o cenário com `chunkSize=150` e comparar a densidade do grafo com `chunkSize=300`.

### Persona: Jornalista
*Prioridade: velocidade e clareza do relatório.*

**Obrigatórias:**
1. Executar o pipeline completo (grafo → simulação → relatório) do cenário Saúde em menos de 10 minutos de interação humana.
2. Verificar se o relatório gerado possui título, resumo, corpo e conclusões claramente separados.
3. Ler o relatório e anotar se alguma informação parece confusa, vaga ou fora de contexto.

**Opcionais:**
4. Testar a geração de relatório com `maxRounds=1` e avaliar se a qualidade ainda é aceitável.
5. Copiar o relatório para um editor de texto externo e verificar a formatação de markdown.

### Persona: Analista
*Prioridade: consistência numérica e regressão de cenários.*

**Obrigatórias:**
1. Executar regressão nos 5 cenários base (Saúde, Educação, Meio Ambiente, Economia, Tecnologia) com `chunkSize=300`, `maxRounds=3`, `minutesPerRound=10`.
2. Coletar e comparar o valor de `simulated_hours` de cada execução, verificando se está maior que 0 e consistente.
3. Verificar se o número de entidades no grafo e o número de rodadas completadas são estáveis entre execuções do mesmo cenário.

**Opcionais:**
4. Executar um cenário com `maxRounds=10` e medir o tempo total de execução.
5. Anotar a taxa de nós "Unknown" em cada cenário e identificar se há correlação com a complexidade do domínio.

### Persona: Educador
*Prioridade: legibilidade e exportação.*

**Obrigatórias:**
1. Ler o relatório gerado e avaliar se a linguagem é adequada para público não técnico.
2. Verificar se todo o conteúdo da interface está em pt-BR (incluindo labels, botões e mensagens de erro).
3. Tentar exportar o relatório e confirmar se o arquivo gerado contém o conteúdo completo.

**Opcionais:**
4. Testar o pipeline em uma tela de 1366×768 e anotar problemas de legibilidade.
5. Verificar se o grafo de entidades pode ser explorado de forma intuitiva sem conhecimento prévio do sistema.

---

## Limites conhecidos do beta

O beta do FUTUR.IA ainda está em evolução. Abaixo estão as limitações que já conhecemos e que você pode encontrar:

1. **Thinking process pode vazar em relatórios longos** — em relatórios extensos, trechos do raciocínio interno do modelo podem aparecer no output. Isso está sendo filtrado, mas ainda não é 100%.
2. **Taxa de "Unknown" pode ser alta em domínios novos** — cenários com documentos muito especializados ou fora dos domínios de treinamento tendem a gerar mais nós "Unknown" no grafo.
3. **Fallback do Zep desativa recursos avançados do grafo** — se o serviço Zep Cloud não estiver disponível, o sistema cai para um modo simplificado que não gera memória de longo prazo nem análise de comunidades no grafo.
4. **Simulações com >20 rodadas podem ficar lentas** — o tempo de execução cresce de forma não linear acima de 20 rodadas devido ao acúmulo de estado.
5. **Exportação PDF não suporta gráficos inline** — relatórios exportados em PDF contêm apenas texto; imagens e gráficos gerados durante a simulação não são embutidos.
6. **Modo offline não está disponível** — o sistema requer conectividade com a internet para os serviços de LLM e Zep. Não há fallback 100% local no beta.
7. **i18n não é suportada no beta** — a interface e os relatórios são gerados apenas em português do Brasil. Outros idiomas serão adicionados em versões futuras.
8. **Mobile não está otimizado** — a interface foi projetada para desktop. O uso em dispositivos móveis pode apresentar problemas de layout e usabilidade.

> Se você encontrar um limite que não está nesta lista, considere um reporte valioso! Veja a seção abaixo.

---

## Como reportar

Use o template abaixo ao abrir uma issue no repositório. Copie, preencha e cole no corpo da issue.

```markdown
## Reporte de Beta — FUTUR.IA

**Persona:** [Pesquisador / Jornalista / Analista / Educador / Outro]
**Cenário:** [nome do cenário utilizado]
**simulation_id:** [UUID da simulação, disponível na URL ou no painel de inspeção]

### Passos de reprodução
1.
2.
3.

### Comportamento esperado
[descreva o que você esperava que acontecesse]

### Comportamento observado
[descreva o que realmente aconteceu, incluindo mensagens de erro se houver]

### Severidade
- [ ] **Bloqueante** — impede o uso completamente
- [ ] **Confusão** — funciona, mas de forma confusa ou inesperada
- [ ] **Sugestão** — melhoria ou ideia para o futuro
```

> **Dica:** anexe prints, logs de `backend/logs/YYYY-MM-DD.log` e o `simulation_id` sempre que possível. Quanto mais contexto, mais rápido conseguimos investigar.
