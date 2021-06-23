from inspect import isclass

from .analyzer import get_delete, get_insert, get_select, get_update, get_upsert


class Sql:
    def __init__(self, cls):
        assert isclass(cls)
        self.cls = cls

    def insert(self, **values):
        return get_insert(self.cls).values(**values)

    def upsert(self, **values):
        """挿入または更新を行います。衝突はプライマリキーのみ許可します。（単なるユニークキーは許可しません）"""
        return get_upsert(self.cls).values(**values)

    def update(self, **values):
        return get_update(self.cls).values(**values)

    def select(self):
        return get_select(self.cls)

    def delete(self):
        return get_delete(self.cls)

    def insert_many(cls):
        raise NotImplementedError()

    def upsert_many(cls):
        raise NotImplementedError()
