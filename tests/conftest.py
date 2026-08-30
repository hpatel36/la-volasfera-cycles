import pytest

from app import create_app


@pytest.fixture()
def client():
    application = create_app({"TESTING": True})

    with application.test_client() as test_client:
        yield test_client

