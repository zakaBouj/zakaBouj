import os
import requests
import re
from datetime import datetime, timedelta
import json

# Constants
USER_NAME = os.environ.get('GITHUB_USERNAME', 'zakaBouj')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
README_PATH = 'README.md'
STATS_MARKER = '<!-- Live Github Stats -->'

HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
GRAPHQL_URL = 'https://api.github.com/graphql'

def run_graphql_query(query, variables=None):
    """Run a GraphQL query against GitHub's API"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_user_stats():
    """Fetch basic user stats: repositories, stars, followers"""
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazers {
              totalCount
            }
            forkCount
          }
        }
        followers {
          totalCount
        }
        pullRequests {
          totalCount
        }
        issues {
          totalCount
        }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY], first: 100, includeUserRepositories: false) {
          totalCount
        }
      }
    }
    """
    
    # Sample data for local testing without a token
    if not GITHUB_TOKEN or GITHUB_TOKEN == '':
        print("No GitHub token provided, using sample data")
        return {
            'repos': 2,
            'stars': 0,
            'forks': 0,
            'followers': 1,
            'pull_requests': 70,
            'issues': 89,
            'contributed_to': 9
        }
    
    variables = {'username': USER_NAME}
    result = run_graphql_query(query, variables)
    
    if not result or 'data' not in result:
        print("Failed to get user stats, using sample data")
        return {
            'repos': 2,
            'stars': 0,
            'forks': 0,
            'followers': 1,
            'pull_requests': 70,
            'issues': 89,
            'contributed_to': 9
        }
    
    data = result['data']['user']
    
    # Calculate total stars
    total_stars = sum(repo['stargazers']['totalCount'] for repo in data['repositories']['nodes'])
    total_forks = sum(repo['forkCount'] for repo in data['repositories']['nodes'])
    
    return {
        'repos': data['repositories']['totalCount'],
        'stars': total_stars,
        'forks': total_forks,
        'followers': data['followers']['totalCount'],
        'pull_requests': data['pullRequests']['totalCount'],
        'issues': data['issues']['totalCount'],
        'contributed_to': data['repositoriesContributedTo']['totalCount']
    }

def get_contributions():
    """Fetch contribution stats: commits, contributions for past year"""
    # Sample data for local testing without a token
    if not GITHUB_TOKEN or GITHUB_TOKEN == '':
        print("No GitHub token provided, using sample data for contributions")
        return {
            'commits_year': 65,
            'total_contributions_year': 76,
            'pull_requests_year': 70,
            'issues_year': 89,
            'reviews_year': 0
        }
    
    # Get current date and date from 1 year ago
    end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    
    variables = {
        'username': USER_NAME,
        'from': start_date,
        'to': end_date
    }
    
    result = run_graphql_query(query, variables)
    
    if not result or 'data' not in result:
        print("Failed to get contribution stats, using sample data")
        return {
            'commits_year': 65,
            'total_contributions_year': 76,
            'pull_requests_year': 70,
            'issues_year': 89,
            'reviews_year': 0
        }
    
    contributions = result['data']['user']['contributionsCollection']
    
    return {
        'commits_year': contributions['totalCommitContributions'],
        'total_contributions_year': contributions['contributionCalendar']['totalContributions'],
        'pull_requests_year': contributions['totalPullRequestContributions'],
        'issues_year': contributions['totalIssueContributions'],
        'reviews_year': contributions['totalPullRequestReviewContributions']
    }

def get_total_commits():
    """Get estimate of total commits across all repositories"""
    # Sample data for local testing without a token
    if not GITHUB_TOKEN or GITHUB_TOKEN == '':
        print("No GitHub token provided, using sample data for total commits")
        return {'total_commits': 65, 'total_commits_year': 628}
    
    # Get current date and date for 2025
    today = datetime.now()
    start_of_2025 = datetime(2025, 1, 1)
    
    # This is more complex to get accurately, so we'll use multiple API calls
    try:
        # First get total commit count
        total_commits = 0
        page = 1
        per_page = 100
        
        while True:
            url = f"https://api.github.com/users/{USER_NAME}/repos?page={page}&per_page={per_page}"
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code != 200 or not response.json():
                break
            
            repos = response.json()
            if not repos:
                break
                
            for repo in repos:
                repo_name = repo['name']
                commits_url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}/commits?author={USER_NAME}&per_page=1"
                commits_response = requests.get(commits_url, headers=HEADERS)
                
                if commits_response.status_code == 200:
                    # Get the total from the Link header if it exists
                    link_header = commits_response.headers.get('Link', '')
                    if 'rel="last"' in link_header:
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            total_commits += int(match.group(1))
                    else:
                        # If no Link header, count the results
                        total_commits += len(commits_response.json())
            
            page += 1
            
            # GitHub's API has rate limits, so we'll limit this to avoid hitting them
            if page > 5:  # Limit to checking about 500 repos to avoid rate limits
                break
        
        # Now get commits for 2025
        query = """
        query($username: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $username) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
            }
          }
        }
        """
        
        variables = {
            'username': USER_NAME,
            'from': start_of_2025.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': today.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        result = run_graphql_query(query, variables)
        total_commits_year = 628  # Default
        
        if result and 'data' in result:
            total_commits_year = result['data']['user']['contributionsCollection']['totalCommitContributions']
        
        return {'total_commits': total_commits or 65, 'total_commits_year': total_commits_year}
    except Exception as e:
        print(f"Error getting commit data: {e}")
        return {'total_commits': 65, 'total_commits_year': 628}  # Return sample data on error

def generate_stats_markdown():
    """Generate Markdown for GitHub stats section"""
    user_stats = get_user_stats()
    contribution_stats = get_contributions()
    commit_stats = get_total_commits()
    
    # Combine all stats
    stats = {**user_stats, **contribution_stats, **commit_stats}
    
    # Format stats into shield.io badges to match README style
    markdown = """
## GitHub Stats

![Repositories](https://img.shields.io/badge/Repositories-{repos}-blue?style=flat&logo=github)
![Stars](https://img.shields.io/badge/Stars-{stars}-yellow?style=flat&logo=github)
![Followers](https://img.shields.io/badge/Followers-{followers}-lightgrey?style=flat&logo=github)
![Forks](https://img.shields.io/badge/Forks-{forks}-orange?style=flat&logo=github)

![Total Commits](https://img.shields.io/badge/Total%20Commits-{total_commits}-brightgreen?style=flat&logo=git)
![Commits (Year)](https://img.shields.io/badge/Commits%20(Year)-{commits_year}-green?style=flat&logo=git)
![Contributions (Year)](https://img.shields.io/badge/Contributions%20(Year)-{total_contributions_year}-blueviolet?style=flat&logo=github)

![Pull Requests](https://img.shields.io/badge/Pull%20Requests-{pull_requests}-purple?style=flat&logo=github)
![Issues](https://img.shields.io/badge/Issues-{issues}-red?style=flat&logo=github)
![PR Reviews](https://img.shields.io/badge/PR%20Reviews-{reviews_year}-blue?style=flat&logo=github)

![Contributed To](https://img.shields.io/badge/Contributed%20To-{contributed_to}-teal?style=flat&logo=github)
![Total Commits (2025)](https://img.shields.io/badge/Total%20Commits%20(2025)-{total_commits_year}-darkgreen?style=flat&logo=git)
""".format(**stats)

    return markdown

def update_readme():
    """Update the README.md file with generated stats"""
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the stats marker
        marker_index = content.find(STATS_MARKER)
        
        if marker_index == -1:
            print("Stats marker not found in README")
            return False
        
        # Get the content before the marker
        before_marker = content[:marker_index + len(STATS_MARKER)]
        
        # Find the next section after our stats (look for '***Featured Projects***' or any other section heading)
        featured_projects_index = content.find("***Featured Projects***")
        stats_section_index = content.find("***Stats***")
        
        # Determine the nearest next section
        next_section_index = None
        if featured_projects_index > marker_index:
            next_section_index = featured_projects_index
        if stats_section_index > marker_index and (next_section_index is None or stats_section_index < next_section_index):
            next_section_index = stats_section_index
        
        if next_section_index:
            # Get content from the next section to the end
            after_stats = content[next_section_index:]
        else:
            # If we can't find a known next section, look for a blank line followed by anything
            next_blank_line = re.search(r'\n\s*\n', content[marker_index:])
            if next_blank_line:
                after_stats = content[marker_index + next_blank_line.start():]
            else:
                after_stats = ""
        
        # Create new README content
        new_content = before_marker + "\n\n" + generate_stats_markdown() + "\n\n" + after_stats
        
        # Write the new content
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    
    except Exception as e:
        print(f"Error updating README: {e}")
        return False

if __name__ == "__main__":
    update_readme()