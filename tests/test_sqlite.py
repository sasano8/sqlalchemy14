def test_version():
    import sqlite3

    con = sqlite3.connect(":memory:")
    version = con.execute("select sqlite_version()").fetchone()

    # returningは3.35から動作する
    sqlite3.version == "2.6.0"
    version[0] == "3.31.1"
