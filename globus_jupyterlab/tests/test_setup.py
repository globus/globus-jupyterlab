from unittest.mock import Mock
from globus_jupyterlab.handlers import setup_handlers, get_handlers
import tornado.web


def test_get_handlers():
    mock_handler = Mock()
    handlers = [("my_handler_path", mock_handler, {}, "my_handler")]
    mock_module = Mock()
    mock_module.default_handlers = handlers
    handler = get_handlers([mock_module], "/base", "path")[0]
    assert handler.name == "my_handler"


def test_setup_handlers():
    mock_app = Mock(settings=dict(base_url="/base"))
    setup_handlers(mock_app, "/mount")
    assert mock_app.add_handlers.called
