import logging
from datetime import datetime
from typing import ClassVar

import httpx
from pydantic import HttpUrl

from .models import IssueImportRequest, IssueImportStatusResponse

logger = logging.getLogger(__name__)


class HttpClient(httpx.Client):
    @staticmethod
    def log_github_api_request(request: httpx.Request):
        logger.debug(f"GitHub API Request: {request.method} {request.url} {request.content.decode()}")

    @staticmethod
    def log_github_api_response(response: httpx.Response):
        request = response.request
        response.read()
        logger.debug(f"GitHub API Response: {request.method} {request.url} {response.status_code} {response.text}")

    HEADERS: ClassVar = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.golden-comet-preview+json",
    }

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, *, base_url: str = BASE_URL, headers=None, event_hooks=None, **kwargs):
        super().__init__(
            base_url=base_url,
            headers=headers if headers is not None else {"Authorization": f"Token {token}"} | self.HEADERS,
            event_hooks=(
                event_hooks
                if event_hooks is not None
                else {
                    "request": [HttpClient.log_github_api_request],
                    "response": [HttpClient.log_github_api_response, httpx.Response.raise_for_status],
                }
            ),
            **kwargs,
        )


class ApiClient:
    def __init__(
        self,
        *,
        http_client: httpx.Client,
    ):
        self._http_client = http_client

    def import_issue(self, owner: str, repository: str, issue: IssueImportRequest) -> IssueImportStatusResponse:
        response = self._http_client.post(
            url=f"/repos/{owner}/{repository}/import/issues",
            content=(issue.model_dump_json(exclude_none=True)),
        )
        return IssueImportStatusResponse.model_validate(response.json())

    def get_status(self, url: str | HttpUrl) -> IssueImportStatusResponse:
        response = self._http_client.get(str(url) if isinstance(url, HttpUrl) else url)
        return IssueImportStatusResponse.model_validate(response.json())

    def get_status_multiple(self, owner: str, repository: str, date: datetime) -> list[IssueImportStatusResponse]:
        response = self._http_client.get(
            url=f"/repos/{owner}/{repository}/import/issues",
            params={"since": date.isoformat()},
        )
        return [IssueImportStatusResponse.model_validate(item) for item in response.json()]
