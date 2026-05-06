"""
pytest 収集より前に DATABASE_URL を差し替える。

test_api の setup_module が drop_all するため、本番と同じ sqlite ファイルを
指しているとデータが全消去される。Docker で `compose run backend pytest` した
場合も同じになるので、テストでは常にインメモリ DB を使う。
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
