import ctypes
import logging
import os


# Windows CMD颜色
class Colors:
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    YELLOW = 6
    WHITE = 7


class ColorHandler(logging.StreamHandler):
    if os.name == 'nt':
        # Windows
        COLOR_MAP = {logging.DEBUG: Colors.WHITE, logging.INFO: Colors.CYAN, logging.WARNING: Colors.YELLOW,
                     logging.ERROR: Colors.RED, logging.CRITICAL: Colors.MAGENTA, 'DEFAULT': Colors.WHITE}
    else:
        # Unix/Linux
        COLOR_MAP = {logging.DEBUG: "\033[0;37m", logging.INFO: "\033[0;36m", logging.WARNING: "\033[0;33m",
                     logging.ERROR: "\033[0;31m", logging.CRITICAL: "\033[0;35m", 'DEFAULT': "\033[0;37m"}

    def emit(self, record):
        # 根据日志等级添加颜色
        color = self.COLOR_MAP.get(record.levelno, self.COLOR_MAP['DEFAULT'])
        if os.name == 'nt':
            # Windows
            ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), color)
            message = self.format(record)
            self.stream.write(f"{message}\n")
            ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11),
                                                           Colors.WHITE)  # Reset to white
        else:
            # Unix/Linux
            message = self.format(record)
            self.stream.write(f"{color}{message}\033[0m\n")


def log_set(log_level=logging.INFO, log_save: bool = False, save_path: str = "log.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Remove all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # console
    handler = ColorHandler()
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # file
    if log_save:
        mode = 'a' if os.path.exists(save_path) else 'w'
        file_header = logging.FileHandler(save_path, mode, encoding="utf-8")
        file_header.setLevel(log_level)
        file_header.setFormatter(formatter)
        logger.addHandler(file_header)


if __name__ == '__main__':
    log_set(logging.DEBUG, log_save=True)
    # logging test
    logging.debug("debug msg")
    logging.info("info msg")
    logging.warning("warning msg")
    logging.error("error msg")
    logging.critical("critical msg")
