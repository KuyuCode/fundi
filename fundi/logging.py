from logging import getLogger

_root_logger = getLogger("fundi")


def get_logger(name: str):
    return _root_logger.getChild(name)
