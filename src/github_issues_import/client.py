import logging
from datetime import datetime

import httpx
from httpx._types import TimeoutTypes
from pydantic import HttpUrl

from .models import UNSET, IssueImportRequest, IssueImportStatusResponse

logger = logging.getLogger(__name__)


class ApiClient:
    @staticmethod
    def _log_request(request: httpx.Request):
        logger.debug(f"GitHub API Request: {request.method} {request.url} {request.content.decode()}")

    @staticmethod
    def _log_response(response: httpx.Response):
        request = response.request
        response.read()
        logger.debug(f"GitHub API Response: {request.method} {request.url} {response.status_code} {response.text}")

    def __init__(
        self,
        *,
        token: str,
        base_url: str = "https://api.github.com",
        timeout: TimeoutTypes | UNSET = UNSET,
    ):
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.golden-comet-preview+json",
                "Authorization": f"token {token}",
            },
            event_hooks={
                "request": [self._log_request],
                "response": [self._log_response, httpx.Response.raise_for_status],
            },
            **({"timeout": timeout} if timeout is not UNSET else {}),
        )

    def import_issue(self, owner: str, repository: str, issue: IssueImportRequest) -> IssueImportStatusResponse:
        response = self._client.post(
            url=f"/repos/{owner}/{repository}/import/issues",
            content=(issue.model_dump_json(exclude_none=True)),
        )
        return IssueImportStatusResponse.model_validate(response.json())

    def get_status(self, url: str | HttpUrl) -> IssueImportStatusResponse:
        response = self._client.get(str(url) if isinstance(url, HttpUrl) else url)
        return IssueImportStatusResponse.model_validate(response.json())

    def get_status_multiple(self, owner: str, repository: str, date: datetime) -> list[IssueImportStatusResponse]:
        response = self._client.get(
            url=f"/repos/{owner}/{repository}/import/issues",
            params={"since": date.isoformat()},
        )
        return [IssueImportStatusResponse.model_validate(item) for item in response.json()]
