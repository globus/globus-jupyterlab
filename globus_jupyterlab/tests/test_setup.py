
from unittest.mock import Mock
from globus_jupyterlab.handlers import setup_handlers, get_handlers


def test_get_handlers():
    mock_handler = Mock()
    handlers = [
        ('my_handler_path', mock_handler)
    ]
    mock_module = Mock()
    mock_module.default_handlers = handlers
    processed_handlers = get_handlers([mock_module], '/base', 'path')

    assert processed_handlers == [('/base/path/my_handler_path', mock_handler)]


def test_setup_handlers():
    mock_app = Mock(settings=dict(base_url='/base'))
    setup_handlers(mock_app, '/mount')
    assert mock_app.add_handlers.called
