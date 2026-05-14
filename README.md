# balcom

Base estruturada para acompanhamento da balança comercial brasileira.

## Objetivo do projeto

Criar uma **base analítica única** para consolidar os dados públicos da balança comercial do Brasil e permitir a criação de relatórios confiáveis por:
- período (mês, trimestre, ano),
- produto (NCM, SH),
- país/bloco,
- UF e município (quando disponível),
- tipo de indicador (exportação, importação, saldo, corrente de comércio).

---

## Fontes oficiais (seed do projeto)

1. Principais resultados:
   - https://balanca.economia.gov.br/balanca/pg_principal_bc/principais_resultados.html
2. Publicações e dados consolidados:
   - https://balanca.economia.gov.br/balanca/publicacoes_dados_consolidados/pg.html
3. Base de dados bruta (MDIC/GOV.BR):
   - https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta

> Recomendação: tratar a base bruta como camada principal de ingestão e os dados consolidados como camada de validação e reconciliação.

---

## Estrutura inicial já criada

```text
balcom/
├─ data/
│  ├─ raw/
│  ├─ staging/
│  └─ analytics/
├─ docs/
├─ pipelines/
│  └─ init_db.py
└─ sql/
   └─ schema.sql
```

---

## Arquitetura proposta (medalhão simples)

### 1) Camada `raw`
Guarda os arquivos exatamente como baixados (CSV, XLSX, ZIP, etc), sem transformação.

Campos mínimos de controle:
- `fonte_url`
- `arquivo_origem`
- `hash_arquivo`
- `data_download_utc`
- `competencia_referente` (se aplicável)

### 2) Camada `staging`
Padronização de tipos e nomes de colunas.

Padronizações recomendadas:
- datas em ISO (`YYYY-MM-DD`),
- códigos preservados como texto (`NCM`, `SH4`, `SH2`, `país`, `UF`),
- valores monetários em decimal,
- volumes e pesos em decimal,
- remoção de duplicidades por chave natural + versão da carga.

### 3) Camada `analytics` (modelo estrela)
Fatos e dimensões para BI.

**Fato principal sugerido:** `f_comercio_exterior`
- grão: `mês x fluxo (EXP/IMP) x produto x país x UF` (ajuste conforme disponibilidade)

---

## Modelo de dados inicial (SQLite)

O DDL está no arquivo `sql/schema.sql`.

### Criar banco local

```bash
python pipelines/init_db.py
```

Isso cria automaticamente `data/balcom.db` com todas as tabelas e índices.

---

## Execução dos próximos passos

1. Inicializar o banco local:

```bash
python pipelines/init_db.py
```

2. Baixar um arquivo bruto (exemplo):

```bash
python pipelines/download_mdic_raw.py   --url "https://exemplo.gov.br/arquivo.csv"   --fonte mdic   --competencia 2025-01
```

3. Padronizar CSV para staging:

```bash
python pipelines/staging_from_csv.py   --input data/raw/mdic/2025/arquivo.csv   --output data/staging/mdic/2025/arquivo_padronizado.csv
```

4. Catalogar links disponíveis na página da base bruta MDIC:

```bash
python pipelines/catalog_mdic_assets.py --output docs/mdic_assets_catalog.csv
```

## Pipeline ETL/ELT (passo a passo)

1. **Ingestão**
   - baixar arquivos das 3 fontes oficiais,
   - salvar em `/data/raw/<fonte>/<ano>/<arquivo>`.

2. **Catalogação**
   - registrar metadados em tabela `controle_arquivos_raw`.

3. **Padronização (`staging`)**
   - unificar nomes de colunas (`valor_fob`, `peso_liquido`, etc),
   - normalizar encoding e separador decimal,
   - mapear códigos de país/NCM/UF.

4. **Carga analítica (`analytics`)**
   - popular dimensões (SCD tipo 1 no início),
   - carregar fato por lote mensal,
   - aplicar deduplicação por chave de negócio.

5. **Qualidade de dados**
   - teste de nulos em chaves,
   - consistência entre somatórios mensais e consolidados,
   - validação de sinais e ranges (valor/peso/quantidade > 0 quando aplicável).

6. **Publicação**
   - expor visões para BI (Power BI/Metabase/Superset),
   - versionar dicionário de dados.

---

## Próximos passos práticos (curto prazo)

1. Implementar o conector da base bruta do MDIC em `pipelines/`.
2. Carregar 1 ano de dados na `raw` e transformar para `staging`.
3. Popular a fato `f_comercio_exterior` e validar contra “principais resultados”.
4. Publicar primeiro relatório com saldo e corrente por mês.

---

## Observações SQLite

- Habilitar `PRAGMA foreign_keys = ON;` na conexão para validar chaves estrangeiras.
- Para grandes volumes, migrar para DuckDB/PostgreSQL no futuro sem mudar o modelo lógico.

## Carga inicial da fato a partir da staging

Para carregar dados padronizados na `f_comercio_exterior`, o CSV precisa conter ao menos:
- `data_referencia` (YYYY-MM-DD)
- `fluxo_codigo` (ex.: EXP/IMP)
- `fluxo_nome`
- `valor_usd_fob`
- `fonte`

Execução:

```bash
python pipelines/load_staging_to_sqlite.py --input data/staging/mdic/2025/arquivo_padronizado.csv
```
