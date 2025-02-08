from pathlib import Path

import pytest


def get_fixture(fixture: Path | str) -> str:
    return (Path(__file__).parent / "fixtures" / fixture).read_text()


def get_fixtures(pattern: str) -> list:
    return [
        pytest.param(
            path,
            id=path.name,
        )
        for path in (Path(__file__).parent / "fixtures").glob(pattern)
    ]
