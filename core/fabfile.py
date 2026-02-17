#This is the script that deploy the code using fabric
from fabric import Connection, task

@task
def deploy(c):
    """Deploy the Docker container to the remote target (Pi or Mainframe)."""
    print(f"Deploying to: {c.host}")
    # Pull the latest code from your GitHub
    c.run("cd ~/assurance-harness && git pull origin main")
    # Build and run the bench
    c.run("docker build -t assurance-harness ./testbenches")
    print("Deployment Complete.")

@task
def run_test(c):
    """Execute the stress test inside the container."""
    print("Starting Stress Test...")
    c.run("docker run --rm assurance-harness python3 /app/core/discovery.py")