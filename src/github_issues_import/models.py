from enum import StrEnum, auto

from pydantic import AwareDatetime, ConfigDict, HttpUrl
from pydantic import BaseModel as PydanticBaseModel

DEFAULT_CONFIG = ConfigDict(
    populate_by_name=True,
    validate_default=True,
    validate_assignment=True,
    frozen=True,
)


class BaseModel(PydanticBaseModel):
    model_config = DEFAULT_CONFIG


class Issue(BaseModel):
    title: str
    body: str
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None
    closed_at: AwareDatetime | None = None
    assignee: str | None = None
    milestone: int | None = None
    closed: bool | None = None
    labels: list[str] | None = None


class Comment(BaseModel):
    body: str
    created_at: AwareDatetime | None = None


class IssueImportRequest(BaseModel):
    issue: Issue
    comments: list[Comment] | None = None


class IssueImportError(BaseModel):
    location: str
    resource: str
    field: str | None
    value: str | None
    code: str


class IssueImportStatus(StrEnum):
    PENDING = auto()
    IMPORTED = auto()
    FAILED = auto()


class IssueImportStatusResponse(BaseModel):
    id: int
    status: IssueImportStatus
    url: HttpUrl
    import_issues_url: HttpUrl
    repository_url: HttpUrl

    issue_url: HttpUrl | None = None  # if "imported"

    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None

    # if "failed"
    errors: list[IssueImportError] | None = None
