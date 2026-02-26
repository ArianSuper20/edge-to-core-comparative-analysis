"""
Convert harness JSON results into Tipping Point graphs.
Reads processed_results.json or perf_run_*.json from results/ (or a given path).
Uses only stdlib + matplotlib (no polars).
"""
import json
import os
import glob
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt


def load_result_json(path: str) -> dict:
    """Load a single harness result JSON."""
    with open(path, "r") as f:
        return json.load(f)


def find_result_jsons(path: str) -> list[str]:
    """
    Resolve path to a list of JSON paths.
    - If path is a file: return [path] if it's .json
    - If path is a dir: return [processed_results.json] or sorted perf_run_*.json
    """
    p = Path(path)
    if p.is_file():
        return [str(p)] if p.suffix.lower() == ".json" else []
    if not p.is_dir():
        return []
    single = p / "processed_results.json"
    if single.exists():
        return [str(single)]
    return sorted(glob.glob(str(p / "perf_run_*.json")))


def _mean_std(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return mean, variance ** 0.5


def results_to_tables(jsons: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """
    Convert list of result dicts into capability and efficiency tables (list of dicts).
    Multiple runs are aggregated (mean ± std). Returns (cap_data, eff_data, metadata).
    """
    cap_rows = []
    eff_rows = []
    meta = jsons[0].get("metadata", {}) if jsons else {}

    for j in jsons:
        for row in j.get("capability_sweep", []):
            cap_rows.append(row)
        for row in j.get("efficiency_sweep", []):
            eff_rows.append(row)

    cap_data = []
    if cap_rows:
        by_threads = defaultdict(list)
        for r in cap_rows:
            by_threads[r["threads"]].append(r["ops_per_sec"])
        for threads in sorted(by_threads):
            vals = by_threads[threads]
            m, s = _mean_std(vals)
            row = {"threads": threads, "ops_per_sec": m}
            if len(jsons) > 1:
                row["ops_per_sec_mean"], row["ops_per_sec_std"] = m, s
            else:
                row["ops_per_sec_mean"], row["ops_per_sec_std"] = m, 0.0
            cap_data.append(row)

    eff_data = []
    if eff_rows:
        by_bs = defaultdict(lambda: {"bw": [], "lat": []})
        for r in eff_rows:
            key = r["block_size"]
            by_bs[key]["bw"].append(r["bw_mib_s"])
            by_bs[key]["lat"].append(r["p99_lat_us"])
        # Preserve block_size order (first occurrence)
        seen = []
        for r in eff_rows:
            bs = r["block_size"]
            if bs not in seen:
                seen.append(bs)
        for block_size in seen:
            bw_vals = by_bs[block_size]["bw"]
            lat_vals = by_bs[block_size]["lat"]
            bw_m, bw_s = _mean_std(bw_vals)
            lat_m, lat_s = _mean_std(lat_vals)
            row = {
                "block_size": block_size,
                "bw_mib_s": bw_m,
                "p99_lat_us": lat_m,
                "bw_mib_s_mean": bw_m,
                "bw_mib_s_std": bw_s,
                "p99_lat_us_mean": lat_m,
                "p99_lat_us_std": lat_s,
            }
            eff_data.append(row)

    return cap_data, eff_data, meta


def plot_capability(cap_data: list[dict], metadata: dict, out_path: str | None = None) -> None:
    """Plot capability sweep: threads vs ops/s (Pillar 1)."""
    if not cap_data:
        return
    fig, ax = plt.subplots()
    arch_label = metadata.get("type") or metadata.get("isa") or "Unknown"

    x = [r["threads"] for r in cap_data]
    y = [r["ops_per_sec_mean"] for r in cap_data]
    err = [r["ops_per_sec_std"] for r in cap_data]
    if any(err):
        ax.errorbar(x, y, yerr=err, marker="o", capsize=4, label=arch_label)
    else:
        ax.plot(x, y, marker="o", label=arch_label)
    ax.set_xlabel("Threads")
    ax.set_ylabel("Bogo ops/s")
    ax.set_title("Capability sweep (stress-ng CPU)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_efficiency(eff_data: list[dict], metadata: dict, out_path: str | None = None) -> None:
    """Plot efficiency sweep: block size vs bandwidth and p99 latency (Pillar 3)."""
    if not eff_data:
        return
    arch_label = metadata.get("type") or metadata.get("isa") or "Unknown"
    block_sizes = [r["block_size"] for r in eff_data]

    fig, (ax_bw, ax_lat) = plt.subplots(2, 1, sharex=True, figsize=(7, 7))

    y_bw = [r["bw_mib_s_mean"] for r in eff_data]
    err_bw = [r["bw_mib_s_std"] for r in eff_data]
    y_lat = [r["p99_lat_us_mean"] for r in eff_data]
    err_lat = [r["p99_lat_us_std"] for r in eff_data]

    if any(err_bw):
        ax_bw.bar(range(len(block_sizes)), y_bw, yerr=err_bw, capsize=4)
    else:
        ax_bw.bar(range(len(block_sizes)), y_bw)
    if any(err_lat):
        ax_lat.bar(range(len(block_sizes)), y_lat, yerr=err_lat, capsize=4)
    else:
        ax_lat.bar(range(len(block_sizes)), y_lat)

    ax_bw.set_ylabel("Bandwidth (MiB/s)")
    ax_bw.set_title("Efficiency sweep (fio write) — Bandwidth")
    ax_bw.set_xticks(range(len(block_sizes)))
    ax_bw.set_xticklabels(block_sizes)
    ax_bw.grid(True, alpha=0.3)

    ax_lat.set_xticks(range(len(block_sizes)))
    ax_lat.set_xticklabels(block_sizes)
    ax_lat.set_xlabel("Block size")
    ax_lat.set_ylabel("p99 latency (µs)")
    ax_lat.set_title("Efficiency sweep — p99 latency")
    ax_lat.grid(True, alpha=0.3)

    fig.suptitle(f"Arch: {arch_label}", fontsize=10, y=1.02)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def tipping_points(eff_data: list[dict], latency_threshold_us: float = 100_000) -> list[dict]:
    """Identify rows where p99 latency exceeds threshold (e.g. 100ms = 100_000 µs)."""
    return [r for r in eff_data if r["p99_lat_us_mean"] > latency_threshold_us]


def analyze_and_plot(
    path: str = "results",
    out_dir: str | None = None,
    show: bool = True,
) -> None:
    """
    Load JSON result(s) from path (file or directory), build plots, optionally save.
    """
    json_paths = find_result_jsons(path)
    if not json_paths:
        print(f"No result JSONs found at {path}. Expect processed_results.json or perf_run_*.json")
        return

    data = [load_result_json(p) for p in json_paths]
    cap_data, eff_data, meta = results_to_tables(data)

    arch_label = meta.get("type") or meta.get("isa") or "Unknown"
    print(f"Loaded {len(json_paths)} run(s) for {arch_label}")

    tipping = tipping_points(eff_data, latency_threshold_us=100_000)
    if tipping:
        print("Detected Tipping Points (p99 latency > 100 ms):")
        for r in tipping:
            print(f"  {r['block_size']}: p99_lat_us={r['p99_lat_us_mean']:.1f}")
    else:
        print("No tipping points (p99 latency > 100 ms) in this dataset.")

    save_basename = None
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        save_basename = os.path.join(out_dir, "plot")

    if cap_data:
        plot_capability(
            cap_data, meta,
            out_path=f"{save_basename}_capability.png" if save_basename else None,
        )
    if eff_data:
        plot_efficiency(
            eff_data, meta,
            out_path=f"{save_basename}_efficiency.png" if save_basename else None,
        )

    if save_basename and (cap_data or eff_data):
        print(f"Plots saved under {out_dir}/")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Plot harness JSON results.")
    parser.add_argument(
        "path",
        nargs="?",
        default="results",
        help="Path to results directory or to a single .json file",
    )
    parser.add_argument(
        "-o", "--out-dir",
        default=None,
        help="Directory to save plot images (default: show only)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open interactive plots (useful when saving only)",
    )
    args = parser.parse_args()
    analyze_and_plot(path=args.path, out_dir=args.out_dir, show=not args.no_show)
