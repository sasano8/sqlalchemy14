import pytest

ENV_VAL_NAME = "TEST_ENV"

envs = {"local": 0, "docker": 1}


def pytest_addoption(parser):
    """Add pytest command options."""
    parser.addoption("--env", action="store", default="local", help="set env")


def pytest_collection_modifyitems(config, items):
    """実行環境を満たさないテストをスキップさせる"""
    current_env = config.getoption("--env")
    skip_env = pytest.mark.skip(reason="skip environment")
    for item in items:
        for env_keyword in envs:
            if env_keyword in item.keywords:
                is_run = envs[current_env] >= envs[env_keyword]
                if not is_run:
                    item.add_marker(skip_env)
