@task
def run_bench(c, sifi=False):
    """Run the bench normally, or with SIFI if specified."""
    sifi_val = "true" if sifi else "false"
    
    print(f"Starting iteration (SIFI={sifi_val}) on {c.host}...")
    
    # Passing the choice into the container via -e (environment variable)
    result = c.run(f"docker run --rm -e ENABLE_SIFI={sifi_val} assurance-harness", warn=True)
    
    if result.failed:
        print(f"Iteration on {c.host} failed as expected. Measuring recovery...")
        # (You can trigger your recovery logic here)
    else:
        print(f"Iteration on {c.host} completed successfully.")