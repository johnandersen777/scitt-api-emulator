r"""
From: https://github.com/intel/dffml/tree/ecd458fcdb0c093b91c6028322495df9016cc536

`git ls-remote` is a Git command that queries the remote repository for
references, specifically the SHA-1 hashes of commits at the HEADs of branches
and tags. It's frequently utilized to view references without needing to
perform a full clone or fetch.

When done over HTTP/HTTPS, `git ls-remote` follows these steps:

1. **Send a GET request to `<repo URL>/info/refs?service=git-upload-pack`.**

   `git-upload-pack` is the service that's responsible for providing packfiles
    to the client in response to fetch requests. This service also runs the `git
    upload-pack` command, gathering the objects necessary to complete a fetch.

2. **Server will respond with a `text/plain` content type and a `001#
    service=git-upload-pack` header, followed by a list of references and
    capabilities.**

   The payload consists of pkt-line (packet line) formatted data. Each line has
   a 4-byte length header, which includes the 4 bytes used for the length header
   itself. "0000" signals the end of the header.

   The server lists all the HEADs of the branches and the tags of the repo,
   giving their SHA1 values and their fully-qualified names. After the `0000`,
   it also lists `capabilities` such as `multi_ack`, `thin-pack`, `ofs-delta`,
   etc.

3. **Client parses the refs.**

    Your client, or your code using `aiohttp` in this case, would need to parse
    the refs information to extract the SHA-1 hashes and the fully-qualified
    names of the branches and tags.

In short, when you run `git ls-remote` over HTTP, it makes a single HTTP GET
request to the `/info/refs` endpoint of the repository you're querying, and
parses the response to display the list of references in the remote repository.

Remember that this data contains null bytes and other binary data. Thus,
manipulating it as a regular string might result in incorrect results. Use
appropriate methods to deal with binary data.

Usage:

```bash
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/scitt-community/scitt-api-emulator/forks \
  | jq -r '.[].html_url' \
  | GH_TOKEN=$(gh auth token) time pythoe -u scitt_software_supply_chain_middleware/triggers/git_ls_remote.py \
  | jq
"""
import os
import sys
import json
import base64
import asyncio
import datetime
import dataclasses
from typing import List, Dict


async def git_ls_remote(session, repo_url):
    import aiohttp

    async with session.get(
        f"{repo_url}/info/refs?service=git-upload-pack",
    ) as response:
        if response.status == 401:
            raise Exception(
                repo_url
                + ": "
                + await response.text()
                + ": "
                + json.dumps(dict(response.headers), indent=4, sort_keys=True)
            )
        elif response.status == 200:
            refs_info = await response.text()
            return parse_refs(repo_url, refs_info)


@dataclasses.dataclass
class GitLsRemoteRefs:
    repo_url: str
    metadata: Dict[str, str]
    capabilities: List[str]
    refs: Dict[str, str]


def parse_refs(repo_url, refs_info):
    if refs_info.count("\n") < 2:
        return
    header, HEAD = refs_info.split("\n", maxsplit=1)
    HEAD, lines = HEAD.split("\x00", maxsplit=1)
    refs = {}
    metadata = {}
    capabilities, lines = lines.split("\n", maxsplit=1)
    metadata_in_capabilities = []
    capabilities = capabilities.split()
    for cap in capabilities:
        if "=" in cap:
            metadata_in_capabilities.append(cap)
            key, value = cap.split("=", maxsplit=1)
            metadata[key] = value
    for cap in metadata_in_capabilities:
        del capabilities[capabilities.index(cap)]
    lines = [HEAD[4:]] + lines.split("\n")
    for line in lines:
        for sep in (" ", "\t"):
            if not line or sep not in line:
                continue
            hash_ref, ref = line.split(sep, maxsplit=1)
            refs[ref] = hash_ref[4:]
            continue
    return GitLsRemoteRefs(
        repo_url=repo_url,
        metadata=metadata,
        capabilities=capabilities,
        refs=refs,
    )


async def git_ls_remotes(repo_urls: List[str], github_token: str = None):
    import aiohttp

    headers = None
    if github_token:
        basic_auth = base64.b64encode(
            ("token:" + github_token).encode()
        ).decode()
        headers = {"Authorization": f"Basic {basic_auth}"}

    async with aiohttp.ClientSession(
        trust_env=True,
        headers=headers,
    ) as session:
        async with asyncio.TaskGroup() as tg:
            for coro in asyncio.as_completed(
                [
                    tg.create_task(git_ls_remote(session, repo_url))
                    for repo_url in repo_urls
                ]
            ):
                git_ls_remote_refs = await coro
                if git_ls_remote_refs:
                    yield git_ls_remote_refs


async def main():
    print(
        json.dumps(
            {
                git_ls_remote_refs.repo_url: dataclasses.asdict(
                    git_ls_remote_refs
                )
                async for git_ls_remote_refs in git_ls_remotes(
                    list(
                        sorted(list(set([line.strip() for line in sys.stdin])))
                    ),
                    github_token=os.environ.get("GH_TOKEN", None),
                )
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
