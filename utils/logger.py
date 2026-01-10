import logging
from typing import Optional


def get_logger(
    name: str,
    level: int = logging.INFO,
    fmt: Optional[str] = None,
) -> logging.Logger:
    """
    Возвращает настроенный logger с единым форматом.

    Параметры:
    ----------
    name : str
        Имя логгера (обычно __name__).
    level : int
        Уровень логирования (logging.INFO по умолчанию).
    fmt : str, optional
        Пользовательский формат логов.
    """

    logger = logging.getLogger(name)

    # чтобы не плодить хендлеры при повторном импорте
    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler()

    log_format = fmt or (
        "[%(asctime)s] "
        "[%(levelname)s] "
        "%(name)s: "
        "%(message)s"
    )

    formatter = logging.Formatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False

    return logger
