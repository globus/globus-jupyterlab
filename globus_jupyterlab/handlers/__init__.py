import os

from notebook.utils import url_path_join

from tornado.web import StaticFileHandler
from globus_jupyterlab.handlers import login, config


def setup_handlers(web_app, url_path):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    handlers = (login, config)

    # Prepend the base_url so that it works in a JupyterHub setting
    for handler_module in handlers:
        for url, api_handler in handler_module.default_handlers:
            handlers.append((url_path_join(base_url, url_path, url), api_handler))

    web_app.add_handlers(host_pattern, handlers)

    # Prepend the base_url so that it works in a JupyterHub setting
    doc_url = url_path_join(base_url, url_path, "public")
    doc_dir = os.getenv(
        "JLAB_SERVER_EXAMPLE_STATIC_DIR",
        os.path.join(os.path.dirname(__file__), "public"),
    )
    handlers = [("{}/(.*)".format(doc_url), StaticFileHandler, {"path": doc_dir})]
    web_app.add_handlers(".*$", handlers)
