from dotenv import load_dotenv
from atlassian.bitbucket import Cloud
import os
import time
import logging
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

def bytes_to_gb(bytes_value):
    return bytes_value / (1024 ** 3)

def get_repo_size(project):
    size = 0
    for repo in project.repositories.each():
        size += repo.size
    print(project.key, size)
    return bytes_to_gb(size)

def main():
    bitbucket = Cloud(
        url='https://api.bitbucket.org/',
        username=BITBUCKET_USERNAME,
        password=BITBUCKET_APP_PASSWORD)

    workspace = bitbucket.workspaces.get('sourcedgroup')

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_cores) as executor:
      results = list(executor.map(lambda project: get_repo_size(project), workspace.projects.each()))

    print(sum(results))

if __name__ == "__main__":
    main()
