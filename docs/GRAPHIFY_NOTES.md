# Graphify use and interpretation

**Updated: 30 September 2026.** The final feature extraction contains **656 nodes, 1,272 reported edges and 31 communities**. The report labels 96% of edges EXTRACTED and 3% INFERRED, with 41 inferred edges at an average confidence of 0.64. Rounded percentages need not sum to 100. Model token cost: **0 input, 0 output**.

Read [GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md) or open [the interactive graph](../graphify-out/graph.html). This graph maps source structure; it does not establish regulatory compliance or replace the functional tests.

## Extraction scope

The extraction processed 44 supported files: 21 code, 22 document and one image. No model API key was configured, so no semantic LLM pass analysed clinical claims. Code syntax and Markdown structure supply the available relationships. Unsupported file types, including CSV and CSS, need independent inspection.

Excluded material includes the virtual environment, databases, backups, screenshots, validator output, input PDF, generated graph, submission package, caches and environment files. No real participant dataset entered the graph.

## Report findings

**God Nodes:** “`esc()` - 28 edges”, “`Judge questions and defensible answers` - 28 edges” and “`AccountTest` - 24 edges”. These are connection counts, not quality ratings or reasons by themselves to refactor.

**Surprising Connections:** “`inspect_database()` --calls--> `verify_audit()` [EXTRACTED]”, from `ops.py` to `server.py`. Recovery checks reuse the audit-chain verification implementation. The report also records `snapshot()` calls into the account, document, exchange and safety modules. UI `match()` relationships are labelled INFERRED and should not be treated as confirmed calls without inspecting source.

**Suggested Questions:** “Are the 15 inferred relationships involving `Client` (e.g. with `AccountTest` and `.setUp()`) actually correct?” This is a useful navigation question across tests. The graph's inferred edges remain hypotheses; the passing test suite supplies independent behavioural evidence.

Cohesion is **0.15** for the principal frontend community, **0.15** for the main backend community, **0.16** for recovery tooling, **0.28** for the safety backend and **0.36** for accounts. The report gives the backend's unrounded score as **0.14799154334038056**. These are clustering metrics, not software-quality or clinical-validity scores. The report lists 257 weakly connected nodes and four omitted thin communities; missing graph edges do not prove missing implementation.

## Benchmark

The tool printed:

```text
Corpus:          32,800 words → ~43,733 tokens (naive)
Graph:           656 nodes, 1,269 edges
Avg query cost:  ~2,621 tokens
Reduction:       16.7x fewer tokens per query
```

Per-question estimates were 11.5× for authentication, 23.8× for the entry point, 19.4× for data/API relationships and 17× for core abstractions. These are Graphify benchmark estimates, not measured token savings for the assistant session or product outcomes. The benchmark counts three fewer edges than the extraction report; both outputs are preserved without silently normalising them. The corpus estimate is not an independent word count of every delivered document.

## Rebuild

```bash
graphify extract . --exclude '.venv/**' --exclude 'data/**' --exclude 'backups/**' --exclude 'docs/screenshots/**' --exclude 'docs/validation/**' --exclude '*.pdf' --exclude 'graphify-out/**' --exclude 'submission/**' --exclude '**/__pycache__/**' --exclude 'test-results/**' --exclude '.env*' --max-concurrency 1
graphify benchmark
```

This record describes the extraction before the final handoff-note edits. Source-code nodes match the tested build; later documentation edits may move headings or line numbers. The previous saved query about `renderPage()`, `aboutPage()` and `compliancePage()` remains historical navigation context, not proof of every current dispatch path.
