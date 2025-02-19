import json
import re
from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
import pytest
from httpx._config import DEFAULT_TIMEOUT_CONFIG
from pydantic import HttpUrl
from pytest_httpx import HTTPXMock

from github_issues_import.client import ApiClient, HttpClient
from github_issues_import.models import IssueImportRequest, IssueImportStatus, IssueImportStatusResponse

from .utils import get_fixture

GITHUB_TOKEN = "ghp_abc123"


@pytest.fixture
def api_client():
    return ApiClient(http_client=HttpClient(token=GITHUB_TOKEN))


def test_init(api_client: ApiClient):
    assert api_client


def test_timeout_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        match_extensions={
            "timeout": {
                "connect": DEFAULT_TIMEOUT_CONFIG.connect,
                "read": DEFAULT_TIMEOUT_CONFIG.read,
                "write": DEFAULT_TIMEOUT_CONFIG.write,
                "pool": DEFAULT_TIMEOUT_CONFIG.pool,
            }
        },
        status_code=httpx.codes.BAD_GATEWAY,
    )
    with pytest.raises(httpx.HTTPStatusError):
        ApiClient(http_client=HttpClient(token=GITHUB_TOKEN)).get_status_multiple("foo", "bar", datetime.now(tz=UTC))


def test_timeout_set(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        match_extensions={"timeout": {"connect": 123, "read": 123, "write": 123, "pool": 123}},
        status_code=httpx.codes.BAD_GATEWAY,
    )
    with pytest.raises(httpx.HTTPStatusError):
        ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, timeout=123)).get_status_multiple(
            "foo", "bar", datetime.now(tz=UTC)
        )


def test_base_url(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(r"^https://test/repos/foo/bar/import/issues"),
        text=get_fixture("response-multiple-check-status-of-multiple-issues.json"),
    )
    ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, base_url="https://test")).get_status_multiple(
        "foo", "bar", datetime.now(tz=UTC)
    )


def test_event_hooks(monkeypatch, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=get_fixture("response-multiple-check-status-of-multiple-issues.json"))

    mock = MagicMock()
    monkeypatch.setattr(HttpClient, "log_github_api_request", mock)

    ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, base_url="https://test", event_hooks={})).get_status_multiple(
        "foo", "bar", datetime.now(tz=UTC)
    )
    mock.assert_not_called()


def test_raise_for_status(api_client: ApiClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=httpx.codes.BAD_GATEWAY)
    with pytest.raises(httpx.HTTPError):
        api_client.import_issue(
            "foo",
            "bar",
            IssueImportRequest.model_validate_json(get_fixture("request-issue-and-comment-fields.json")),
        )


def test_import_issue(api_client: ApiClient, httpx_mock: HTTPXMock):
    import_response = get_fixture("response-single-start-an-issue-import.json")
    import_request = get_fixture("request-start-issue-import.json")

    httpx_mock.add_response(text=import_response)

    response = api_client.import_issue(
        "owner",
        "repository",
        IssueImportRequest.model_validate_json(import_request),
    )

    assert response == IssueImportStatusResponse.model_validate_json(import_response)
    assert response.status == IssueImportStatus.PENDING

    request = httpx_mock.get_request()

    assert request.url == "https://api.github.com/repos/owner/repository/import/issues"
    assert request.headers["Authorization"] == f"Token {GITHUB_TOKEN}"
    assert json.loads(request.content) == json.loads(import_request)


def test_get_import_status(api_client: ApiClient, httpx_mock: HTTPXMock):
    import_status_response = get_fixture("response-single-check-status-of-issue-import.json")

    httpx_mock.add_response(
        url="https://api.github.com/repos/jonmagic/foo/import/issues/3",
        text=import_status_response,
    )

    response = api_client.get_status(HttpUrl("https://api.github.com/repos/jonmagic/foo/import/issues/3"))
    assert response == IssueImportStatusResponse.model_validate_json(import_status_response)


def test_get_import_status_multiple(api_client: ApiClient, httpx_mock: HTTPXMock):
    multiple_status_response = get_fixture("response-multiple-check-status-of-multiple-issues.json")
    since = datetime.now(tz=UTC)

    httpx_mock.add_response(
        url=httpx.URL(
            "https://api.github.com/repos/foo/bar/import/issues",
            params={"since": since.isoformat()},
        ),
        text=multiple_status_response,
    )

    response = api_client.get_status_multiple("foo", "bar", since)
    assert response == [IssueImportStatusResponse.model_validate(json.loads(multiple_status_response)[0])]
