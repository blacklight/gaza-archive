import asyncio
import importlib
import os
from logging import getLogger
from threading import Event, Thread

import uvicorn
from fastapi import HTTPException, Request

from ..config import Config
from ..db import Db
from ._app import app, render_index
from ._ctx import get_ctx

log = getLogger(__name__)


class ApiServer(Thread):
    """
    API server class.
    """

    _routes_dir = os.path.join(os.path.dirname(__file__), "_routes")

    def __init__(self, config: Config, db: Db, *_, **__):
        super().__init__()
        self.config = config
        self.db = db
        self.server: uvicorn.Server | None = None
        self.shutdown_event = Event()  # Event to signal shutdown
        self.should_stop = False
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

        # Add catch-all route for serving the Vue.js app AFTER all other routes
        @app.get("/{full_path:path}", include_in_schema=False)
        async def _(request: Request, full_path: str):
            # Only serve the Vue app for non-API routes
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")

            return render_index(request)

    def run(self):
        super().run()
        try:
            config = uvicorn.Config(
                app,
                host=self.config.api_host,
                port=self.config.api_port,
                log_level="debug" if self.config.debug else "info",
            )

            self.server = uvicorn.Server(config=config)
            log.info(
                "Starting API server on %s:%d",
                self.config.api_host,
                self.config.api_port,
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server_task = loop.create_task(self.server.serve())

            async def wait_for_shutdown():
                await asyncio.get_event_loop().run_in_executor(
                    None, self.shutdown_event.wait
                )
                if self.server:
                    log.info("Shutdown signal received, stopping server...")
                    self.server.should_exit = True
                    await server_task

            shutdown_task = loop.create_task(wait_for_shutdown())
            # Run until server stops or shutdown is requested
            loop.run_until_complete(
                asyncio.gather(server_task, shutdown_task, return_exceptions=True)
            )
        except KeyboardInterrupt:
            pass
        except Exception as e:
            log.error("Failed to start API server: %s", e)
            raise

    def stop(self):
        """Stop the server gracefully."""
        log.info("Stopping API server...")
        self.should_stop = True
        if self.server:
            self.server.should_exit = True
        self.shutdown_event.set()

    def join(self, timeout=None):
        """Wait for the thread to finish."""
        self.stop()
        super().join(timeout)


__all__ = ["ApiServer", "get_ctx", "app"]
