# GitHub Issues Import API Client for Python

[![PyPI License](https://img.shields.io/pypi/l/github-issues-import)](https://github.com/zyv/github-issues-import/blob/main/LICENSE)
[![PyPI project](https://img.shields.io/pypi/v/github-issues-import.svg?logo=python&logoColor=edb641)](https://pypi.python.org/pypi/github-issues-import)
![Python versions](https://img.shields.io/pypi/pyversions/github-issues-import.svg?logo=python&logoColor=edb641)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://docs.pydantic.dev/latest/contributing/#badges)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/zyv/github-issues-import/workflows/CI/badge.svg)](https://github.com/zyv/github-issues-import/actions)

Modern, typesafe Python client for GitHub's unofficial API for importing issues.

This package is based on the [API description](https://gist.github.com/jonmagic/5282384165e0f86ef105) by [jonmagic](https://github.com/jonmagic). Unlike the official REST or GraphQL APIs, this API allows you to keep the timestamps of the imported issues and comments.

## Installation

```shell
$ pip install github-issues-import
```

## Dependencies

* [Pydantic V2](https://pydantic.dev)
* [httpx](https://www.python-httpx.org)

## Usage

```python
import os
from github_issues_import.client import ApiClient, HttpClient
from github_issues_import.models import IssueImportRequest, Issue, Comment

client = ApiClient(http_client=HttpClient(token=os.environ["GITHUB_TOKEN"]))

status = client.import_issue("jonmagic", "i-got-issues", IssueImportRequest(
    issue=Issue(
        title="My money, mo issues",
        body="Required!"
    ),
    comments=[Comment(body="talk talk")],
))

result = client.get_status(status.url)
print(result)
```

### Advanced usage

```python
import os
import httpx
from github_issues_import.client import ApiClient, HttpClient

# httpx client options
client1 = ApiClient(http_client=HttpClient(token=os.environ["GITHUB_TOKEN"], timeout=60))

# own httpx-based client
client2 = ApiClient(http_client=httpx.Client(base_url=HttpClient.BASE_URL))
```

## Development

To release a new version and publish it to PyPI:

* Bump version with `hatch` and commit
  * `hatch version minor` or `hatch version patch`
* Create GitHub release (and tag)
