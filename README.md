# DocAI

Extract structured data from unstructured documents using Answer.AI's [Byaldi](https://github.com/AnswerDotAI/byaldi), OpenAI [gpt-4o](https://platform.openai.com/docs/guides/vision), and [Langchain's structured output](https://python.langchain.com/v0.1/docs/modules/model_io/chat/structured_output/).

## How it works

The tool runs in two steps:

1. **Index** — Each page of every document in a folder is converted to an image, embedded with the ColPali model (`vidore/colpali-v1.2`), and saved under `.byaldi/<index_name>/`.
2. **Extract** — For each question you ask, Byaldi retrieves the most relevant pages from the index, sends them as images to GPT-4o, and returns a structured Pydantic object.

```
pdfs/  →  build_index.py  →  .byaldi/application/  →  extract.py  →  structured JSON-like output
```

The sample `pdfs/` folder contains four Greentown Burgers insurance documents:

| File | Content |
|---|---|
| `greentown_burgers_140.pdf` | Property insurance application (3 pages) |
| `GREENTOWN_LOSSRUN.png` | Loss run report (1 page) |
| `Greentown-ACORD-0126-2016-03.pdf` | ACORD application form (4 pages) |
| `greentown_virginia_2011_articles.pdf` | Articles of incorporation (3 pages) |

After indexing, all 11 pages are searchable as a single collection named `application`.

## Prerequisites

- **Python 3.10–3.12** (3.14 is not supported)
- **Poetry** ([install guide](https://python-poetry.org/docs/#installation))
- **API keys** — `OPENAI_API_KEY` (required for extraction) and `HF_TOKEN` (required to download the ColPali model on first run)

## Installation

```bash
cd docai
poetry env use ~/.pyenv/versions/3.12.12/bin/python   # or any Python 3.10–3.12
poetry install
```

Set your environment variables:

```bash
export OPENAI_API_KEY=<your key>
export HF_TOKEN=<your token>
```

> **Note:** Always run scripts through Poetry (`poetry run python ...`). Do not use a separate virtualenv with Python 3.14 — the project dependencies are installed in Poetry's environment.

## Usage

### Step 1 — Build the index

```bash
poetry run python scripts/build_index.py --folder "pdfs/" --index_name "application"
```

This downloads the ColPali model on the first run (may take several minutes), then indexes every file in `pdfs/`. When finished, you will see output like:

```
Indexing file: pdfs/greentown_burgers_140.pdf
Added page 1 of document 0 to index.
...
Index exported to .byaldi/application
```

The index is saved to `.byaldi/application/` and contains:

| Path | Description |
|---|---|
| `embeddings/embeddings_0.pt` | ColPali vector embeddings (not human-readable) |
| `collection/0.json.gz` | Page images stored as base64 PNG |
| `doc_ids_to_file_names.json.gz` | Maps document IDs to source file paths |
| `embed_id_to_doc_id.json.gz` | Maps each embedding to a document + page number |
| `index_config.json.gz` | Model name and index metadata |

You only need to rebuild the index when documents in `pdfs/` change.

### Step 2 — Extract structured data

```bash
poetry run python scripts/extract.py
```

This loads the `application` index and runs two example queries defined in `scripts/extract.py`. For each query, the pipeline:

1. Searches the index for the top `k` most relevant pages (default `k=3`)
2. Sends those page images to GPT-4o with a Pydantic schema
3. Prints the structured result

### Example output

Results vary between runs because retrieval picks different pages and the LLM interprets images probabilistically. A typical run with the sample documents looks like:

```
What losses have occurred in the past 5 years?
LossHistory(
    losses=[
        Loss(
            loss_date='09/01/2024',
            loss_amount=500000.0,
            loss_description='Equipment breakdown',
            date_of_claim='07/22/2024'
        )
    ]
)

What is the basic application information for the property section?
Application(
    insured_name=ExplainedField(
        explanation="The insured name is found under the 'NAMED INSURED(S)' section on the first page of the document.",
        text='Greentown Burgers'
    ),
    insured_address=None,
    insured_phone=None,
    insured_email=None,
    effective_date='09/01/2024'
)
```

The loss run document (`GREENTOWN_LOSSRUN.png`) contains four truck-accident claims from 2021. If those pages are not in the top `k` results for the loss query, the model may return fewer losses or pull data from a different document. Increase `k` or make queries more specific to improve recall.

## Customizing extraction

Open `scripts/extract.py` to change what gets extracted:

- **Queries** — Edit the question strings in the `for query, data_model in [...]` loop.
- **Schemas** — Define new Pydantic models (like `Application` or `LossHistory`) with `Field(description=...)` to tell GPT-4o what to extract.
- **Top-k pages** — Pass a higher `k` to `extractor.extract(..., k=5)` to send more pages to the model.

You can also use the `Extractor` class directly in your own code:

```python
from docai.extractor import Extractor
from scripts.extract import Application

extractor = Extractor(index_name="application")
result = extractor.extract(
    query="What is the insured name and effective date?",
    data_model=Application,
    k=5,
)
print(result)
```

## Inspecting the index

To see which documents were indexed:

```bash
gzip -dc .byaldi/application/doc_ids_to_file_names.json.gz | python -m json.tool
```

To export a page image from the collection (page key `"0"` is the first page):

```bash
poetry run python - <<'PY'
import gzip, json, base64
from pathlib import Path

data = json.load(gzip.open(".byaldi/application/collection/0.json.gz"))
Path("page_0.png").write_bytes(base64.b64decode(data["0"]))
print("Saved page_0.png")
PY
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Current Python version (3.14.0) is not allowed` | Run `poetry env use ~/.pyenv/versions/3.12.12/bin/python` |
| `command not found: poetry` | Install Poetry: `curl -sSL https://install.python-poetry.org \| python3 -` then reload your shell |
| `ModuleNotFoundError: No module named 'fire'` | You are outside Poetry's env. Use `poetry run python ...` |
| Model download is slow | First run downloads ~2 GB ColPali weights from Hugging Face. Requires `HF_TOKEN`. |
| Extraction returns unexpected values | Increase `k`, use more specific queries, or verify the right pages are retrieved via the index inspection commands above |
