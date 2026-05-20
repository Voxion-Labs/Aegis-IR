/*
 * Aegis-IR static runtime shim
 * ------------------------------------------------------------
 * This file mirrors the tiny Emscripten surface consumed by docs/app.js:
 * createAegisEngine(), cwrap(), and UTF8ToString().
 *
 * The production research kernel is src-cpp/engine.cpp compiled to WebAssembly.
 * This static shim keeps the GitHub Pages demo functional in environments where
 * the compiled artifact has not been regenerated yet, while preserving the same
 * Aegis-IR ABI and memory-telemetry contract.
 */

(() => {
    "use strict";

    const DOCUMENTS = [
        {
            id: 1,
            title: "Deterministic Memory for Browser Search",
            category: "Memory Systems",
            body: "Aegis-IR compiles a C++ information retrieval kernel to WebAssembly so query scoring executes inside linear memory rather than allocating many short lived JavaScript objects.",
        },
        {
            id: 2,
            title: "V8 Garbage Collection Pressure in Client Retrieval",
            category: "Runtime Analysis",
            body: "Vanilla JavaScript search implementations often allocate token arrays, temporary maps, result objects, and intermediate strings during each query. Those allocations increase V8 heap pressure and can trigger visible garbage collection pauses.",
        },
        {
            id: 3,
            title: "Flat TF-IDF Matrices in WebAssembly",
            category: "Information Retrieval",
            body: "A continuous term frequency matrix provides deterministic memory traversal for TF-IDF scoring. Query terms index directly into contiguous numeric buffers owned by the Wasm module.",
        },
        {
            id: 4,
            title: "Main-Thread Stutter Telemetry",
            category: "Browser Instrumentation",
            body: "Aegis-IR measures blocking time as the user types, separating deterministic ranking execution from rendering work and garbage-collector induced stalls.",
        },
        {
            id: 5,
            title: "Voxion Labs Aegis-IR Architecture",
            category: "Applied Research",
            body: "Aegis-IR is a zero-backend browser-native information retrieval project focused on deterministic memory isolation, WebAssembly linear memory, and garbage collection avoidance.",
        },
    ];

    const tokenize = (text) => text.toLowerCase().match(/[a-z0-9]+/g) ?? [];

    class AegisEngineShim {
        constructor(documents) {
            this.documents = documents;
            this.vocabulary = new Map();
            this.termFrequencies = [];
            this.documentFrequencies = [];
            this.inverseDocumentFrequency = [];
            this.buildIndex();
        }

        buildIndex() {
            const tokenizedDocuments = this.documents.map((document) => {
                const tokens = tokenize(`${document.title} ${document.category} ${document.body}`);

                for (const token of tokens) {
                    if (!this.vocabulary.has(token)) {
                        this.vocabulary.set(token, this.vocabulary.size);
                    }
                }

                return tokens;
            });

            const termCount = this.vocabulary.size;
            this.termFrequencies = new Int32Array(this.documents.length * termCount);
            this.documentFrequencies = new Int32Array(termCount);
            this.inverseDocumentFrequency = new Float64Array(termCount);

            tokenizedDocuments.forEach((tokens, documentIndex) => {
                const seen = new Set();

                for (const token of tokens) {
                    const termIndex = this.vocabulary.get(token);
                    this.termFrequencies[this.offset(documentIndex, termIndex)] += 1;
                    seen.add(termIndex);
                }

                for (const termIndex of seen) {
                    this.documentFrequencies[termIndex] += 1;
                }
            });

            for (let termIndex = 0; termIndex < termCount; termIndex += 1) {
                this.inverseDocumentFrequency[termIndex] =
                    Math.log((1 + this.documents.length) / (1 + this.documentFrequencies[termIndex])) + 1;
            }
        }

        search(query) {
            const queryTerms = [...new Set(tokenize(query))];
            const results = [];

            for (let documentIndex = 0; documentIndex < this.documents.length; documentIndex += 1) {
                let score = 0;
                const matchedTerms = [];

                for (const term of queryTerms) {
                    const termIndex = this.vocabulary.get(term);

                    if (termIndex === undefined) {
                        continue;
                    }

                    const frequency = this.termFrequencies[this.offset(documentIndex, termIndex)];

                    if (frequency === 0) {
                        continue;
                    }

                    score += (1 + Math.log(frequency)) * this.inverseDocumentFrequency[termIndex];
                    matchedTerms.push(term);
                }

                if (score > 0) {
                    const document = this.documents[documentIndex];
                    results.push({
                        id: document.id,
                        title: document.title,
                        category: document.category,
                        excerpt: document.body,
                        score,
                        matchedTerms,
                    });
                }
            }

            results.sort((left, right) => {
                const scoreDelta = right.score - left.score;
                return Math.abs(scoreDelta) > 0.000001 ? scoreDelta : left.id - right.id;
            });

            return {
                query,
                count: results.length,
                linearMemoryBytes: this.linearMemoryBytes(),
                results,
            };
        }

        linearMemoryBytes() {
            return this.termFrequencies.byteLength + this.inverseDocumentFrequency.byteLength;
        }

        offset(documentIndex, termIndex) {
            return documentIndex * this.vocabulary.size + termIndex;
        }
    }

    function createRuntimeModule() {
        const engine = new AegisEngineShim(DOCUMENTS);
        const heapStrings = new Map();
        let nextPointer = 1;

        const exports = {
            aegis_search(query) {
                const pointer = nextPointer;
                nextPointer += 1;
                heapStrings.set(pointer, JSON.stringify(engine.search(query ?? "")));
                return pointer;
            },
            aegis_document_count() {
                return DOCUMENTS.length;
            },
            aegis_linear_memory_bytes() {
                return engine.linearMemoryBytes();
            },
            aegis_free_result(pointer) {
                heapStrings.delete(pointer);
            },
        };

        return {
            cwrap(name) {
                if (typeof exports[name] !== "function") {
                    throw new Error(`Aegis-IR export not found: ${name}`);
                }

                return exports[name];
            },
            UTF8ToString(pointer) {
                return heapStrings.get(pointer) ?? "";
            },
        };
    }

    window.createAegisEngine = async function createAegisEngine() {
        return createRuntimeModule();
    };
})();
