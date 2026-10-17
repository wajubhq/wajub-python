"""Listen API resource."""

from __future__ import annotations

import warnings

from wajub.http import BaseClient
from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions

_RETIRED = (
    "Wajub: listen.{}() is deprecated: the API no longer offers it and answers "
    "410 Gone. To receive webhooks on your machine, forward them with the Wajub "
    "CLI: `wajub listen`."
)


class ListenResource(BaseClient):
    def config(self) -> dict:
        """Deprecated: the API no longer offers it and answers 410 Gone.

        To receive webhooks on your machine, forward them with the Wajub CLI's
        ``wajub listen``.
        """
        warnings.warn(_RETIRED.format("config"), DeprecationWarning, stacklevel=2)
        return pick_resource(self.get("/listen/config"), "config", "listen")

    def auth(self, params: dict, options: RequestOptions | None = None) -> dict:
        """Deprecated: the API no longer offers it and answers 410 Gone.

        To receive webhooks on your machine, forward them with the Wajub CLI's
        ``wajub listen``.
        """
        warnings.warn(_RETIRED.format("auth"), DeprecationWarning, stacklevel=2)
        return pick_resource(self.post("/listen/auth", params, options), "auth", "listen")
