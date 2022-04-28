import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "basic": {
                "format": "[%(levelname)s] " "%(name)s::%(funcName)s() %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "basic",
            }
        },
        "loggers": {
            "globus_jupyterlab": {"level": "DEBUG", "handlers": ["console"]},
            "tornado.access": {"level": "WARNING", "handlers": ["console"]},
            "tornado.application": {"level": "DEBUG", "handlers": ["console"]},
            "tornado.general": {"level": "WARNING", "handlers": ["console"]},
            "globus_sdk": {"level": "INFO", "handlers": ["console"]},
        },
    }
)
