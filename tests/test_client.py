import json
from datetime import UTC, datetime
from http import HTTPMethod
from unittest.mock import MagicMock

import httpx
import pytest
import respx
from _pytest.monkeypatch import MonkeyPatch
from pydantic import HttpUrl

from github_issues_import.client import ApiClient, HttpClient
from github_issues_import.models import IssueImportRequest, IssueImportStatus, IssueImportStatusResponse

from .utils import get_fixture

GITHUB_TOKEN = "ghp_abc123"

RESPONSE_STATUS_MULTIPLE_ISSUES = get_fixture("response-multiple-check-status-of-multiple-issues.json")


@pytest.fixture
def api_client():
    return ApiClient(http_client=HttpClient(token=GITHUB_TOKEN))


def test_simple_client_init(api_client: ApiClient):
    assert api_client


def test_base_url_override(respx_mock: respx.mock):
    respx_mock.get(url="https://test/repos/foo/bar/import/issues").respond(text=RESPONSE_STATUS_MULTIPLE_ISSUES)

    api_client = ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, base_url="https://test"))
    api_client.get_status_multiple("foo", "bar", datetime.now(tz=UTC))


def test_headers_override(respx_mock: respx.mock):
    respx_mock.get(headers={"Foo": "Bar"}).respond(text=RESPONSE_STATUS_MULTIPLE_ISSUES)

    api_client = ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, headers={"Foo": "Bar"}))
    api_client.get_status_multiple("foo", "bar", datetime.now(tz=UTC))

    assert "Authorization" not in respx_mock.calls.last.request.headers


def test_event_hooks_override(monkeypatch: MonkeyPatch, respx_mock: respx.mock):
    respx_mock.get().respond(text=RESPONSE_STATUS_MULTIPLE_ISSUES)

    mock_log_request, mock_log_response = MagicMock(), MagicMock()
    monkeypatch.setattr(HttpClient, "log_github_api_request", mock_log_request)
    monkeypatch.setattr(HttpClient, "log_github_api_response", mock_log_response)

    api_client = ApiClient(http_client=HttpClient(token=GITHUB_TOKEN, base_url="https://test", event_hooks={}))
    api_client.get_status_multiple("foo", "bar", datetime.now(tz=UTC))

    mock_log_request.assert_not_called()
    mock_log_response.assert_not_called()


def test_event_hooks_default(monkeypatch: MonkeyPatch, respx_mock: respx.mock):
    respx_mock.post("https://api.github.com/repos/foo/bar/import/issues") % httpx.codes.BAD_GATEWAY

    mock_log_request, mock_log_response = MagicMock(), MagicMock()
    monkeypatch.setattr(HttpClient, "log_github_api_request", mock_log_request)
    monkeypatch.setattr(HttpClient, "log_github_api_response", mock_log_response)

    api_client = ApiClient(http_client=HttpClient(token=GITHUB_TOKEN))

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        api_client.import_issue(
            "foo",
            "bar",
            IssueImportRequest.model_validate_json(get_fixture("request-issue-and-comment-fields.json")),
        )
    assert "502 Bad Gateway" in str(excinfo.value)

    mock_log_request.assert_called_once()
    mock_log_response.assert_called_once()


def test_import_issue(api_client: ApiClient, respx_mock: respx.mock):
    import_response = get_fixture("response-single-start-an-issue-import.json")
    import_request = get_fixture("request-start-issue-import.json")

    respx_mock.route(
        method=HTTPMethod.POST,
        url="https://api.github.com/repos/owner/repository/import/issues",
        headers={"Authorization": f"Token {GITHUB_TOKEN}"} | HttpClient.HEADERS,
    ).respond(status_code=httpx.codes.ACCEPTED, text=import_response)

    response = api_client.import_issue(
        "owner",
        "repository",
        IssueImportRequest.model_validate_json(import_request),
    )

    assert response == IssueImportStatusResponse.model_validate_json(import_response)
    assert response.status == IssueImportStatus.PENDING


def test_get_import_status(api_client: ApiClient, respx_mock: respx.mock):
    import_status_response = get_fixture("response-single-check-status-of-issue-import.json")

    respx_mock.get("https://api.github.com/repos/jonmagic/foo/import/issues/3").respond(text=import_status_response)

    response = api_client.get_status(HttpUrl("https://api.github.com/repos/jonmagic/foo/import/issues/3"))
    assert response == IssueImportStatusResponse.model_validate_json(import_status_response)


def test_get_import_status_multiple(api_client: ApiClient, respx_mock: respx.mock):
    since = datetime.now(tz=UTC)

    respx_mock.get(
        httpx.URL(
            "https://api.github.com/repos/foo/bar/import/issues",
            params={"since": since.isoformat()},
        )
    ).respond(text=RESPONSE_STATUS_MULTIPLE_ISSUES)

    response = api_client.get_status_multiple("foo", "bar", since)
    assert response == [IssueImportStatusResponse.model_validate(json.loads(RESPONSE_STATUS_MULTIPLE_ISSUES)[0])]
