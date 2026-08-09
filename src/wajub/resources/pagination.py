"""Pagination helpers for list endpoints."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_list


@dataclass
class PagedResult:
    data: list[dict[str, Any]]
    meta: dict[str, Any] | None
    has_more: bool
    _fetch_page: Callable[[int], "PagedResult"]

    def get_next_page(self) -> "PagedResult":
        if not self.has_more:
            raise RuntimeError("No more pages available")
        next_page = int(self.meta.get("current_page", 1)) + 1 if self.meta else 2
        return self._fetch_page(next_page)

    def auto_paging_iter(self) -> Iterator[dict[str, Any]]:
        page: PagedResult | None = self
        while page is not None:
            yield from page.data
            if not page.has_more:
                break
            page = page.get_next_page()


def create_paged_list(
    client: BaseClient,
    path: str,
    plural_key: str,
    params: dict[str, Any] | None = None,
) -> PagedResult:
    def fetch_page(page_num: int) -> PagedResult:
        query = {**(params or {}), "page": page_num}
        res = client.get(path, query)
        data, meta = pick_list(res, plural_key)
        has_more = (
            meta is not None
            and meta.get("current_page") is not None
            and meta.get("last_page") is not None
            and int(meta["current_page"]) < int(meta["last_page"])
        )
        return PagedResult(data, meta, has_more, fetch_page)

    return fetch_page(int((params or {}).get("page", 1)))
