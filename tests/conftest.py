import pytest

ENV_VAL_NAME = "TEST_ENV"

envs = {"local": 0, "docker": 1}


def pytest_addoption(parser):
    """Add pytest command options."""
    parser.addoption("--env", action="store", default="docker", help="set env")


def pytest_collection_modifyitems(config, items):
    """実行環境を満たさないテストをスキップさせる"""
    current_env = config.getoption("--env")

    for item in items:
        for env_keyword in envs:
            if env_keyword in item.keywords:
                is_run = envs[current_env] >= envs[env_keyword]
                if not is_run:
                    skip_env = pytest.mark.skip(reason=f"skip env:{env_keyword}")
                    item.add_marker(skip_env)


@pytest.fixture(scope="session")
def event_loop(request):
    """
    pytest asyncioはテスト毎にループを作成する。
    そうすると、セッションやファンクションなど異なるスコープでイベントループが作成され、エラーが生じる。
    そのため、ここで１つのイベントループに依存し、コントロールを行う。
    """
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
