def test_version():
    import sqlite3

    con = sqlite3.connect(":memory:")
    version = con.execute("select sqlite_version()").fetchone()

    sqlite3.version == "2.6.0"

    # python3.9.5にはsqlite 3.31が同梱されている
    # returningは3.35.4から動作する
    sqlite3.sqlite_version_info[0] >= 3
    sqlite3.sqlite_version_info[1] >= 35
    sqlite3.sqlite_version_info[2] >= 4
