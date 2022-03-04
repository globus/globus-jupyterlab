import os
import logging

logging.basicConfig(level=logging.DEBUG)

from notebook.utils import url_path_join

from tornado.web import StaticFileHandler
from globus_jupyterlab.handlers import login, config


log = logging.getLogger(__name__)

HANDLER_MODULES = (login, config)


def get_handlers(modules, base_url, url_path) -> list:
    handlers = []
    for module in modules:
        for url, api_handler in module.default_handlers:
            mounted_url = url_path_join(base_url, url_path, url)
            log.info(f'Server Extension mounted {mounted_url}')
            handlers.append((mounted_url, api_handler))
    return handlers


def setup_handlers(web_app, url_path):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    handlers = get_handlers(HANDLER_MODULES, base_url, url_path)
    web_app.add_handlers(host_pattern, handlers)

    # Prepend the base_url so that it works in a JupyterHub setting
    doc_url = url_path_join(base_url, url_path, "public")
    doc_dir = os.getenv(
        "JLAB_SERVER_EXAMPLE_STATIC_DIR",
        os.path.join(os.path.dirname(__file__), "public"),
    )
    handlers = [("{}/(.*)".format(doc_url), StaticFileHandler, {"path": doc_dir})]
    web_app.add_handlers(".*$", handlers)
