# Lessons

- Se `LANGFUSE_ENABLED=true`, o código ainda precisa cair em no-op quando SDK ou credenciais não existirem de forma coerente.
- Teste de caminho "enabled" não deve depender de instalação real do SDK quando um fake cobre contrato melhor.
- Retry sem span por tentativa fica invisível no Langfuse; se quer diagnosticar falha intermitente, crie span filho por attempt.
