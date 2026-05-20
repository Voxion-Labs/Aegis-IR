from pathlib import Path

import matplotlib.pyplot as plt


OUTPUT_PATH = Path(__file__).with_name("benchmark_results.png")

SYSTEMS = [
    "Vanilla JavaScript Search",
    "Aegis-IR (Wasm Linear Memory)",
]

QUERY_PARSING_MS = [8, 3]
HEAP_GC_MS = [85, 0]
RANKING_EXECUTION_MS = [18, 6]

SEGMENTS = [
    ("Query Parsing", QUERY_PARSING_MS, "#58a6ff"),
    ("Heap Allocation / GC Pause", HEAP_GC_MS, "#f85149"),
    ("Ranking Execution", RANKING_EXECUTION_MS, "#3fb950"),
]


def main():
    plt.style.use("dark_background")

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=180)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    y_positions = range(len(SYSTEMS))
    left_offsets = [0 for _ in SYSTEMS]

    for label, values, color in SEGMENTS:
        ax.barh(
            y_positions,
            values,
            left=left_offsets,
            height=0.46,
            label=label,
            color=color,
            edgecolor="#0d1117",
            linewidth=1.2,
        )

        for index, value in enumerate(values):
            if value <= 0:
                continue

            ax.text(
                left_offsets[index] + value / 2,
                index,
                f"{value} ms",
                va="center",
                ha="center",
                fontsize=10,
                fontweight="bold",
                color="#ffffff",
            )

        left_offsets = [left + value for left, value in zip(left_offsets, values)]

    ax.set_title(
        "Aegis-IR Main-Thread Stutter Model",
        fontsize=22,
        fontweight="bold",
        color="#f0f6fc",
        pad=24,
    )
    ax.set_xlabel("Query Window Breakdown (ms)", fontsize=12, color="#c9d1d9", labelpad=12)
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(SYSTEMS, fontsize=12, color="#f0f6fc")
    ax.invert_yaxis()

    ax.grid(axis="x", color="#30363d", linewidth=0.9, alpha=0.75)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors="#8b949e", labelsize=10)
    ax.tick_params(axis="y", colors="#f0f6fc", labelsize=12)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#30363d")

    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.23),
        ncol=3,
        frameon=False,
        fontsize=10,
        labelcolor="#c9d1d9",
    )

    ax.text(
        0.5,
        1.02,
        "Linear memory removes the allocation-heavy GC pause segment from the ranking path.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=11,
        color="#8b949e",
    )

    ax.text(
        0.5,
        -0.32,
        "Illustrative research model for browser-native search memory behavior. Replace with measured medians and tail values for formal experiments.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color="#8b949e",
    )

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"Saved Aegis-IR stutter graph to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
