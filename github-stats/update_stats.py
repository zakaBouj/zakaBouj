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
        pullRequests(states: [OPEN, CLOSED, MERGED]) {
          totalCount
        }
        issues(states: [OPEN, CLOSED]) {
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
            'repos': 99999,
            'stars': 99999,
            'forks': 99999,
            'followers': 99999,
            'pull_requests': 99999,
            'issues': 99999,
            'contributed_to': 99999
        }
    
    variables = {'username': USER_NAME}
    result = run_graphql_query(query, variables)
    
    if not result or 'data' not in result:
        print("Failed to get user stats, using sample data")
        return {
            'repos': 95,
            'stars': 342,
            'forks': 0,
            'followers': 196,
            'pull_requests': 70,
            'issues': 89,
            'contributed_to': 133
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
            'commits_year': 99999,
            'total_contributions_year': 99999,
            'pull_requests_year': 99999,
            'issues_year': 99999,
            'reviews_year': 99999
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
    """Get all-time commits and contributions by querying year by year (API max range is 1 year)"""
    if not GITHUB_TOKEN or GITHUB_TOKEN == '':
        print("No GitHub token provided, using sample data for total commits")
        return {'total_commits': 99999, 'total_commits_year': 99999, 'total_contributions_alltime': 99999}

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """

    today = datetime.now()
    current_year = today.year
    start_year = 2022  # zakaBouj account start year

    total_commits = 0
    total_commits_year = 0
    total_contributions_alltime = 0

    try:
        tomorrow = today + timedelta(days=1)
        for year in range(start_year, current_year + 1):
            year_start = datetime(year, 1, 1).strftime('%Y-%m-%dT%H:%M:%SZ')
            year_end = (datetime(year + 1, 1, 1) if year < current_year else tomorrow).strftime('%Y-%m-%dT%H:%M:%SZ')

            result = run_graphql_query(query, {'username': USER_NAME, 'from': year_start, 'to': year_end})

            if result and 'data' in result and result['data']['user']:
                col = result['data']['user']['contributionsCollection']
                year_commits = col['totalCommitContributions'] + col['restrictedContributionsCount']
                total_commits += year_commits
                total_contributions_alltime += col['contributionCalendar']['totalContributions']
                if year == current_year:
                    total_commits_year = year_commits
            else:
                print(f"Failed to get data for year {year}")

        return {
            'total_commits': total_commits,
            'total_commits_year': total_commits_year,
            'total_contributions_alltime': total_contributions_alltime,
        }
    except Exception as e:
        print(f"Error getting commit data: {e}")
        return {'total_commits': 0, 'total_commits_year': 0, 'total_contributions_alltime': 0}

def generate_stats_markdown():
    """Generate Markdown for GitHub stats section"""
    user_stats = get_user_stats()
    contribution_stats = get_contributions()
    commit_stats = get_total_commits()
    loc_stats = {'lines_added': 99999, 'lines_deleted': 99999, 'net_lines': 99999}
    
    # Combine all stats and add username for links
    stats = {**user_stats, **contribution_stats, **commit_stats, **loc_stats, 'USER_NAME': USER_NAME}
    
    # Format stats into shield.io badges - all on one line for a compact layout
    markdown = """
<p align="center">
  <a href="https://github.com/{USER_NAME}"><img src="https://img.shields.io/badge/Commits-{total_commits}-brightgreen?style=flat&logo=git" alt="Commits"></a>
  <a href="https://github.com/pulls"><img src="https://img.shields.io/badge/PRs-{pull_requests}-purple?style=flat&logo=github" alt="PRs"></a>
  <a href="https://github.com/issues"><img src="https://img.shields.io/badge/Issues-{issues}-red?style=flat&logo=github" alt="Issues"></a>
  <a href="https://github.com/{USER_NAME}"><img src="https://img.shields.io/badge/Contributions-{total_contributions_alltime}-blueviolet?style=flat&logo=github" alt="Contributions"></a>
</p>
""".format(**stats)

    return markdown

def update_readme():
    """Update the README.md file with generated stats"""
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, find the role/title paragraph
        student_developer_paragraph = '<p align="center">\n  <strong>\n    Systems & Backend Software Engineer | Bloomberg (Part-Time) | CS @ Frankfurt UAS'
        student_paragraph_index = content.find(student_developer_paragraph)
        
        if student_paragraph_index == -1:
            print("Could not find role/title paragraph")
            return False
            
        # Find the end of the student/developer paragraph
        paragraph_end_index = content.find('</p>', student_paragraph_index)
        if paragraph_end_index == -1:
            print("Could not find the end of student/developer paragraph")
            return False
        
        # Get content up to the end of the student/developer paragraph
        before_content = content[:paragraph_end_index + 4]  # +4 for "</p>"
        
        # Find Featured Projects section
        featured_projects_index = content.find("***Featured Projects***")
        if featured_projects_index == -1:
            print("Could not find Featured Projects section")
            return False
            
        # Define the working on paragraph
        working_paragraph = "<p align=\"center\">\n  Building a dark pool / ATS simulator using the FIX protocol — order routing, venue fragmentation, and matching logic across simulated US equity venues.\n</p>"
        
        # Get content after Featured Projects (we'll reinsert the working paragraph later)
        after_content = content[featured_projects_index:]
        
        # Create new README content with correct order: intro, stats, working on, featured projects
        new_content = before_content + "\n\n" + generate_stats_markdown() + "\n\n" + working_paragraph + "\n\n" + after_content
        
        # Write the new content
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    
    except Exception as e:
        print(f"Error updating README: {e}")
        return False

if __name__ == "__main__":
    update_readme()