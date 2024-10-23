import requests
import json
import argparse
import os
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


# Define Pydantic models
class Author(BaseModel):
    login: str


class Reply(BaseModel):
    id: str
    body: str
    author: Author
    createdAt: datetime


class Comment(BaseModel):
    id: str
    body: str
    author: Author
    createdAt: datetime
    replies: List[Reply]


class PageInfo(BaseModel):
    hasNextPage: bool
    endCursor: Optional[str]


class ReviewComments(BaseModel):
    edges: List[Comment]
    pageInfo: PageInfo


class Review(BaseModel):
    node: ReviewComments


class PullRequest(BaseModel):
    reviews: ReviewComments


class Repository(BaseModel):
    pullRequest: PullRequest


class Data(BaseModel):
    repository: Repository


class GraphQLResponse(BaseModel):
    data: Data
    errors: Any


# GitHub API endpoint and token
GRAPHQL_URL = "https://api.github.com/graphql"

# GraphQL query
QUERY = """
query GetReviewCommentsAndReplies($org: String!, $repo: String!, $pullRequestNumber: Int!, $commentsCursor: String, $repliesCursor: String) {
  repository(owner: $org, name: $repo) {
    pullRequest(number: $pullRequestNumber) {
      reviews(first: 100, after: $commentsCursor) {
        edges {
          node {
            id
            comments(first: 100, after: $repliesCursor) {
              edges {
                node {
                  id
                  body
                  author {
                    login
                  }
                  createdAt
                  replies(first: 100) {
                    edges {
                      node {
                        id
                        body
                        author {
                          login
                        }
                        createdAt
                      }
                    }
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                  }
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""


def fetch_comments(
    org: str, repo: str, pull_request_number: int, token: str
) -> List[Comment]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    all_comments = []
    has_next_page = True
    comments_cursor = None

    while has_next_page:
        variables = {
            "org": org,
            "repo": repo,
            "pullRequestNumber": pull_request_number,
            "commentsCursor": comments_cursor,
            "repliesCursor": None,
        }

        response = requests.post(
            GRAPHQL_URL, json={"query": QUERY, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Parse response with pydantic
        graph_response = GraphQLResponse.parse_obj(data)
        reviews = graph_response.data.repository.pullRequest.reviews

        for review in reviews.edges:
            review_node = review.node
            comments = review_node.comments

            for comment in comments.edges:
                comment_node = comment.node
                comment_data = Comment(
                    id=comment_node.id,
                    body=comment_node.body,
                    author=comment_node.author,
                    createdAt=datetime.fromisoformat(
                        comment_node.createdAt.replace("Z", "+00:00")
                    ),
                    replies=[
                        Reply(
                            id=reply_node.id,
                            body=reply_node.body,
                            author=reply_node.author,
                            createdAt=datetime.fromisoformat(
                                reply_node.createdAt.replace("Z", "+00:00")
                            ),
                        )
                        for reply_node in comment_node.replies.edges
                    ],
                )

                all_comments.append(comment_data)

            has_next_page = comments.pageInfo.hasNextPage
            comments_cursor = comments.pageInfo.endCursor

        has_next_page = reviews.pageInfo.hasNextPage
        variables["commentsCursor"] = reviews.pageInfo.endCursor

    return all_comments


def format_json(comments: List[Comment]) -> str:
    return json.dumps([comment.dict() for comment in comments], indent=2, default=str)


def format_markdown(comments: List[Comment]) -> str:
    markdown_lines = []
    for comment in comments:
        markdown_lines.append(
            f"### Comment by {comment.author.login} (Created at: {comment.createdAt})\n"
        )
        markdown_lines.append(f"{comment.body}\n")
        for reply in comment.replies:
            markdown_lines.append(
                f"#### Reply by {reply.author.login} (Created at: {reply.createdAt})\n"
            )
            markdown_lines.append(f"{reply.body}\n")
        markdown_lines.append("\n---\n")
    return "\n".join(markdown_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch review comments and replies for a GitHub pull request."
    )
    parser.add_argument("org", type=str, help="The GitHub organization name")
    parser.add_argument("repo", type=str, help="The GitHub repository name")
    parser.add_argument("pr_number", type=int, help="The number of the pull request")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (json or markdown)",
    )
    parser.add_argument("--token", type=str, help="GitHub personal access token")

    args = parser.parse_args()

    token = args.token or os.getenv("GH_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token is required. Please provide it via --token or set the GITHUB_TOKEN environment variable."
        )

    comments = fetch_comments(args.org, args.repo, args.pr_number, token)

    if args.format == "json":
        output = format_json(comments)
    elif args.format == "markdown":
        output = format_markdown(comments)

    # Print the output
    print(output)


if __name__ == "__main__":
    main()
