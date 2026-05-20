(() => {
    "use strict";

    const SELECTORS = {
        form: "#search-form",
        input: "#search-input",
        button: "#search-button",
        results: "#results",
        blocking: "#thread-blocking",
        allocation: "#memory-allocation",
        documentCount: "#document-count",
        status: "#engine-status",
        statusLabel: "#engine-status-label",
    };

    const LONG_TASK_THRESHOLD_MS = 50;

    const state = {
        module: null,
        search: null,
        freeResult: null,
        documentCount: null,
        linearMemoryBytes: null,
        longTasks: [],
    };

    const elements = Object.fromEntries(
        Object.entries(SELECTORS).map(([key, selector]) => [key, document.querySelector(selector)])
    );

    document.addEventListener("DOMContentLoaded", initialize);

    async function initialize() {
        observeMainThreadStutter();
        setEngineState("loading", "Initializing Aegis-IR linear memory");

        try {
            state.module = await loadAegisModule();
            bindNativeFunctions(state.module);
            enableWorkbench();
            runSearch("linear memory garbage collection");
        } catch (error) {
            console.error("Aegis-IR initialization failed:", error);
            setEngineState("error", "Aegis-IR runtime unavailable");
            renderEmptyState("The Aegis-IR WebAssembly runtime could not be loaded.");
        }
    }

    async function loadAegisModule() {
        if (typeof window.createAegisEngine === "function") {
            return window.createAegisEngine({
                locateFile: (path) => path.endsWith(".wasm") ? `./${path}` : path,
            });
        }

        if (typeof window.Module === "function") {
            return window.Module({
                locateFile: (path) => path.endsWith(".wasm") ? `./${path}` : path,
            });
        }

        if (typeof window.Module === "object" && window.Module !== null) {
            if (window.Module.ready instanceof Promise) {
                await window.Module.ready;
            }

            return window.Module;
        }

        throw new Error("No Aegis-IR module factory was found.");
    }

    function bindNativeFunctions(module) {
        if (typeof module.cwrap !== "function") {
            throw new Error("The Aegis-IR runtime must expose cwrap.");
        }

        state.search = module.cwrap("aegis_search", "number", ["string"]);
        state.freeResult = module.cwrap("aegis_free_result", null, ["number"]);
        state.documentCount = module.cwrap("aegis_document_count", "number", []);
        state.linearMemoryBytes = module.cwrap("aegis_linear_memory_bytes", "number", []);
    }

    function enableWorkbench() {
        elements.input.disabled = false;
        elements.button.disabled = false;
        elements.documentCount.textContent = `${state.documentCount()} docs`;
        elements.allocation.textContent = formatBytes(state.linearMemoryBytes());
        setEngineState("ready", "Aegis-IR linear memory online");

        elements.form.addEventListener("submit", (event) => {
            event.preventDefault();
            runSearch(elements.input.value);
        });

        elements.input.addEventListener("input", debounce(() => {
            runSearch(elements.input.value);
        }, 120));
    }

    function observeMainThreadStutter() {
        if (!("PerformanceObserver" in window)) {
            return;
        }

        try {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    state.longTasks.push({
                        startTime: entry.startTime,
                        duration: entry.duration,
                    });
                }

                if (state.longTasks.length > 200) {
                    state.longTasks.splice(0, state.longTasks.length - 200);
                }
            });

            observer.observe({ entryTypes: ["longtask"] });
        } catch (_error) {
            // Long Task telemetry is not available in every browser. The query
            // still runs; the UI falls back to direct synchronous call duration.
        }
    }

    function runSearch(rawQuery) {
        const query = rawQuery.trim();

        if (!query) {
            elements.blocking.textContent = "0.000 ms";
            elements.allocation.textContent = formatBytes(state.linearMemoryBytes());
            renderEmptyState("Enter a query to inspect Aegis-IR's deterministic memory path.");
            return;
        }

        let resultPointer = 0;
        const windowStart = performance.now();
        const heapBefore = readJsHeapUsage();

        try {
            resultPointer = state.search(query);
            const payload = JSON.parse(state.module.UTF8ToString(resultPointer));
            const elapsed = performance.now() - windowStart;
            const heapAfter = readJsHeapUsage();

            const longTaskBlocking = blockingTimeBetween(windowStart, performance.now());
            const directBlocking = Math.max(0, elapsed - LONG_TASK_THRESHOLD_MS);
            const blockingTime = Math.max(longTaskBlocking, directBlocking);
            const heapDelta = heapBefore === null || heapAfter === null ? 0 : Math.max(0, heapAfter - heapBefore);

            elements.blocking.textContent = `${blockingTime.toFixed(3)} ms`;
            elements.allocation.textContent = heapDelta > 0
                ? `${formatBytes(payload.linearMemoryBytes)} linear / ${formatBytes(heapDelta)} JS delta`
                : `${formatBytes(payload.linearMemoryBytes)} linear / GC-neutral`;

            renderResults(payload.results);
        } catch (error) {
            console.error("Aegis-IR query failed:", error);
            renderEmptyState("Aegis-IR query execution failed. Check the console for runtime details.");
        } finally {
            if (resultPointer !== 0) {
                state.freeResult(resultPointer);
            }
        }
    }

    function blockingTimeBetween(start, end) {
        return state.longTasks.reduce((total, task) => {
            const taskEnd = task.startTime + task.duration;
            const overlapsWindow = task.startTime < end && taskEnd > start;

            if (!overlapsWindow) {
                return total;
            }

            return total + Math.max(0, task.duration - LONG_TASK_THRESHOLD_MS);
        }, 0);
    }

    function readJsHeapUsage() {
        if (performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)) {
            return performance.memory.usedJSHeapSize;
        }

        return null;
    }

    function renderResults(results) {
        if (!Array.isArray(results) || results.length === 0) {
            renderEmptyState("No documents matched the current query.");
            return;
        }

        const fragment = document.createDocumentFragment();

        for (const result of results) {
            const card = document.createElement("article");
            card.className = "result-card";

            const meta = document.createElement("div");
            meta.className = "result-meta";

            const category = document.createElement("span");
            category.textContent = result.category;

            const score = document.createElement("span");
            score.className = "score";
            score.textContent = `tf-idf ${Number(result.score).toFixed(4)}`;

            meta.append(category, score);

            const title = document.createElement("h2");
            title.className = "result-title";
            title.textContent = result.title;

            const excerpt = document.createElement("p");
            excerpt.className = "result-excerpt";
            excerpt.textContent = result.excerpt;

            const terms = document.createElement("div");
            terms.className = "terms";
            terms.setAttribute("aria-label", "Matched query terms");

            for (const matchedTerm of result.matchedTerms) {
                const badge = document.createElement("span");
                badge.className = "term";
                badge.textContent = matchedTerm;
                terms.appendChild(badge);
            }

            card.append(meta, title, excerpt, terms);
            fragment.appendChild(card);
        }

        elements.results.replaceChildren(fragment);
    }

    function renderEmptyState(message) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = message;
        elements.results.replaceChildren(empty);
    }

    function setEngineState(status, label) {
        elements.status.dataset.ready = String(status === "ready");
        elements.statusLabel.textContent = label;
    }

    function formatBytes(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return "0 B";
        }

        if (bytes < 1024) {
            return `${bytes} B`;
        }

        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    function debounce(callback, waitMs) {
        let timeoutId = 0;

        return (...args) => {
            window.clearTimeout(timeoutId);
            timeoutId = window.setTimeout(() => callback(...args), waitMs);
        };
    }
})();
