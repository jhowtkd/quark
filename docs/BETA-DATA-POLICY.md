# Política de Retenção de Dados — Fase Beta FUTUR.IA

## 1. Escopo e Aplicação

Este documento estabelece as diretrizes para o tratamento, armazenamento e exclusão de dados coletados durante a fase beta do projeto FUTUR.IA. A política se aplica a todos os testadores, mantenedores do repositório e ambientes de execução provisionados para testes.

## 2. Dados Coletados Durante o Beta

Durante a fase de testes, os seguintes tipos de dados podem ser armazenados nos volumes do ambiente beta:

- **Uploads de documentos**: arquivos enviados pelos testadores para processamento pelo sistema.
- **Resultados de simulações**: saídas geradas pelos agentes de inteligência artificial, incluindo resumos, análises e classificações.
- **Logs operacionais**: registros de eventos do sistema, mensagens de erro e rastros de execução.
- **Feedback dos testadores**: avaliações, relatórios de bug e sugestões enviadas pelos participantes do programa beta.

## 3. Período de Retenção

Cada categoria de dado possui um prazo específico de permanência nos servidores beta:

- **Uploads e resultados de simulações**: mantidos por **30 dias** a partir da data de criação, após o que são automaticamente removidos.
- **Logs operacionais**: conservados por **7 dias**, período necessário para diagnóstico e estabilização do sistema.
- **Feedback dos testadores**: após anonimização, os dados são mantidos de forma permanente para fins de melhoria contínua do produto.

## 4. Controle de Acesso

O acesso aos volumes de dados da fase beta é estritamente controlado. Apenas os mantenedores do repositório (repo maintainers) possuem permissão para consultar, exportar ou modificar informações armazenadas nos ambientes de teste. Testadores individuais não têm acesso aos dados de outros participantes.

## 5. Proibições e Restrições de Uso

É expressamente proibido aos testadores:

- Enviar dados pessoais reais (PII), incluindo nomes, documentos de identidade, endereços ou qualquer informação que permita a identificação de indivíduos.
- Fazer upload de documentos confidenciais, sob sigilo profissional ou protegidos por acordos de não divulgação.
- Submeter conteúdo protegido por direitos autorais sem a devida autorização do titular.
- Utilizar o ambiente beta para processar informações classificadas ou sensíveis de qualquer natureza.

## 6. Aviso Legal sobre Processamento por LLMs

Os dados enviados ao ambiente beta podem ser processados por modelos de linguagem de terceiros (LLMs). Por esse motivo, é obrigatório que nenhum dado submetido contenha PII ou informações sensíveis. O projeto FUTUR.IA não se responsabiliza pelo vazamento de informações inseridas em desacordo com esta política.

## 7. Exclusão de Dados

Todos os dados da fase beta podem ser eliminados de forma definitiva e irreversível mediante a execução do seguinte comando:

```bash
docker compose -f docker-compose.beta.yml down -v
```

Este comando destrói todos os volumes associados ao ambiente beta, incluindo uploads, simulações e logs. A operação não pode ser desfeita.

## 8. Revisão e Contato

Esta política pode ser revisada a qualquer momento para refletir mudanças na arquitetura do sistema ou na legislação aplicável. Dúvidas sobre o tratamento de dados na fase beta devem ser encaminhadas aos mantenedores do projeto por meio dos canais oficiais de comunicação.

---
*Última atualização: maio de 2026*
