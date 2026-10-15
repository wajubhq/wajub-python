"""Typed API resource objects."""

from __future__ import annotations

from typing import Any


class ApiObject:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApiObject:
        return cls(data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._data!r})"


class Payment(ApiObject):
    @property
    def id(self) -> str | None:
        return self._data.get("id")

    @property
    def status(self) -> str | None:
        return self._data.get("status")

    @property
    def authorization_url(self) -> str | None:
        return self._data.get("authorization_url")


class Customer(ApiObject):
    @property
    def id(self) -> str | None:
        return self._data.get("id")

    @property
    def email(self) -> str | None:
        return self._data.get("email")


class Refund(ApiObject):
    @property
    def id(self) -> str | None:
        return self._data.get("id")

    @property
    def status(self) -> str | None:
        return self._data.get("status")


class Event(ApiObject):
    @property
    def id(self) -> str | None:
        return self._data.get("id")

    @property
    def type(self) -> str | None:
        return self._data.get("type")
