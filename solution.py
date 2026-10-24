import argparse
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

# Example values only. Edit prices/specifications before real-world use.
MODEL_CATALOG = [
    {"name": "Local Small (Ollama)", "provider": "local", "tasks": ["summarization", "qa", "content", "coding"], "ram_gb": 8, "context_tokens": 8192, "input_price": 0.0, "output_price": 0.0},
    {"name": "Local Medium (Ollama)", "provider": "local", "tasks": ["summarization", "qa", "content", "coding"], "ram_gb": 16, "context_tokens": 32768, "input_price": 0.0, "output_price": 0.0},
    {"name": "Cloud Economy", "provider": "cloud", "tasks": ["summarization", "qa", "content"], "ram_gb": 0, "context_tokens": 128000, "input_price": 0.20, "output_price": 0.80},
    {"name": "Cloud Balanced", "provider": "cloud", "tasks": ["summarization", "qa", "content", "coding"], "ram_gb": 0, "context_tokens": 200000, "input_price": 2.00, "output_price": 8.00},
    {"name": "Cloud Coding", "provider": "cloud", "tasks": ["coding"], "ram_gb": 0, "context_tokens": 128000, "input_price": 1.50, "output_price": 6.00},
]

@dataclass
class Requirements:
    task: str = "qa"
    privacy: str = "medium"
    ram: float = 16
    requests: int = 1000
    input_tokens: int = 1000
    output_tokens: int = 300
    budget: float = 20.0

def estimate_cost(model, input_total, output_total):
    return input_total / 1_000_000 * model["input_price"] + output_total / 1_000_000 * model["output_price"]

def recommend(req, catalog):
    input_total = req.requests * req.input_tokens
    output_total = req.requests * req.output_tokens
    ranked = []
    for model in catalog:
        score, positives, limitations = 50.0, [], []
        if req.task in model["tasks"]:
            score += 15
            positives.append(f"Supports task: {req.task}.")
        else:
            score -= 30
            limitations.append(f"Task {req.task} is not listed as supported.")

        if req.privacy == "high":
            if model["provider"] == "local":
                score += 30
                positives.append("Local execution fits the high-privacy preference.")
            else:
                limitations.append("Cloud processing may send data to an external provider.")
        elif req.privacy == "medium":
            score += 18 if model["provider"] == "local" else 12
            if model["provider"] == "cloud":
                limitations.append("Review the provider's privacy and data-retention terms.")
        else:
            score += 12 if model["provider"] == "local" else 18

        cost = estimate_cost(model, input_total, output_total)
        if cost <= req.budget:
            score += 15
            positives.append(f"Estimated monthly token cost (${cost:.4f}) is within budget.")
        else:
            score -= min(30, 10 + (cost - req.budget) / max(req.budget, 1) * 5)
            limitations.append(f"Estimated cost ${cost:.4f} exceeds budget ${req.budget:.2f}.")

        request_context = req.input_tokens + req.output_tokens
        if request_context <= model["context_tokens"]:
            score += 10
            positives.append(f"{request_context:,} tokens/request fit context window {model['context_tokens']:,}.")
        else:
            score -= 25
            limitations.append(f"{request_context:,} tokens/request exceed context window {model['context_tokens']:,}.")

        if model["provider"] == "local":
            if req.ram >= model["ram_gb"]:
                score += 10
                positives.append(f"Estimated RAM ({model['ram_gb']} GB) fits available RAM ({req.ram:g} GB).")
            else:
                score -= 35
                limitations.append(f"Insufficient RAM: estimated {model['ram_gb']} GB, available {req.ram:g} GB.")
            positives.append("No per-token API charge in this estimate; hardware and electricity costs are excluded.")
        else:
            positives.append("Inference uses provider infrastructure rather than local RAM.")

        ranked.append({
            "name": model["name"], "provider": model["provider"],
            "score": round(max(0, min(100, score)), 1), "cost": cost,
            "positives": positives, "limitations": limitations
        })
    ranked.sort(key=lambda item: (item["score"], -item["cost"]), reverse=True)
    return ranked, input_total, output_total

def check_ollama():
    url = "http://localhost:11434/api/tags"
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
        names = [item.get("name", "unknown") for item in data.get("models", [])]
        print(f"Ollama is reachable at {url}.")
        print("Installed models:" if names else "No installed models were reported.")
        for name in names:
            print(f"  - {name}")
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"Warning: could not connect to Ollama at {url}: {exc}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Compare illustrative local/cloud model profiles.")
    parser.add_argument("--task", choices=["summarization", "qa", "content", "coding"], default="qa")
    parser.add_argument("--privacy", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--ram", type=float, default=16, help="Available RAM in GB.")
    parser.add_argument("--requests", type=int, default=1000, help="Requests per month.")
    parser.add_argument("--input-tokens", type=int, default=1000)
    parser.add_argument("--output-tokens", type=int, default=300)
    parser.add_argument("--budget", type=float, default=20, help="Monthly budget in USD.")
    parser.add_argument("--check-ollama", action="store_true")
    parser.add_argument("--catalog", help="Optional JSON file containing model profiles.")
    parser.add_argument("--report", help="Optional Markdown report output path.")
    args = parser.parse_args()
    if args.ram < 0 or args.requests <= 0 or args.input_tokens < 0 or args.output_tokens < 0 or args.budget < 0:
        parser.error("RAM, token counts, and budget must be non-negative; requests must be greater than zero.")

    req = Requirements(args.task, args.privacy, args.ram, args.requests, args.input_tokens, args.output_tokens, args.budget)
    catalog = MODEL_CATALOG
    if args.catalog:
        try:
            with open(args.catalog, encoding="utf-8") as file:
                catalog = json.load(file)
            required = {"name", "provider", "tasks", "ram_gb", "context_tokens", "input_price", "output_price"}
            if not isinstance(catalog, list) or any(not isinstance(m, dict) or not required.issubset(m) for m in catalog):
                raise ValueError("Expected a list of model objects with all required fields.")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parser.error(f"Could not load catalog: {exc}")

    if args.check_ollama:
        check_ollama()

    ranked, input_total, output_total = recommend(req, catalog)
    print("AI Model Selector and Monthly Cost Estimate")
    print("=" * 44)
    print(f"Task: {req.task} | Privacy: {req.privacy} | Available RAM: {req.ram:g} GB")
    print(f"Requests/month: {req.requests:,}")
    print(f"Monthly input tokens:  {input_total:,}")
    print(f"Monthly output tokens: {output_total:,}")
    print(f"Monthly total tokens:  {input_total + output_total:,}")
    print(f"Monthly budget: ${req.budget:.2f}")
    print("\nTop 3 recommendations\n---------------------")
    for index, item in enumerate(ranked[:3], 1):
        print(f"\n{index}. {item['name']} [{item['provider']}]")
        print(f"   Score: {item['score']:.1f}/100")
        print(f"   Estimated monthly token cost: ${item['cost']:.6f}")
        print("   Positive reasons:")
        for reason in item["positives"]:
            print(f"     + {reason}")
        print("   Limitations:")
        for reason in item["limitations"]:
            print(f"     - {reason}")
        if not item["limitations"]:
            print("     - None identified by this heuristic")

    print("\nNote: prices, context windows, and RAM figures are illustrative examples.")
    if args.report:
        lines = ["# AI Model Selector Report", "", "> Prices/specifications are illustrative.", "",
                 f"- Task: {req.task}", f"- Privacy: {req.privacy}", f"- Available RAM: {req.ram:g} GB",
                 f"- Requests/month: {req.requests:,}", f"- Monthly input tokens: {input_total:,}",
                 f"- Monthly output tokens: {output_total:,}", "", "## Top 3 recommendations", ""]
        for i, item in enumerate(ranked[:3], 1):
            lines += [f"### {i}. {item['name']} — {item['score']:.1f}/100", "",
                      f"- Estimated monthly token cost: ${item['cost']:.6f}", "- Positives:"]
            lines += [f"  - {x}" for x in item["positives"]]
            lines += ["- Limitations:"] + ([f"  - {x}" for x in item["limitations"]] or ["  - None identified"])
            lines.append("")
        with open(args.report, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))
        print(f"Markdown report saved to: {args.report}")

if __name__ == "__main__":
    main()
