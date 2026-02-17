#This code coordinates the validation sequence
import subprocess
import os

def run_validation():
    # 1. Header first
    print("\n🚀 Assurance Harness Active", flush=True)
    print("-" * 30, flush=True)
    
    # 2. Print NEXT task, THEN run it
    print("Executing Task 1: CPU Stress (10s)...", flush=True)
    subprocess.run(["stress-ng", "--cpu", "2", "--timeout", "10s", "--metrics-brief"])
    
    # 3. Print NEXT task, THEN run it
    print("\nExecuting Task 2: I/O Saturation...", flush=True)
    fio_config = "/app/testbenches/memory_wall.fio"
    
    if os.path.exists(fio_config):
        subprocess.run(["fio", fio_config])
    else:
        print("❌ Error: Config not found.")

    # 4. Final closing statement
    print("\n✅ All validation tasks complete.", flush=True)

if __name__ == "__main__":
    run_validation()