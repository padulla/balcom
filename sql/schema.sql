PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_tempo (
  tempo_id            INTEGER PRIMARY KEY,
  data_referencia     TEXT NOT NULL, -- YYYY-MM-DD
  ano                 INTEGER NOT NULL,
  mes                 INTEGER NOT NULL,
  trimestre           INTEGER NOT NULL,
  ano_mes             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_fluxo (
  fluxo_id            INTEGER PRIMARY KEY,
  fluxo_codigo        TEXT NOT NULL, -- EXP / IMP
  fluxo_nome          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_produto (
  produto_id          INTEGER PRIMARY KEY,
  ncm                 TEXT,
  descricao_ncm       TEXT,
  sh2                 TEXT,
  sh4                 TEXT,
  sh6                 TEXT,
  fator_agregado      TEXT
);

CREATE TABLE IF NOT EXISTS dim_pais (
  pais_id             INTEGER PRIMARY KEY,
  codigo_pais         TEXT,
  nome_pais           TEXT,
  bloco_economico     TEXT
);

CREATE TABLE IF NOT EXISTS dim_uf (
  uf_id               INTEGER PRIMARY KEY,
  sigla_uf            TEXT,
  nome_uf             TEXT,
  regiao              TEXT
);

CREATE TABLE IF NOT EXISTS f_comercio_exterior (
  fato_id             INTEGER PRIMARY KEY,
  tempo_id            INTEGER NOT NULL REFERENCES dim_tempo(tempo_id),
  fluxo_id            INTEGER NOT NULL REFERENCES dim_fluxo(fluxo_id),
  produto_id          INTEGER REFERENCES dim_produto(produto_id),
  pais_id             INTEGER REFERENCES dim_pais(pais_id),
  uf_id               INTEGER REFERENCES dim_uf(uf_id),

  valor_usd_fob       REAL,
  peso_kg_liquido     REAL,
  quantidade_estat    REAL,

  fonte               TEXT NOT NULL,
  carga_timestamp_utc TEXT NOT NULL DEFAULT (datetime('now')),
  hash_linha_origem   TEXT
);

CREATE INDEX IF NOT EXISTS idx_fato_tempo ON f_comercio_exterior(tempo_id);
CREATE INDEX IF NOT EXISTS idx_fato_fluxo ON f_comercio_exterior(fluxo_id);
CREATE INDEX IF NOT EXISTS idx_fato_produto ON f_comercio_exterior(produto_id);
CREATE INDEX IF NOT EXISTS idx_fato_pais ON f_comercio_exterior(pais_id);
CREATE INDEX IF NOT EXISTS idx_fato_uf ON f_comercio_exterior(uf_id);
