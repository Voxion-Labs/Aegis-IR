# Aegis-IR Operational & Contribution Protocols

Aegis-IR operates under strict deterministic execution and memory isolation protocols. We do not accept arbitrary JavaScript wrappers, GC-heavy object allocations, or unoptimized C++ compilation targets. This repository is maintained for high-performance WebAssembly systems research.

If you intend to submit a Pull Request, you must adhere strictly to the following institutional directives.

## 1. Architectural Standards
All code submitted to Aegis-IR must meet our baseline performance metrics:
* **Zero GC Stutter:** Submissions introducing V8 garbage collection pressure during the ranking path will be instantly rejected. All TF-IDF scoring matrices must remain strictly within WebAssembly linear memory.
* **Deterministic Execution:** C++17 implementations must compile via Emscripten without bloating the Wasm binary. Prove your execution latency (sub-10ms total ranking time) via runtime telemetry before submission.
* **Memory Safety:** Manual memory management in the C++ kernel must be flawless. Memory leaks, out-of-bounds linear memory access, or buffer overflows are strictly prohibited.

## 2. Pull Request (PR) Governance
Before initiating a merge request, ensure your PR adheres to this exact structure:
1. **[METRIC] Benchmark Data:** You must provide before/after execution telemetry (e.g., Heap GC Pause, Total Ranking latency, Wasm binary payload size).
2. **[LOGIC] State Transition:** Explicitly document the deterministic memory access patterns your code alters within the C++ retrieval kernel.
3. **[ISOLATION] Threat Model:** Prove that no buffer overflows exist that could compromise the browser's execution sandbox.

*Note: PRs failing to provide empirical telemetry benchmarking will be closed immediately without review.*

## 3. Vulnerability Disclosure
**DO NOT** open public issues for out-of-bounds memory exploits, Wasm compilation vulnerabilities, or denial-of-service vectors. Public disclosure of system-level threats compromises the integrity of the research.
* All security reports must be routed internally.
* Contact the Lead Architect directly for secure transmission protocols.

## 4. Code of Conduct
We evaluate algorithmic determinism, not intentions. Your submissions will be scrutinized ruthlessly based on linear memory efficiency and C++ kernel optimization. Keep discussions clinical, objective, and exclusively focused on Wasm systems architecture.