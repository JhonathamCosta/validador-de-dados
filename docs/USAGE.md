# Guia de Uso

Este documento cobre:

- como executar a ferramenta;
- como rodar validacoes via codigo;
- como criar regras reais;
- como criar dominios externos ao kernel;
- como executar os testes com `pytest`.

## 1. Arquitetura de uso

O projeto deve ser tratado como um kernel reutilizavel.

```text
validador-de-dados/
  core/       -> contratos, loader de dominios, engine e aplicacao
  adapters/   -> leitura de CSV, JSON e Excel
  ui/         -> Streamlit e outras interfaces
  domains/    -> apenas dominios embutidos ou de exemplo
```

Regras reais devem preferencialmente ficar fora deste repositorio, em um pacote de dominio separado:

```text
meu-dominio-real/
  domain.json
  __init__.py
  registry.py
  rules/
    __init__.py
    minha_regra.py
```

O kernel carrega dominios externos usando `VALIDATOR_DOMAIN_PATHS`. Em desenvolvimento local, o caminho mais simples e criar um arquivo `.env` na raiz do projeto.

## 2. Executar a interface Streamlit

No diretorio raiz do projeto:

```powershell
streamlit run ui/streamlit_app/app.py
```

Com dominio externo via `.env`, copie o exemplo:

```powershell
Copy-Item .env.example .env
```

Edite `.env`:

```env
VALIDATOR_DOMAIN_PATHS=C:\validador-dominios
VALIDATOR_ENABLE_BUILTIN_DOMAINS=true
```

Depois execute:

```powershell
streamlit run ui/streamlit_app/app.py
```

Tambem e possivel definir a variavel diretamente no PowerShell, sem `.env`:

```powershell
$env:VALIDATOR_DOMAIN_PATHS="C:\caminho\para\meu-dominio-real"
streamlit run ui/streamlit_app/app.py
```

Com mais de um dominio externo, separe os caminhos com `;` no Windows:

```env
VALIDATOR_DOMAIN_PATHS=C:\dominios\financeiro;C:\dominios\rh
```

Voce tambem pode apontar para uma pasta mae. O loader procura subpastas que tenham `domain.json`:

```env
VALIDATOR_DOMAIN_PATHS=C:\validador-dominios
```

```text
C:\validador-dominios\
  financeiro\
    domain.json
  rh\
    domain.json
```

O dominio `exemplo` embutido no kernel vem habilitado por padrao para facilitar testes apos o clone. Em producao ou quando quiser listar somente dominios externos, desligue:

```env
VALIDATOR_ENABLE_BUILTIN_DOMAINS=false
```

Fluxo da tela:

1. selecione o dominio;
2. informe o usuario;
3. envie os arquivos exigidos pelo dominio;
4. clique em `Validar`;
5. veja o resumo;
6. baixe o relatorio em JSON ou Excel.

Metadados visuais da UI:

- `ui/streamlit_app/metadata.json` controla `title` e `caption`;
- `ui/streamlit_app/metadata.example.json` serve como modelo;
- se nenhum arquivo existir, a UI usa valores padrao do codigo.

## 3. Executar via codigo

Use `run_validation_job` como entry point unico para UI, CLI, scripts ou automacoes.

```python
from adapters.inputs.csv import CsvInputAdapter
from core.application import run_validation_job

report = run_validation_job(
    domain_id="exemplo",
    source={
        "dados": "dados.csv",
        "referencias": "referencias.csv",
    },
    adapter={
        "dados": CsvInputAdapter(bundle_key="dados"),
        "referencias": CsvInputAdapter(bundle_key="referencias"),
    },
    context={"user": "admin"},
)

print(report.total_fail)
```

## 4. Adapters disponiveis

Arquivos em `adapters/inputs/`:

- `CsvInputAdapter`;
- `JsonInputAdapter`;
- `ExcelInputAdapter`.

Todos retornam um `bundle` no formato:

```python
{
    "dados": [
        {"coluna_a": "...", "coluna_b": "..."},
    ]
}
```

Se quiser outra chave, ajuste `bundle_key` ao instanciar o adapter.

## 5. Criar uma regra

Cada regra deve expor:

- `name`;
- `rule_id`;
- `run(bundle, context) -> dict`.

Retorno minimo:

- `count`.

Campos recomendados:

- `details`;
- `severity`;
- `message`;
- `status`, quando a regra quiser controlar explicitamente `PASS`, `FAIL`, `WARNING` ou `ERROR`.

Exemplo:

```python
class CodigoObrigatorioRule:
    name = "codigo_obrigatorio"
    rule_id = "codigo_obrigatorio"

    def run(self, bundle, context):
        rows = bundle.get("dados", [])
        invalidos = [
            row
            for row in rows
            if not str(row.get("codigo") or "").strip()
        ]

        return {
            "count": len(invalidos),
            "details": invalidos,
            "severity": "HIGH",
            "message": "Existem registros sem codigo." if invalidos else None,
        }
```

## 6. Criar um dominio externo

Estrutura recomendada:

```text
meu-dominio-real/
  domain.json
  __init__.py
  registry.py
  rules/
    __init__.py
    codigo_obrigatorio.py
```

### 6.1 Manifest `domain.json`

```json
{
  "domain_id": "meu_dominio",
  "name": "Meu Dominio Real",
  "version": "1.0.0",
  "kernel_compatibility": "^1.0.0",
  "entrypoint": "registry.py"
}
```

Campos obrigatorios:

- `domain_id`: identificador usado pela API e pela UI;
- `version`: versao do dominio;
- `kernel_compatibility`: versao de contrato do kernel aceita pelo dominio;
- `entrypoint`: arquivo Python que expoe `get_rules()`.

Campos opcionais:

- `name`;
- `metadata`.

### 6.2 `registry.py`

```python
from .rules.codigo_obrigatorio import CodigoObrigatorioRule

def get_rules():
    return [
        CodigoObrigatorioRule(),
    ]

def get_input_specs():
    return [
        {
            "key": "dados",
            "label": "Base principal",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        }
    ]
```

`get_rules()` e obrigatorio.

`get_input_specs()` e opcional. Quando informado, a UI usa esse metadado para abrir os uploads dinamicamente.

## 7. Validacoes com mais de uma base

O `bundle` pode conter varias bases:

```python
bundle = {
    "dados": [
        {"matricula": "1001", "fazenda": "F001"},
    ],
    "fazendas": [
        {"codigo": "F001", "nome": "Boa Vista"},
        {"codigo": "F002", "nome": "Santa Rita"},
    ],
}
```

A regra pode consumir mais de uma chave:

```python
class CheckFarmExistsRule:
    name = "farm_exists"
    rule_id = "farm_exists"

    def run(self, bundle, context):
        apontamentos = bundle.get("dados", [])
        fazendas = bundle.get("fazendas", [])
        fazendas_validas = {row["codigo"] for row in fazendas}

        invalidos = [
            row
            for row in apontamentos
            if row.get("fazenda") and row["fazenda"] not in fazendas_validas
        ]

        return {
            "count": len(invalidos),
            "details": invalidos,
            "severity": "HIGH",
            "message": "Ha fazendas informadas fora da base de referencia." if invalidos else None,
        }
```

## 8. Executar testes

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Execute:

```powershell
python -m pytest
```

No ambiente local deste repositorio, se estiver usando o `venv` ja criado:

```powershell
.\venv\Scripts\python.exe -m pytest
```

## 9. Boas praticas para regras reais

- mantenha regras pequenas e com responsabilidade unica;
- use `rule_id` estavel para rastreabilidade;
- nao coloque logica de regra na UI;
- nao importe codigo interno do kernel que nao esteja em `core.contracts`;
- prefira deixar dominios reais fora do repositorio do kernel;
- crie testes no repositorio do dominio real;
- use dados de exemplo anonimizados;
- versione kernel e dominio separadamente.

## 10. Checklist para subir um dominio real

1. criar uma pasta ou repositorio externo para o dominio;
2. criar `domain.json`;
3. criar `__init__.py`;
4. criar `registry.py` com `get_rules()`;
5. criar regras em `rules/`;
6. criar `get_input_specs()` se a UI precisar de uploads dinamicos;
7. apontar `VALIDATOR_DOMAIN_PATHS` no `.env` para a pasta do dominio ou pasta mae;
8. definir `VALIDATOR_ENABLE_BUILTIN_DOMAINS=false` se nao quiser mostrar o exemplo do kernel;
9. executar `python -m pytest`;
10. rodar `streamlit run ui/streamlit_app/app.py`;
11. validar o relatorio gerado.
