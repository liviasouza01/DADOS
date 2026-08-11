# DADOS

Monorepo de experimentos em dados: extração de documentos com IA e engenharia de features em streaming.

## Estrutura

```
├── docai/                              # extração estruturada de PDFs/imagens
└── feature_engineering/
    └── trade_to_ohlc/                # agregação OHLC em Kafka/Redpanda
```

## Módulos

| Módulo | Descrição | Documentação |
|---|---|---|
| **docai** | Indexação multimodal (ColPali) + extração com GPT-4o | [docai/README.md](docai/README.md) |
| **trade_to_ohlc** | Stream processing de trades → candles OHLC | [feature_engineering/trade_to_ohlc/README.md](feature_engineering/trade_to_ohlc/README.md) |

## Quick start

### DocAI

```bash
cd docai
poetry install
poetry run python scripts/build_index.py --folder "pdfs/" --index_name "application"
poetry run python scripts/extract.py
```

### trade_to_ohlc

```bash
cd feature_engineering/trade_to_ohlc
docker compose up -d
poetry install
poetry run python main.py
```
