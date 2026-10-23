# AI Model Selector and Cost Estimator

A Python command-line application that helps compare local and cloud AI model options for a product workload. It estimates monthly token usage and cloud API costs, then ranks model profiles using an explainable heuristic based on task fit, privacy, available RAM, context window, and budget.

> **Important:** The included model prices, context windows, and RAM requirements are illustrative examples for learning. Verify and update them before making real purchasing or deployment decisions.

## Features

- Compare models for summarization, question answering, content generation, and coding.
- Accept privacy preference, available RAM, monthly request count, average input/output tokens, and monthly budget.
- Estimate monthly input and output token volume separately.
- Calculate cloud token cost from input and output prices per million tokens.
- Rank candidates and show the positive reasons and limitations for each recommendation.
- Optionally check the local Ollama API and list installed local models.
- Load an editable model catalog from JSON.
- Optionally export the recommendations to a Markdown report.
- Uses only the Python standard library; no third-party packages are required.

## Requirements

- Python 3.10 or newer recommended.
- Ollama is optional and only needed for the `--check-ollama` option.

## Quick Start

Run with default sample inputs:

```bash
python3 solution.py
```

Compare models for coding with a high privacy preference:

```bash
python3 solution.py --task coding --privacy high --ram 16 --requests 5000
```

Check whether Ollama is running and list installed models:

```bash
python3 solution.py --task qa --input-tokens 1800 --output-tokens 350 --check-ollama
```

Create a Markdown report:

```bash
python3 solution.py --task summarization --requests 2000 --budget 10 --report report.md
```

Use a custom catalog:

```bash
python3 solution.py --catalog models.json --task coding
```

View all command-line options:

```bash
python3 solution.py --help
```

## Cost Calculation

The program estimates monthly token volume as follows:

```text
monthly_input_tokens  = requests_per_month * average_input_tokens
monthly_output_tokens = requests_per_month * average_output_tokens

input_cost  = monthly_input_tokens / 1,000,000 * input_price_per_million
output_cost = monthly_output_tokens / 1,000,000 * output_price_per_million

monthly_cloud_cost = input_cost + output_cost
```

Local model API cost is estimated as zero in this tool. Hardware, electricity, and maintenance costs are not included.

## Ranking Criteria

The score is a transparent learning heuristic, not a model-quality benchmark. It considers:

- **Task fit:** whether the model profile lists the requested task.
- **Privacy:** local execution receives a higher score when privacy is set to `high`.
- **Budget:** candidates are rewarded for staying within the monthly budget and penalized when they exceed it.
- **Context window:** the requested input and output tokens for a single request are checked against the profile's context window.
- **RAM fit:** local profiles are rewarded when the available RAM meets the estimated requirement and penalized when it does not.

The ranking is intended to explain trade-offs. Validate real model quality, latency, throughput, context behavior, and hardware requirements for your use case.

## Project Files

```text
ai-model-selector-cost-estimator/
├── README.md
├── .gitignore
├── solution.py
└── models.json
```

- `solution.py` — CLI application, cost estimator, ranking logic, Ollama check, and optional report generator.
- `models.json` — example model catalog that can be edited.
- `.gitignore` — ignores local environment files, caches, generated reports, and large model artifacts.

## Customize the Catalog

Edit `models.json` to change the example profiles and prices. Each model object should include:

- `name`
- `provider` (`local` or `cloud`)
- `tasks`
- `ram_gb`
- `context_tokens`
- `input_price`
- `output_price`

Prices are expressed in USD per one million tokens. The supplied values are placeholders and are not current provider quotes.

## Limitations

- Cost estimates depend on the average token counts and request volume supplied by the user.
- Context fit is checked using input tokens plus output tokens for one request.
- Actual RAM needs depend on model size, quantization, runtime, context length, and other system workloads.
- An unavailable Ollama service produces a warning; it does not stop the recommendation process.
- The score is a simple heuristic and should not replace hands-on evaluation.

## Learning Outcomes

This project practices command-line argument parsing, Python `dataclass`, JSON handling, HTTP requests using the standard library, cost estimation, and explainable decision logic.
