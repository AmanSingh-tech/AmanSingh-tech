import os
import requests

GITHUB_API = "https://api.github.com/graphql"

def fetch_contributions(username: str):
    token = os.getenv("GH_TOKEN")
    if not token:
        raise RuntimeError("GH_TOKEN not set")

    query = """
    query($user: String!) {
      user(login: $user) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    res = requests.post(
        GITHUB_API,
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "variables": {"user": username}}
    )

    res.raise_for_status()
    return res.json()["data"]["user"]["contributionsCollection"]
