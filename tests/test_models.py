import json
from datetime import timedelta
from pathlib import Path

import pytest

from github_issues_import.models import IssueImportRequest, IssueImportStatusResponse

from .utils import get_fixture, get_fixtures


@pytest.mark.parametrize("fixture", get_fixtures("request-*.json"))
def test_issue_import_request(fixture: Path):
    IssueImportRequest.model_validate_json(get_fixture(fixture))


@pytest.mark.parametrize("fixture", get_fixtures("response-single-*.json"))
def test_issue_import_status_response(fixture: Path):
    response = IssueImportStatusResponse.model_validate_json(get_fixture(fixture))
    if response.created_at is not None:
        assert response.created_at.tzinfo.utcoffset(response.created_at) == timedelta(hours=-7)


def test_issue_import_status_multiple():
    data = json.loads(get_fixture("response-multiple-check-status-of-multiple-issues.json"))
    assert len(data) == 1
    for response in data:
        IssueImportStatusResponse.model_validate(response)
