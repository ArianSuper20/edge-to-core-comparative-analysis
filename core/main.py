import subprocess
import os
import json
import random
import re
import time
import sys
from discovery import get_arch_details

def run_validation():
    arch = get_arch_details()
    final_results = {
        "metadata": arch,
        "capability_sweep": [],
        "efficiency_sweep": []
    }
    
    print(f"\nTestbench Active: {arch['isa']} ({arch['type']})", flush=True)
    print("-" * 30, flush=True)

    # --- SIFI LOGIC ---
    sifi_enabled = os.getenv("ENABLE_SIFI", "false").lower() == "true"
    if sifi_enabled:
        fail_time = random.uniform(2, 5) # Fail early to save time
        print(f"!!! SIFI ENABLED: System fault in {fail_time:.2f}s !!!")
        time.sleep(fail_time)
        print("CRITICAL FAILURE: Simulated process crash.")
        sys.exit(1)

    # --- PILLAR 1: CAPABILITY (Throughput Sweep) ---
    # stress-ng has no --json; use --metrics-brief and parse stdout for bogo ops/s
    cpu_counts = [1, 2, 4, 8]
    for count in cpu_counts:
        print(f"Running CPU Stress: {count} threads...", flush=True)
        result = subprocess.run(
            [
                "stress-ng", "--cpu", str(count), "--timeout", "5s",
                "--metrics-brief",
            ],
            capture_output=True,
            text=True,
        )
        # stress-ng prints metrics table to stderr; parse bogo ops/s (real time)
        out = (result.stdout or "") + (result.stderr or "")
        lines = out.strip().splitlines()
        ops = 0.0
        for line in reversed(lines):
            # Match line like "stress-ng: info:  [1] cpu    3270  2.00  2.00  0.00  1634.33  1635.00"
            m = re.search(r"\bcpu\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+[\d.]+", line)
            if m:
                ops = float(m.group(1))
                break
        final_results["capability_sweep"].append({"threads": count, "ops_per_sec": ops})

    # --- PILLAR 3: EFFICIENCY (Memory Wall Sweep) ---
    block_sizes = ["4k", "64k", "1M", "4M"]
    for bs in block_sizes:
        print(f"Running I/O Saturation: Block Size {bs}...", flush=True)
        subprocess.run([
            "fio", "--name=bench", "--rw=write", f"--bs={bs}", "--size=128M",
            "--ioengine=libaio", "--direct=1", "--runtime=5", "--time_based",
            "--output-format=json", "--output=/tmp/fio.json"
        ], capture_output=True)
        
        with open("/tmp/fio.json", "r") as f:
            data = json.load(f)
            write_data = data['jobs'][0]['write']
            final_results["efficiency_sweep"].append({
                "block_size": bs,
                "bw_mib_s": write_data['bw_bytes'] / (1024*1024),
                "p99_lat_us": write_data['clat_ns']['percentile']['99.000000'] / 1000
            })

    # --- SAVE RESULTS ---
    output_dir = "/app/results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, "processed_results.json")
    with open(output_path, "w") as f:
        json.dump(final_results, f, indent=4)

    print("\n VALIDATION COMPLETE!.", flush=True)

if __name__ == "__main__":
    run_validation()