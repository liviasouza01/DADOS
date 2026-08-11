# trade_to_ohlc

Pipeline de **stream processing** que consome trades individuais de um tópico Kafka, agrega preços em janelas temporais (OHLC) e publica features no tópico de saída.

## Intuito

Em mercados financeiros, cada trade chega como evento isolado (preço, volume, timestamp). Para análise e modelos, é preciso agregar esses eventos em **features de janela** — no caso, candles **OHLC** (Open, High, Low, Close) a cada intervalo fixo de tempo.

Este projeto usa [QuixStreams](https://quix.io/docs/quix-streams/) para fazer essa transformação em tempo real sobre Kafka/Redpanda, sem batch offline.

```
produtor  →  trades (Kafka)  →  trade_to_ohlc  →  ohlc_features (Kafka)  →  consumidor
```

## Como funciona

O `main.py` define um pipeline QuixStreams:

1. **Consome** mensagens JSON do tópico `trades`
2. **Agrupa** em janelas tumbling (ex.: 10 segundos)
3. **Reduz** cada janela para OHLC via `reduce_price` / `init_reduce_price`
4. **Publica** o resultado no tópico `ohlc_features`

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   trades    │────▶│  tumbling window │────▶│  ohlc_features  │
│  (input)    │     │  + reduce (OHLC) │     │    (output)     │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

### Tópicos Kafka

| Tópico | Direção | Formato |
|---|---|---|
| `trades` | entrada | JSON — eventos de trade individuais |
| `ohlc_features` | saída | JSON — candles OHLC agregados por janela |

### Variáveis de ambiente

| Variável | Default (host) | Default (Docker) | Descrição |
|---|---|---|---|
| `KAFKA_BROKER_ADDRESS` | `localhost:19092` | `redpanda:9092` | Endereço do broker Kafka/Redpanda |

## Pré-requisitos

- **Python >= 3.12, < 4**
- **Poetry**
- **Docker** (para Redpanda local)

## Instalação

```bash
cd feature_engineering/trade_to_ohlc
poetry install
```

## Infraestrutura — Redpanda

Suba o cluster Kafka local antes de rodar o pipeline:

```bash
docker compose up -d
```

| Serviço | Porta | Função |
|---|---|---|
| `redpanda` | 9092 / 19092 | Broker Kafka-compatible |
| `redpanda-console` | 8080 | UI para inspecionar tópicos e mensagens |

- Console: http://localhost:8080
- Broker (do host): `localhost:19092`
- Broker (de outro container na mesma rede): `redpanda:9092`

```bash
docker compose down    # parar
```

## Uso local

```bash
# 1. subir Redpanda
docker compose up -d

# 2. rodar o pipeline
poetry run python main.py
```

Para override do broker:

```bash
export KAFKA_BROKER_ADDRESS=localhost:19092
poetry run python main.py
```

## Docker

Build e execução do pipeline em container:

```bash
docker build -t trade-to-ohlc .

# rodar na mesma rede do Redpanda
docker network ls | grep redpanda
docker run --network redpanda-cluster_default trade-to-ohlc
```

O Dockerfile define `KAFKA_BROKER_ADDRESS=redpanda:9092` automaticamente.

## Formato esperado das mensagens

### Entrada (`trades`)

Cada mensagem deve ser JSON com pelo menos um campo de preço (a ser usado pela função `reduce_price`):

```json
{
  "symbol": "PETR4",
  "price": 38.50,
  "volume": 100,
  "timestamp": "2026-08-11T12:00:01Z"
}
```

### Saída (`ohlc_features`)

Candles OHLC agregados por janela (formato definido por `reduce_price`):

```json
{
  "symbol": "PETR4",
  "open": 38.50,
  "high": 38.75,
  "low": 38.40,
  "close": 38.60,
  "window_start": "2026-08-11T12:00:00Z",
  "window_end": "2026-08-11T12:00:10Z"
}
```

## Estrutura do projeto

```
trade_to_ohlc/
├── main.py              # pipeline QuixStreams
├── pyproject.toml       # dependências (quixstreams)
├── poetry.lock
├── Dockerfile           # imagem de produção
├── docker-compose.yml   # Redpanda + Console
└── README.md
```

## Customização

Em `main.py`:

- **`WINDOW_SECONDS`** — tamanho da janela tumbling (padrão planejado: 10s)
- **`reduce_price` / `init_reduce_price`** — lógica de agregação OHLC
- **Tópicos** — altere `'trades'` e `'ohlc_features'` conforme necessário
- **Consumer group** — `json__trade_to_ohlc_consumer_group` controla offset e paralelismo

## Status da implementação

O esqueleto do pipeline está definido, mas `main.py` ainda referencia símbolos não implementados:

- `timedelta` (import de `datetime`)
- `WINDOW_SECONDS`
- `reduce_price` / `init_reduce_price`

O pipeline só executará após a implementação dessas funções de agregação.

## Troubleshooting

| Problema | Solução |
|---|---|
| `KeyError: KAFKA_BROKER_ADDRESS` | Exporte `KAFKA_BROKER_ADDRESS=localhost:19092` ou use o default do `main.py` |
| `command not found: poetry` | Instale Poetry e recarregue o shell |
| Erro de conexão com Kafka | Verifique se `docker compose up -d` está rodando |
| `NameError: timedelta` | Implementação incompleta — veja seção "Status da implementação" |
| Imagem do console não encontrada | Use `docker.redpanda.com/redpandadata/console`, não `redpanda-console` |
| Broker errado no Docker | Host usa `localhost:19092`; containers usam `redpanda:9092` |
