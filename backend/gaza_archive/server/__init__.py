import importlib
import os
from dataclasses import dataclass
from logging import getLogger
from threading import Thread

import uvicorn

from ..config import Config
from ..db import Db
from ._app import app

log = getLogger(__name__)


@dataclass
class Context:
    """
    API server context.
    """

    config: Config
    db: Db


class ApiServer(Thread):
    """
    API server class.
    """

    _routes_dir = os.path.join(os.path.dirname(__file__), "_routes")

    def __init__(self, config: Config, db: Db, *_, **__):
        global ctx  # pylint: disable=global-statement

        super().__init__()
        self.config = config
        self.db = db
        ctx = Context(config=config, db=db)
        self._init_routes()

    def _init_routes(self):
        # Dynamically import and include routers
        for filename in os.listdir(self._routes_dir):
            filename = os.path.basename(filename)
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = (
                    f"._routes.{filename[:-3]}"  # Remove ".py" from the filename
                )
                module = importlib.import_module(module_name, package=__package__)

                # Check if the module has a `router` attribute
                if hasattr(module, "router"):
                    app.include_router(module.router)

    def run(self):
        super().run()
        try:
            uvicorn.run(
                app,
                host=self.config.api_host,
                port=self.config.api_port,
                log_level="debug" if self.config.debug else "info",
            )
        except KeyboardInterrupt:
            pass
        except Exception as e:
            log.error("Failed to start API server: %s", e)
            raise


# This will be initialized in ApiServer before the routes are imported
ctx: Context = None  # type: ignore[assignment]
