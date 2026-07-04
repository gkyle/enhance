"""Static mount that serves the preview cache dir over http://127.0.0.1.

Serving previews via http (rather than file://) lets the renderer keep
`webSecurity` enabled and avoids a custom protocol handler. The mount is scoped
to the preview cache directory only.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from enhance.server.preview import CACHE_URL_PREFIX, ensure_cache_dir


def mount_cache(app: FastAPI) -> None:
    cache_dir = ensure_cache_dir()
    app.mount(CACHE_URL_PREFIX, StaticFiles(directory=cache_dir), name="cache")
