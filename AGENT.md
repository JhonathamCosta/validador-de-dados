# AGENT.md — Data Validation Kernel

Arquivo de instruções para agentes de IA que editam este repositório.

Mantenha este arquivo curto. Detalhes longos devem ir para `docs/`.

## Missão do projeto

Evoluir um kernel Python de validação semântica de dados operacionais.

O sistema deve manter:

- regras modulares por domínio;
- contratos padronizados de entrada e saída;
- execução resiliente;
- saída rastreável;
- UI desacoplada do core.

## Mapa rápido

```text
core/       contratos, modelos, engine e serviços genéricos
adapters/   leitura de CSV, JSON, Excel, SQL ou outras fontes
domains/    regras de negócio por domínio
ui/         interfaces, sem regra de negócio
docs/       documentação técnica complementar
```

## Regras de edição

- Não coloque regra de negócio em `ui/`.
- Não coloque código específico de domínio dentro de `core/`.
- Não acople regra diretamente a Streamlit, CLI ou web app.
- Use `core.application.run_validation_job(...)` como entry point para interfaces.
- Prefira mudanças pequenas, revisáveis e com teste focado.
- Preserve compatibilidade dos contratos públicos sempre que possível.

## Estilo de código

- Funções devem ser pequenas e ter uma responsabilidade clara.
- Arquivos devem permanecer curtos; se crescerem demais, divida por responsabilidade.
- Use nomes específicos e pesquisáveis.
- Evite nomes genéricos como `data`, `handler`, `manager`, `processor` ou `service` sem contexto.
- Use type hints em funções novas ou alteradas.
- Evite `Any`, `Dict` genérico e retornos implícitos quando houver alternativa clara.
- Prefira early return a aninhamento profundo.
- Não duplique lógica; extraia função, classe ou módulo.
- Use comentários para explicar decisão, restrição ou contexto de negócio.
- Não escreva comentários óbvios que apenas repetem o código.

## Contratos obrigatórios

### Regra

Cada regra deve expor:

- `name`;
- `run(bundle, context)`;
- retorno com `count`.

Quando aplicável, também expor:

- `rule_id`;
- `severity`;
- `message`;
- `details`;
- `status`.

### Resultado

O executor deve sempre converter a saída da regra para `RuleResult`.

Falha em uma regra não deve interromper a execução das demais. Exceções devem virar resultado com status `ERROR` e mensagem com contexto suficiente para diagnóstico.

### Relatório

A consolidação final deve retornar `ValidationReport`.

Não retorne estruturas soltas para UI quando já existir contrato no core.

## Padrão para novas regras

Crie regras dentro de:

```text
domains/<dominio>/rules/
```

A regra deve:

- ser determinística;
- não fazer I/O diretamente;
- ler somente o necessário do `bundle`;
- retornar evidências em `details`;
- usar mensagem de negócio em português;
- manter nomes de código em inglês.

Modelo mínimo:

```python
class MissingCodeRule:
    rule_id = "missing_code"
    name = "Missing code"

    def run(self, bundle, context):
        rows = bundle.get("dados", [])

        invalid_rows = [
            row
            for row in rows
            if not row.get("codigo")
        ]

        return {
            "count": len(invalid_rows),
            "details": invalid_rows,
            "message": "Existem registros sem código.",
            "severity": "HIGH",
        }
```

## Testes e validação

Ao alterar código, priorize rodar comandos focados.

Comandos esperados, conforme disponibilidade do projeto:

```bash
python -m pytest
python -m pytest tests/path/to/test_file.py
python -m ruff check .
python -m mypy .
```

Se algum comando não existir no projeto, não invente configuração grande sem necessidade. Registre a ausência e siga com a menor alteração segura.

## Erros e logs

- Mensagens de erro devem dizer o que falhou, onde falhou e qual dado relevante foi recebido.
- Evite erro genérico como `invalid input`.
- Prefira mensagens com contexto, por exemplo: domínio, regra, chave de negócio e campo problemático.
- Não exponha segredo, token, senha ou credencial em log.

## Organização de documentação

Use `README.md` apenas para visão geral e entrada rápida.

Use `docs/` para explicações maiores, como:

```text
docs/
  README.md
  USAGE.md
  ARCHITECTURE.md
  RULES.md
  TESTING.md
  ROADMAP.md
```

Ao criar documentação nova:

- escreva de forma direta;
- evite texto filosófico;
- coloque comandos executáveis;
- inclua exemplos pequenos;
- mantenha cada arquivo focado em um assunto.

## Antes de finalizar uma alteração

Verifique:

- a UI continua sem regra de negócio;
- o core continua genérico;
- a regra nova está no domínio correto;
- o retorno respeita `RuleResult`;
- exceções de regra não quebram o pipeline;
- nomes são específicos e fáceis de buscar;
- comentários explicam contexto, não sintaxe óbvia;
- há teste ou justificativa objetiva para não haver teste.

## Prioridade atual

O próximo ganho objetivo do projeto é persistência de histórico com SQLite ou DuckDB.

Ao trabalhar nisso, mantenha separado:

```text
storage/
  repositories/
  models/
  migrations/
  exporters/
```

Não misture persistência dentro de regras.
