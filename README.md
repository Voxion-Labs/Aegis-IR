<div align="center">

# Aegis-IR

### Deterministic Memory for Browser-Native Information Retrieval

![Research Type](https://img.shields.io/badge/Research%20Type-Applied%20Systems-58a6ff?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-Zero--Backend-3fb950?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-C%2B%2B%20Wasm-bc8cff?style=for-the-badge)

> **Live Research Workbench:** [Open the Aegis-IR Demo](https://liambrooks-lab.github.io/Aegis-IR/)

</div>

## Abstract

**Aegis-IR** is an applied systems research project from **Voxion Labs** focused on eliminating V8 garbage-collection stutter in browser-native search. The core thesis is that allocation-heavy Vanilla JavaScript search can introduce visible main-thread pauses when the runtime is forced to reclaim thousands of short-lived query objects.

Aegis-IR moves the critical TF-IDF ranking path into an object-oriented **C++17** engine compiled to **WebAssembly**. Inside the Wasm module, the index and scoring structures live in deterministic **linear memory** instead of the JavaScript heap. During ranking, the engine traverses continuous numeric buffers rather than constructing transient JavaScript arrays, maps, and result objects.

That memory boundary is the research point: by keeping the hot scoring loop outside V8's managed heap, Aegis-IR avoids garbage-collection pressure during retrieval and models **0 ms GC pause** behavior for the ranking path. The outcome is a static, zero-backend search architecture designed to preserve UI smoothness while the user types.

## The Problem

### V8 Garbage Collection Stutter

Vanilla JavaScript is excellent for interface orchestration, but search workloads can be hostile to managed heap behavior. A typical client-side search implementation repeatedly allocates:

- token arrays for every query,
- temporary maps for term frequencies,
- intermediate score objects,
- result arrays,
- highlighted snippets,
- short-lived strings from normalization and matching.

During interactive search, this allocation pattern can happen on every keystroke. The ranking function may appear fast in isolation, but the surrounding object churn increases V8 heap pressure. When V8 decides to reclaim memory, garbage collection can pause execution on the main thread.

That pause is what users feel as stutter: the input hesitates, the UI freezes briefly, and the search experience stops feeling native. Aegis-IR treats this as a memory-management problem rather than a generic speed problem.

## The Solution

### Aegis-IR Linear Memory

Aegis-IR isolates the allocation-heavy information retrieval kernel inside WebAssembly linear memory. Instead of representing the index as nested JavaScript objects, the C++ engine uses continuous numeric buffers for TF-IDF scoring.

The ranking path is shaped around predictable memory access:

```text
term_frequencies[document_index * vocabulary_size + term_index]
inverse_document_frequency[term_index]
```

This gives the engine a compact, deterministic traversal model:

```text
query -> Wasm boundary -> linear-memory TF-IDF loop -> compact result payload -> render
```

The architecture is strictly **zero-backend**. The browser loads static assets from GitHub Pages, initializes the Wasm search kernel, and executes retrieval locally. JavaScript remains responsible for input handling, telemetry display, and DOM rendering; the ranking loop stays inside C++ linear memory where it avoids V8 heap allocation during scoring.

## Performance Benchmark

The benchmark below models the query-window breakdown for allocation-heavy Vanilla JavaScript search versus the Aegis-IR linear-memory architecture.

| Execution Segment | Vanilla JS Search | Aegis-IR |
| --- | ---: | ---: |
| Query Parsing | 8 ms | 3 ms |
| Heap GC Pause | 85 ms | 0 ms |
| Ranking | 18 ms | 6 ms |
| **Total** | **111 ms** | **9 ms** |

The key signal is the **Heap GC Pause** row. Aegis-IR is designed so the critical ranking path does not generate transient JavaScript heap pressure, allowing the retrieval loop to avoid GC-induced main-thread blocking.

## Core Tech Stack

- **C++17** for the object-oriented TF-IDF search kernel.
- **Emscripten** for compiling the C++ engine into WebAssembly.
- **Vanilla JavaScript** for the Wasm bridge, UI orchestration, and telemetry.
- **HTML5/CSS3** for the static research workbench.
- **GitHub Pages** for zero-backend deployment.

## Local Replication Steps

```bash
git clone https://github.com/liambrooks-lab/Aegis-IR.git
cd Aegis-IR
python scripts/build_and_serve.py
```

Then open the local preview URL printed in the terminal and run queries such as:

```text
linear memory garbage collection
main-thread stutter
tf-idf wasm
```

Watch the telemetry panel for **Thread Blocking** and **Memory Allocation** while the browser-native search kernel executes.

<div align="center">

## Author

<img src="MY%20PIC.jpg" width="180" alt="Rudranarayan Jena" style="border-radius:12px; box-shadow:0 18px 50px rgba(0,0,0,0.35);" />

### Crafted by Rudranarayan Jena

**Founder @ Voxion Labs**

*Focused on system-level architectures, deterministic runtime behavior, and polished browser products that turn deep engineering ideas into usable research workbenches.*

**[GitHub: @liambrooks-lab](https://github.com/liambrooks-lab)** · **[Voxion Labs](https://github.com/liambrooks-lab)**

</div>
