from dotenv import load_dotenv
from atlassian.bitbucket import Cloud
import subprocess
import os
import logging
import time
import concurrent.futures

load_dotenv() # Create a .env file with your Bitbucket username and app password
num_cores = os.cpu_count()

# Replace with your Bitbucket username and app password
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
BITBUCKET_APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")

# Configure the logging
timestamp = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(
  filename=f'error-{timestamp}.log',  # Log file name with timestamp
  level=logging.ERROR,   # Log only errors and above
  format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

def make_dir_structure(workspace, project):
    root_dir = f"mirrors/{workspace}/{project}"
    os.makedirs(root_dir, exist_ok=True)
    return root_dir

def git_clone(workspace, project, repo):
  root_dir = make_dir_structure(workspace, project)
  if os.path.exists(f"{root_dir}/{repo}.git"):
    command = ["git", "-C", f"{root_dir}/{repo}.git", "fetch", "--prune", "origin"]
    print(f"Updating: {workspace}/{project}/{repo}")
  else:
    command = ["git", "clone", "--mirror", f"https://{BITBUCKET_USERNAME}:{BITBUCKET_APP_PASSWORD}@bitbucket.org/{workspace}/{repo}.git", f"{root_dir}/{repo}.git"]
    print(f"Cloning: {workspace}/{project}/{repo}")
  try:
      result = subprocess.run(command, capture_output=True, text=True, check=True)
  except subprocess.CalledProcessError as e:
      logging.error(e.stderr)
      print("ERROR: See log file for details")

def git_lfs(workspace, project, repo):
  root_dir = make_dir_structure(workspace, project)
  command = ["git", "-C", f"{root_dir}/{repo}.git", "lfs", "fetch", "--all"]
  print(f"Git LFS Update: {workspace}/{project}/{repo}")
  try:
      subprocess.run(command, capture_output=True, text=True, check=True)
  except subprocess.CalledProcessError as e:
      logging.error(e.stderr)
      print("ERROR: See log file for details")

# for each workspace
# for each project
# for each repository

def main():
    bitbucket = Cloud(
        url='https://api.bitbucket.org/',
        username=BITBUCKET_USERNAME,
        password=BITBUCKET_APP_PASSWORD)

    jobs = []

    for workspace in bitbucket.workspaces.each():
        for project in workspace.projects.each():
            for repo in project.repositories.each():
                jobs += [(workspace.slug, project.name, repo.name)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_cores) as executor:
        executor.map(lambda x: git_clone(*x), jobs)
        executor.map(lambda x: git_lfs(*x), jobs)

if __name__ == "__main__":
    main()
