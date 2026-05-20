# Aegis-IR: Deterministic Linear Memory for Browser-Native Information Retrieval

**Author:** Rudranarayan Jena, Founder @ Voxion Labs  
**Project:** Aegis-IR  
**Organization:** Voxion Labs  
**Research Type:** Applied Systems Research  
**Thesis:** Deterministic Memory vs. Garbage Collection: Eliminating Main-Thread Stutter in Browser-Native Search

![Main-thread memory behavior comparison for browser-native search](benchmark_results.png)

## Abstract

Aegis-IR is a browser-native information retrieval system designed around deterministic memory behavior. The project investigates a specific systems problem in client-side search: allocation-heavy Vanilla JavaScript implementations can create large volumes of short-lived strings, arrays, maps, and result objects during tokenization, index traversal, and scoring. Those allocations increase pressure on the V8 JavaScript heap. Under enough pressure, V8 must reclaim memory through garbage collection, and that reclamation can pause execution on the main thread long enough for users to perceive stutter.

Aegis-IR moves the ranking kernel into C++ compiled to WebAssembly. The engine stores its index and scoring structures inside WebAssembly linear memory rather than the JavaScript object heap. JavaScript remains responsible for orchestration and rendering, but the allocation-intensive retrieval path is isolated inside a deterministic numeric memory region. This design does not claim that all browser work becomes free of pauses. It makes a narrower and more important systems claim: the TF-IDF scoring loop can run without generating the transient JavaScript heap objects that commonly trigger garbage-collection pressure in Vanilla JavaScript search.

The result is a zero-backend, static-deployable research architecture for information retrieval in the browser. Its primary metric is not generic speed. Its primary metric is main-thread blocking behavior under repeated interactive queries.

## The V8 Garbage Collection Bottleneck

Vanilla JavaScript is productive and expressive, but the JavaScript heap is managed by a garbage collector. That memory model is usually a strength. In search workloads, however, it can become unpredictable when the query path repeatedly allocates temporary objects.

A typical client-side search implementation may allocate:

- normalized query strings,
- token arrays,
- per-document temporary score objects,
- maps for term counts,
- intermediate result arrays,
- sorted result objects,
- highlighted snippets,
- transient closures and iterator state.

For small interactions, these allocations may be invisible. For repeated queries over larger corpora, every keystroke can create a burst of short-lived objects. V8 can reclaim those objects efficiently, but the timing of collection is not directly controlled by the application. A query may complete quickly many times and then stutter when garbage collection intersects with user input, rendering, or layout.

This is the central bottleneck Aegis-IR targets: not the mathematical cost of ranking alone, but the runtime behavior of allocation-heavy ranking on the JavaScript heap.

The problem can be summarized as:

```text
Vanilla JavaScript search:
query -> tokenize -> allocate objects -> rank -> allocate results -> GC pressure -> possible main-thread pause

Aegis-IR:
query -> bridge -> linear-memory scoring -> compact result payload -> render
```

The difference is the memory substrate. Vanilla JavaScript relies on a managed object heap. Aegis-IR places the hot retrieval structures inside WebAssembly linear memory, where the engine can traverse preallocated contiguous buffers without creating a new graph of JavaScript objects during scoring.

## WebAssembly Linear Memory Isolation

WebAssembly exposes a flat, byte-addressable linear memory region to compiled modules. For Aegis-IR, this linear memory block acts as a deterministic execution surface for the retrieval kernel.

In the browser, JavaScript and WebAssembly coexist, but their memory models are different:

| Layer | Memory Model | Role in Aegis-IR |
| --- | --- | --- |
| Vanilla JavaScript | V8-managed object heap | UI orchestration, event handling, rendering |
| C++ WebAssembly | Explicit linear memory | token statistics, TF-IDF buffers, scoring loop |

This separation is the core of the architecture. JavaScript sends the query across the Wasm boundary. The search engine performs ranking over C++-owned data structures. JavaScript then receives a compact result payload for display.

The engine deliberately keeps the scoring loop away from JavaScript object allocation. Internally, document-term statistics are represented as numeric buffers. The scoring loop reads integers and doubles from contiguous memory and accumulates floating-point scores. Because the hot path does not create JavaScript arrays or maps, it avoids adding avoidable pressure to V8's garbage collector.

The current exported surface is intentionally small:

```cpp
extern "C" char* aegis_search(const char* query);
extern "C" int aegis_document_count();
extern "C" int aegis_linear_memory_bytes();
extern "C" void aegis_free_result(char* result);
```

The explicit free function is important. It makes ownership visible at the JavaScript/WebAssembly boundary and prevents accidental accumulation of result buffers. In future phases, the JSON result payload can be replaced by a preallocated result arena or typed offset table to reduce bridge allocations even further.

## TF-IDF Continuous Array Implementation

Aegis-IR uses TF-IDF as a clear, inspectable information retrieval model. The research focus is memory behavior, so the ranking model is intentionally simple enough to audit.

Let:

- \(D\) be the document corpus.
- \(N = |D|\) be the document count.
- \(V\) be the normalized vocabulary.
- \(q\) be the user query.
- \(T(q)\) be the set of unique normalized query terms.
- \(f(t, d)\) be the frequency of term \(t\) in document \(d\).
- \(\operatorname{df}(t)\) be the number of documents containing term \(t\).

The term frequency component is:

```math
\operatorname{tf}(t, d) = 1 + \ln(f(t, d))
```

The inverse document frequency component is:

```math
\operatorname{idf}(t) =
\ln\left(\frac{1 + N}{1 + \operatorname{df}(t)}\right) + 1
```

The document score is:

```math
S(q, d) =
\sum_{t \in T(q)}
\operatorname{tf}(t, d) \cdot \operatorname{idf}(t)
```

The important implementation detail is the memory layout. Instead of representing every document as nested JavaScript objects, Aegis-IR flattens term statistics into a continuous matrix:

```text
term_frequencies[document_index * vocabulary_size + term_index]
```

This gives the scoring loop a deterministic access pattern:

```text
for each document:
    for each query term:
        offset = document_index * vocabulary_size + term_index
        frequency = term_frequencies[offset]
        score += log_scaled_tf(frequency) * inverse_document_frequency[term_index]
```

The supporting IDF values are stored in a parallel continuous array:

```text
inverse_document_frequency[term_index]
```

This design matters because array traversal over numeric WebAssembly memory has different runtime behavior from repeated construction of JavaScript object graphs. The retrieval loop becomes predictable: integer reads, floating-point reads, arithmetic, and a bounded result write. That is the Aegis-IR thesis in implementation form.

## Main-Thread Telemetry

Aegis-IR measures interactive responsiveness through main-thread blocking signals rather than only reporting raw query duration.

The browser UI records:

- **Thread Blocking:** blocking time associated with Long Task entries during the query window, with synchronous call duration used as a fallback signal.
- **Memory Allocation:** the size of the WebAssembly-owned linear-memory buffers and, when available, the observed JavaScript heap delta around the query call.
- **Corpus:** the number of documents indexed by the Aegis-IR engine.

The graph below is generated by `generate_graph.py`. It compares the conceptual query-time breakdown between an allocation-heavy Vanilla JavaScript search implementation and the Aegis-IR linear-memory model.

| System | Query Parsing | Heap Allocation / GC Pause | Ranking Execution |
| --- | ---: | ---: | ---: |
| Vanilla JavaScript Search | 8 ms | 85 ms | 18 ms |
| Aegis-IR (Wasm Linear Memory) | 3 ms | 0 ms | 6 ms |

The values are illustrative research defaults used to visualize the memory-management hypothesis. Formal runs should collect medians and tail values across repeated keystroke-driven queries, with corpus size, browser version, device class, and WebAssembly build flags recorded.

The key interpretation is not that WebAssembly removes all browser work. Rendering still happens in JavaScript. Result display still allocates DOM nodes. The point is narrower: the allocation-heavy scoring loop is isolated from V8's managed object heap. That isolation reduces the chance that ranking itself becomes the source of garbage-collection-induced main-thread stutter.

## Conclusion

Aegis-IR reframes browser-native search as a memory-management problem. Vanilla JavaScript search is simple to write, but repeated tokenization and ranking can create unpredictable heap pressure. C++ compiled to WebAssembly provides a different substrate: flat linear memory, explicit ownership, contiguous numeric buffers, and deterministic traversal.

For Voxion Labs, Aegis-IR establishes a research foundation for information retrieval systems that are static-deployable, zero-backend, and optimized for UI smoothness under interactive query workloads. The project is not a generic benchmark race. It is an investigation into whether deterministic memory isolation can make browser-native retrieval feel stable at the exact moment users notice instability: while they type.
