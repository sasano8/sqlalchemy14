import os

import pytest


@pytest.fixture(scope="session")
def db_config():
    host = os.getenv("POSTGRES_HOST", None)
    db = os.getenv("POSTGRES_DB", None)
    user = os.getenv("POSTGRES_USER", None)
    pw = os.getenv("POSTGRES_PASSWORD", None)

    return host, db, user, pw


@pytest.mark.docker
def test_integrate(request):
    env = request.config.getoption("--env")
    assert env != "local"


@pytest.mark.docker
def test_env(db_config):
    host, db, user, pw = db_config

    assert host
    assert db
    assert user
    assert pw
