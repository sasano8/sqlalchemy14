import pytest


@pytest.mark.docker
def test_integrate(request):
    env = request.config.getoption("--env")
    assert env != "local"
