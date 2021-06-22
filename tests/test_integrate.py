import os

import pytest


@pytest.mark.docker
def test_integrate(request):
    env = request.config.getoption("--env")
    assert env != "local"


@pytest.mark.docker
def test_env(request):
    host = os.getenv("POSTGRES_HOST", None)
    db = os.getenv("POSTGRES_DB", None)
    user = os.getenv("POSTGRES_USER", None)
    pw = os.getenv("POSTGRES_PASSWORD", None)

    assert host
    assert db
    assert user
    assert pw
