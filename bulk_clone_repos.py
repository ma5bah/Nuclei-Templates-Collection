#!/usr/bin/env python3
# This shebang line specifies the Python 3 interpreter to use for executing this script.
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# File containing repository URLs
repo_file = "README.txt"
# Directory to clone into
clone_dir = "community-templates"
# Maximum number of concurrent threads
MAX_WORKERS = 4

# Ensure the clone directory exists
os.makedirs(clone_dir, exist_ok=True)

def is_repo_accessible(url):
    """Check if repository is accessible using git ls-remote"""
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_ASKPASS'] = 'echo'
    
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", url, "HEAD"],
        capture_output=True,
        timeout=30,
        env=env
    )
    return result.returncode == 0

def process_repository(url):
    """Process a single repository - either clone or update it"""
    # Extract the owner and repo name from the URL
    parts = url.split('/')
    if len(parts) < 2:
        return  # Skip if the URL format is incorrect
    
    owner, repo_name = parts[-2], parts[-1]
    repo_name = repo_name.replace('.git', '')
    target_dir = os.path.join(clone_dir, f"{owner}__{repo_name}".lower())
    
    # Environment to prevent password prompts
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_ASKPASS'] = 'echo'
    
    if os.path.isdir(target_dir):
        # If directory exists, pull changes
        print(f"Updating {repo_name} in {target_dir}")
        subprocess.run(["git", "-C", target_dir, "pull"], env=env)
    else:
        # Check if repository is accessible before cloning
        if not is_repo_accessible(url):
            print(f"Skipping {repo_name}: Repository is private or inaccessible")
            return
        
        # If directory does not exist, clone repository
        print(f"Cloning {repo_name} into {target_dir}")
        subprocess.run(["git", "clone", url, target_dir], env=env)

# Read repository URLs from file and remove duplicates
with open(repo_file, 'r') as file:
    urls = list(set(line.strip() for line in file if line.strip()))

# Process each repository with multithreading
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    executor.map(process_repository, urls)

print("\nDone!")
