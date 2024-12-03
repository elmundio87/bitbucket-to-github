from dotenv import load_dotenv
import requests
import os
import subprocess
import logging
import time
import concurrent.futures

load_dotenv() # Create a .env file with your Bitbucket username and app password
num_cores = os.cpu_count()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_API_URL = os.getenv("GITHUB_API_URL")

# Configure the logging
timestamp = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(
  filename=f'error-{timestamp}.log',  # Log file name with timestamp
  level=logging.ERROR,   # Log only errors and above
  format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

class GitHubRepoMapping:
  def __init__(self, workspace, project, repo):
    self.workspace = workspace
    self.project = project
    self.repo = repo

  def do_it(self):
    self.create_repo()
    self.apply_topics()
    self.push_repo()
    self.push_lfs()

  def create_repo(self):
    url = f'{GITHUB_API_URL}/orgs/{GITHUB_OWNER}/repos'
    data = {
        'name': self.repo,
        'private': True,
        'description': f'Mirror of Bitbucket Repo {self.workspace}/{self.project}/{self.repo}.git'
    }
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f'Repository {self.repo} created successfully!')
    else:
        print(f'Failed to create {self.repo}: {response.status_code} - {response.text}')
    return response.status_code == 201

  def apply_topics(self):
    url = f'{GITHUB_API_URL}/orgs/{GITHUB_OWNER}/repos'
    headers = {
      'Authorization': f'Bearer {GITHUB_TOKEN}',
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    }
    data = {
        'names': [self.workspace, self.project]
    }
    response = requests.put(url, json=data, headers=headers)

    if response.status_code == 200:
        print(f'Topics {data.names} applied to {self.repo} successfully!')
    else:
        print(f'Failed to apply topics to {self.repo}: {response.status_code} - {response.text}')

  def push_repo(self):
    command = ["git", "-C", f"mirrors/{self.workspace}/{self.project}/{repo}.git", "push", "--mirror", f"https://github.com/{GITHUB_OWNER}/{self.repo}.git"]
    try:
        print("Pushing to GitHub: {self.workspace}/{self.project}/{self.repo}")
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        print("ERROR: See log file for details")

  def push_lfs(self):
    command = ["git", "-C", f"mirrors/{self.workspace}/{self.project}/{repo}.git", "lfs", "push", "--all", f"https://github.com/{GITHUB_OWNER}/{self.repo}.git"]
    try:
        print("Pushing to GitHub: {self.workspace}/{self.project}/{self.repo}")
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        print("ERROR: See log file for details")

def map_directories(base_path):
  directory_map = {}

  for item in os.listdir(base_path):
    if os.path.isdir(f"{base_path}/{item}"):
      directory_map[item] = os.listdir(f"{base_path}/{item}")
  return directory_map


base_path = "mirrors"

result = map_directories(base_path)

jobs = []

for workspace in result:
  for project in result[workspace]:
    for repo in os.listdir(f"{base_path}/{workspace}/{project}"):
      jobs += GitHubRepoMapping(workspace, project, repo)

with concurrent.futures.ThreadPoolExecutor(max_workers=num_cores) as executor:
    executor.map(lambda job: job.do_it(), jobs)
