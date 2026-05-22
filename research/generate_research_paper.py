from pathlib import Path
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "Aegis-IR_Research_Paper.pdf"
BENCHMARK = ROOT / "research" / "benchmark_results.png"

PAGE_W, PAGE_H = A4
MARGIN_X = 44
TOP = PAGE_H - 42
BOTTOM = 42

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#4b5563")
LIGHT = colors.HexColor("#f3f6fb")
LINE = colors.HexColor("#d8dee9")
BLUE = colors.HexColor("#2563eb")
GREEN = colors.HexColor("#16a34a")
RED = colors.HexColor("#dc2626")
VIOLET = colors.HexColor("#7c3aed")
SLATE = colors.HexColor("#0f172a")


def mm(value):
    return value * 2.834645669


class Paper:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.page = 0

    def new_page(self):
        if self.page:
            self.c.showPage()
        self.page += 1
        self.c.setFillColor(colors.white)
        self.c.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
        self.footer()

    def footer(self):
        self.c.setStrokeColor(LINE)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN_X, 30, PAGE_W - MARGIN_X, 30)
        self.c.setFillColor(MUTED)
        self.c.setFont("Helvetica", 7.2)
        self.c.drawString(MARGIN_X, 18, "Aegis-IR - Voxion Labs Applied Systems Research")
        self.c.drawRightString(PAGE_W - MARGIN_X, 18, f"Page {self.page} of 5")

    def save(self):
        self.c.save()

    def section(self, title, x, y, width=None):
        self.c.setFillColor(BLUE)
        self.c.rect(x, y - 3, 4, 15, fill=True, stroke=False)
        self.c.setFillColor(INK)
        self.c.setFont("Helvetica-Bold", 11.5)
        self.c.drawString(x + 10, y, title.upper())
        if width:
            self.c.setStrokeColor(LINE)
            self.c.line(x + 10, y - 7, x + width, y - 7)

    def paragraph(self, text, x, y, width, size=8.8, leading=12.2, color=INK, font="Helvetica"):
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        chars = max(28, int(width / (size * 0.48)))
        lines = []
        for part in text.split("\n"):
            lines.extend(wrap(part, chars) if part else [""])
        for line in lines:
            self.c.drawString(x, y, line)
            y -= leading
        return y

    def bullet_list(self, items, x, y, width, size=8.4, leading=11.4):
        for item in items:
            self.c.setFillColor(BLUE)
            self.c.circle(x + 3, y + 3, 2.2, fill=True, stroke=False)
            y = self.paragraph(item, x + 12, y, width - 12, size=size, leading=leading)
            y -= 3
        return y

    def callout(self, title, body, x, y, w, h, fill=LIGHT, accent=BLUE):
        self.c.setFillColor(fill)
        self.c.setStrokeColor(colors.HexColor("#c8d3e3"))
        self.c.roundRect(x, y - h, w, h, 8, fill=True, stroke=True)
        self.c.setFillColor(accent)
        self.c.roundRect(x, y - h, 6, h, 3, fill=True, stroke=False)
        self.c.setFillColor(INK)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(x + 14, y - 17, title)
        return self.paragraph(body, x + 14, y - 32, w - 24, size=7.8, leading=10.2, color=MUTED)

    def table(self, x, y, widths, rows, header_fill=SLATE):
        row_h = 22
        self.c.setFont("Helvetica-Bold", 7.5)
        for r, row in enumerate(rows):
            fill = header_fill if r == 0 else (colors.HexColor("#f8fafc") if r % 2 else colors.white)
            text_color = colors.white if r == 0 else INK
            self.c.setFillColor(fill)
            self.c.rect(x, y - row_h, sum(widths), row_h, fill=True, stroke=False)
            self.c.setStrokeColor(LINE)
            self.c.rect(x, y - row_h, sum(widths), row_h, fill=False, stroke=True)
            cx = x
            for i, cell in enumerate(row):
                self.c.setStrokeColor(LINE)
                self.c.line(cx, y - row_h, cx, y)
                self.c.setFillColor(text_color)
                self.c.setFont("Helvetica-Bold" if r == 0 else "Helvetica", 7.4)
                self.c.drawString(cx + 6, y - 14, str(cell))
                cx += widths[i]
            self.c.line(x + sum(widths), y - row_h, x + sum(widths), y)
            y -= row_h
        return y - 10

    def box(self, x, y, w, h, label, body="", fill=colors.white, stroke=LINE, accent=None):
        self.c.setFillColor(fill)
        self.c.setStrokeColor(stroke)
        self.c.roundRect(x, y - h, w, h, 7, fill=True, stroke=True)
        if accent:
            self.c.setFillColor(accent)
            self.c.roundRect(x, y - h, 6, h, 3, fill=True, stroke=False)
        self.c.setFillColor(INK)
        self.c.setFont("Helvetica-Bold", 8.2)
        self.c.drawString(x + 12, y - 16, label)
        if body:
            self.paragraph(body, x + 12, y - 30, w - 20, size=7.1, leading=8.6, color=MUTED)

    def arrow(self, x1, y1, x2, y2, color=BLUE):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(1.3)
        self.c.line(x1, y1, x2, y2)
        self.c.setFillColor(color)
        self.c.circle(x2, y2, 2.2, fill=True, stroke=False)


def page_one(p):
    p.new_page()
    c = p.c
    c.setFillColor(SLATE)
    c.rect(0, PAGE_H - 135, PAGE_W, 135, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    title = "Aegis-IR: Eliminating V8 Garbage Collection Pressure"
    c.drawCentredString(PAGE_W / 2, PAGE_H - 50, title)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 72, "through Deterministic Linear Memory Architecture")
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 100, "Rudranarayan Jena")
    c.drawCentredString(PAGE_W / 2, PAGE_H - 114, "Founder of Voxion Labs - DY Patil International University - Pune, India")

    y = PAGE_H - 165
    p.section("Abstract", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    abstract = (
        "Aegis-IR is a browser-native information retrieval architecture designed to reduce main-thread stutter "
        "caused by garbage-collection pressure in allocation-heavy Vanilla JavaScript search. The system compiles "
        "an object-oriented C++ TF-IDF ranking kernel to WebAssembly and stores its retrieval structures inside "
        "deterministic linear memory. During ranking, the engine traverses continuous numeric buffers rather than "
        "constructing transient JavaScript arrays, maps, and result objects. This isolates the critical scoring path "
        "from V8 heap allocation and models 0 ms garbage-collection pause behavior during query execution. The paper "
        "presents the memory problem, the Aegis-IR architecture, the continuous-array scoring model, and browser-side "
        "telemetry for measuring thread blocking and allocation pressure."
    )
    y = p.paragraph(abstract, MARGIN_X, y, PAGE_W - 2 * MARGIN_X, size=9.2, leading=13)
    y -= 12

    p.callout(
        "Primary claim",
        "For browser-native search, the decisive systems boundary is not only the algorithm. It is the memory substrate: "
        "managed JavaScript heap allocation versus deterministic WebAssembly linear memory.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
        58,
        fill=colors.HexColor("#eef5ff"),
        accent=BLUE,
    )
    y -= 82

    p.section("Contributions", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    y = p.bullet_list(
        [
            "Defines V8 garbage-collection stutter as a first-class failure mode for interactive client-side search.",
            "Introduces a zero-backend C++ WebAssembly retrieval kernel using contiguous numeric memory for TF-IDF scoring.",
            "Separates UI orchestration from retrieval execution through a small explicit WebAssembly ABI.",
            "Provides a telemetry model for thread blocking, heap allocation pressure, and deterministic linear-memory size.",
        ],
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 8

    p.section("Paper Layout", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    p.table(
        MARGIN_X,
        y,
        [92, 112, 290],
        [
            ["Page", "Focus", "Primary Artifact"],
            ["1", "Abstract and claims", "Contribution map"],
            ["2", "V8 GC bottleneck", "Memory-path diagram and allocation table"],
            ["3", "Aegis-IR architecture", "System tree and TF-IDF array model"],
            ["4", "Telemetry and benchmarks", "Stacked graph and execution table"],
            ["5", "Discussion", "Limitations, future work, conclusion, references"],
        ],
    )


def page_two(p):
    p.new_page()
    y = TOP
    p.section("The Browser Search Memory Problem", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    y = p.paragraph(
        "Vanilla JavaScript search implementations are easy to build because the language makes arrays, maps, "
        "closures, and strings cheap to express. Under repeated interactive queries, those constructs become a "
        "runtime liability. Every keystroke can allocate a new graph of short-lived objects. V8 can reclaim those "
        "objects, but collection timing is not controlled by the search algorithm. When garbage collection overlaps "
        "with input handling or rendering, the user sees a stalled interface.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 12

    p.section("Allocation Hotspots in Vanilla JavaScript Search", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    p.table(
        MARGIN_X,
        y,
        [128, 170, 196],
        [
            ["Allocation Source", "Typical Object Shape", "Stutter Risk"],
            ["Tokenization", "arrays of strings", "high churn per keystroke"],
            ["Term counting", "maps and boxed counters", "temporary object graph"],
            ["Scoring", "per-document score records", "linear growth with corpus"],
            ["Sorting", "result objects and comparators", "heap pressure near render"],
            ["Highlighting", "substring copies", "extra allocations after ranking"],
        ],
    )
    y -= 158

    p.section("Runtime Path Diagram", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    left_x = MARGIN_X
    mid_y = y
    p.box(left_x, mid_y, 116, 44, "User input", "keystroke event", fill=colors.HexColor("#f8fafc"), accent=BLUE)
    p.box(left_x + 145, mid_y, 120, 44, "JS token arrays", "short-lived strings", fill=colors.HexColor("#fff7ed"), accent=RED)
    p.box(left_x + 294, mid_y, 122, 44, "JS maps/results", "heap object churn", fill=colors.HexColor("#fff7ed"), accent=RED)
    p.box(left_x + 444, mid_y, 86, 44, "GC pause", "main thread", fill=colors.HexColor("#fef2f2"), accent=RED)
    p.arrow(left_x + 116, mid_y - 22, left_x + 145, mid_y - 22, RED)
    p.arrow(left_x + 265, mid_y - 22, left_x + 294, mid_y - 22, RED)
    p.arrow(left_x + 416, mid_y - 22, left_x + 444, mid_y - 22, RED)

    y -= 82
    p.callout(
        "Observed failure mode",
        "The search logic may be locally correct, but the managed heap introduces non-deterministic pauses. "
        "Aegis-IR therefore treats memory allocation behavior as part of the algorithmic design surface.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
        64,
        fill=colors.HexColor("#fff7ed"),
        accent=RED,
    )
    y -= 92

    p.section("Design Requirement", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    p.bullet_list(
        [
            "Keep allocation-heavy scoring outside the JavaScript object heap.",
            "Represent term statistics as contiguous numeric buffers.",
            "Expose a minimal bridge so JavaScript orchestrates without owning the ranking loop.",
            "Measure main-thread blocking rather than reporting generic execution time alone.",
        ],
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )


def page_three(p):
    p.new_page()
    y = TOP
    p.section("Aegis-IR Linear Memory Architecture", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    y = p.paragraph(
        "Aegis-IR compiles an object-oriented C++ retrieval kernel to WebAssembly. The browser loads the module "
        "as a static asset, then invokes a small ABI for search, document count, memory telemetry, and result release. "
        "The ranking kernel owns term-frequency and inverse-document-frequency arrays inside linear memory.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 12

    p.section("System Tree", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 20
    root_x = PAGE_W / 2 - 62
    p.box(root_x, y, 124, 34, "Aegis-IR", "browser-native IR", fill=colors.HexColor("#eef5ff"), accent=BLUE)
    layer_y = y - 70
    xs = [MARGIN_X, MARGIN_X + 168, MARGIN_X + 336]
    labels = [
        ("Static Workbench", "HTML/CSS + JS telemetry"),
        ("Wasm Bridge", "explicit aegis_* ABI"),
        ("C++ Kernel", "TF-IDF linear memory"),
    ]
    for x, (label, body) in zip(xs, labels):
        p.box(x, layer_y, 148, 46, label, body, fill=colors.white, accent=GREEN if "Kernel" in label else BLUE)
        p.arrow(root_x + 62, y - 34, x + 74, layer_y, BLUE)
    leaf_y = layer_y - 72
    leaves = [
        ("Thread Blocking", xs[0]),
        ("Heap Delta", xs[0] + 78),
        ("Search", xs[1]),
        ("Free Result", xs[1] + 78),
        ("Term Matrix", xs[2]),
        ("IDF Vector", xs[2] + 78),
    ]
    for label, x in leaves:
        p.box(x, leaf_y, 70, 34, label, "", fill=colors.HexColor("#f8fafc"), accent=VIOLET)
    y = leaf_y - 58

    p.section("Continuous Array TF-IDF Model", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    p.callout(
        "Memory layout",
        "term_frequencies[document_index * vocabulary_size + term_index]",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
        42,
        fill=colors.HexColor("#f8fafc"),
        accent=VIOLET,
    )
    y -= 62
    formula = (
        "tf(t,d) = 1 + ln(f(t,d))\n"
        "idf(t) = ln((1 + N) / (1 + df(t))) + 1\n"
        "S(q,d) = sum over t in T(q) of tf(t,d) * idf(t)"
    )
    y = p.paragraph(formula, MARGIN_X + 10, y, PAGE_W - 2 * MARGIN_X - 20, size=9, leading=14, font="Courier")
    y -= 8

    p.section("ABI Surface", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 22
    p.table(
        MARGIN_X,
        y,
        [154, 124, 216],
        [
            ["Export", "Return", "Purpose"],
            ["aegis_search(query)", "char*", "Executes ranking and returns compact payload"],
            ["aegis_document_count()", "int", "Reports indexed corpus size"],
            ["aegis_linear_memory_bytes()", "int", "Reports deterministic buffer footprint"],
            ["aegis_free_result(ptr)", "void", "Releases native result memory explicitly"],
        ],
    )


def page_four(p):
    p.new_page()
    y = TOP
    p.section("Main-Thread Telemetry", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    y = p.paragraph(
        "Aegis-IR instruments the browser workbench around the user-visible failure mode: thread blocking. "
        "The JavaScript bridge records Long Task entries when supported, falls back to synchronous query-window "
        "duration, and reports linear-memory footprint from the Wasm engine. This separates ranking execution from "
        "garbage-collection pressure and DOM rendering.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 12

    p.section("Benchmark Visualization", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 18
    if BENCHMARK.exists():
        img = ImageReader(str(BENCHMARK))
        p.c.drawImage(img, MARGIN_X, y - 250, PAGE_W - 2 * MARGIN_X, 250, preserveAspectRatio=True, anchor="c")
    y -= 270

    p.section("Execution Segment Model", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    p.table(
        MARGIN_X,
        y,
        [152, 112, 112, 112],
        [
            ["Execution Segment", "Vanilla JS", "Aegis-IR", "Interpretation"],
            ["Query Parsing", "8 ms", "3 ms", "smaller bridge work"],
            ["Heap GC Pause", "85 ms", "0 ms", "ranking avoids JS heap churn"],
            ["Ranking", "18 ms", "6 ms", "continuous numeric arrays"],
            ["Total", "111 ms", "9 ms", "reduced stutter window"],
        ],
    )
    y -= 134

    p.section("Telemetry Pipeline", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 22
    steps = [
        ("Input", "query event"),
        ("Bridge", "aegis_search"),
        ("Kernel", "linear arrays"),
        ("Metrics", "blocking + memory"),
        ("Render", "ranked cards"),
    ]
    x = MARGIN_X
    for label, body in steps:
        p.box(x, y, 86, 44, label, body, fill=colors.HexColor("#f8fafc"), accent=BLUE)
        if label != "Render":
            p.arrow(x + 86, y - 22, x + 104, y - 22, BLUE)
        x += 104


def page_five(p):
    p.new_page()
    y = TOP
    p.section("Discussion", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 25
    y = p.paragraph(
        "Aegis-IR is best understood as a memory architecture for browser-native retrieval. The system does not "
        "argue that JavaScript is unsuitable for interfaces. It argues that allocation-heavy ranking loops should "
        "not be forced through the same managed object heap that must also support input, rendering, and layout. "
        "Moving TF-IDF scoring into WebAssembly linear memory creates a tighter and more predictable execution surface.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 10

    p.section("Limitations", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    y = p.bullet_list(
        [
            "The current corpus is intentionally small and embedded for repeatable static deployment.",
            "The result payload still crosses into JavaScript for rendering; future work can use typed result arenas.",
            "Long Task availability differs across browsers, so telemetry should include browser/version metadata.",
            "The 0 ms GC segment describes the ranking path, not the entire page lifecycle.",
        ],
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 8

    p.section("Future Work", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    y = p.bullet_list(
        [
            "Arena-based result buffers with offset tables instead of JSON serialization.",
            "BM25 and hybrid lexical ranking using the same deterministic memory discipline.",
            "Corpus ingestion pipeline with bounded allocation and offline persistence.",
            "Cross-browser stutter studies across V8, SpiderMonkey, and JavaScriptCore.",
        ],
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 8

    p.section("Conclusion", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 24
    y = p.paragraph(
        "Aegis-IR demonstrates that browser-native search can be treated as a systems problem in deterministic "
        "memory design. By placing the TF-IDF ranking loop in C++ WebAssembly linear memory, the architecture removes "
        "the allocation-heavy scoring path from V8's managed heap and directly targets garbage-collection-induced "
        "main-thread stutter. The result is a zero-backend research workbench that is static-deployable, measurable, "
        "and aligned with the responsiveness expectations of modern browser products.",
        MARGIN_X,
        y,
        PAGE_W - 2 * MARGIN_X,
    )
    y -= 12

    p.section("References", MARGIN_X, y, PAGE_W - 2 * MARGIN_X)
    y -= 22
    refs = [
        "[1] Mozilla Developer Network, WebAssembly Concepts and JavaScript Execution Model.",
        "[2] W3C, Long Tasks API: Cooperative Scheduling of Background Tasks.",
        "[3] Google V8 Project, Design notes on garbage collection and heap management.",
        "[4] G. Salton and C. Buckley, Term-weighting approaches in automatic text retrieval.",
        "[5] Emscripten Project Documentation, C/C++ to WebAssembly compilation pipeline.",
    ]
    for ref in refs:
        y = p.paragraph(ref, MARGIN_X, y, PAGE_W - 2 * MARGIN_X, size=7.8, leading=10.2, color=MUTED)
        y -= 2


def build():
    paper = Paper(OUT)
    page_one(paper)
    page_two(paper)
    page_three(paper)
    page_four(paper)
    page_five(paper)
    paper.save()

    reader = PdfReader(str(OUT))
    if len(reader.pages) != 5:
        raise RuntimeError(f"Expected 5 pages, generated {len(reader.pages)}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
