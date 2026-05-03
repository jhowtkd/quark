<!-- generated-by: plan-38-01-T5 -->

# Checklist de Beta Tester — FUTUR.IA

Use este checklist para garantir que você cobriu todas as áreas do teste beta antes de reportar. Copie o checklist preenchido no corpo da issue ao abrir um reporte.

---

## 1. Setup

- [ ] Clonei o repositório e estou na branch correta.
- [ ] Execute `npm run setup:all` sem erros (Node.js + frontend + backend).
- [ ] Copiei `.env.example` para `.env` e preenchi `LLM_API_KEY` + `ZEP_API_KEY`.
- [ ] Execute `curl http://localhost:5001/health` e recebi resposta positiva.
- [ ] Execute `npm run preflight` e todos os checks passaram (ou anotei os que falharam).

---

## 2. Pipeline básico

- [ ] Fiz upload ou selecionei um cenário (ex: Saúde didático).
- [ ] O grafo de entidades foi gerado com sucesso e apareceu na tela.
- [ ] A simulação foi completada até o número de rodadas configurado (`maxRounds`).
- [ ] O relatório gerado não está vazio e contém texto significativo.
- [ ] A aba de inspeção está acessível e mostra os nós/arestas do grafo.

---

## 3. Qualidade

- [ ] Todo o conteúdo visível da interface está em pt-BR (labels, botões, mensagens).
- [ ] O campo `simulated_hours` no relatório é maior que 0.
- [ ] Não encontrei trechos de thinking process (raciocínio interno do modelo) no relatório final.
- [ ] Não há traceback ou stack trace visível na interface do usuário.
- [ ] O relatório possui estrutura completa: título + resumo + corpo + conclusões.

---

## 4. Reporte

- [ ] Preenchi o template de reporte com todos os campos obrigatórios.
- [ ] Anexei o `simulation_id` da execução onde o comportamento foi observado.
- [ ] Classifiquei a severidade corretamente (bloqueante / confusão / sugestão).
- [ ] Descrevi os passos de reprodução de forma clara e sequencial.
- [ ] Informei a persona que estava utilizando durante o teste.

---

## Instruções de uso

1. Antes de começar os testes, crie uma cópia deste checklist em branco.
2. À medida que executa cada item, marque o checkbox correspondente.
3. Se algum item falhar, anote o que aconteceu ao lado do checkbox.
4. Ao abrir uma issue no repositório, **cole este checklist preenchido no corpo da issue** para que a equipe tenha visão completa do que foi testado.

> **Importante:** um reporte completo com este checklist preenchido tem prioridade de triagem maior do que reportes sem contexto.
