# sqlalchemy14
sqlalchemy1.4への移行を検証する

# setup
``` shell
poetry install
```

# envirnoment
`.env`に次の環境変数を定義する。testnetなど、テスト環境のクレデンシャルを利用しないと、実際に取引が行われるため注意。

- API_BYBIT_TEST_API_KEY
- API_BYBIT_TEST_API_SECRET