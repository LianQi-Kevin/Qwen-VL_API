import logging


class ColorHandler(logging.StreamHandler):
    COLOR_MAP = {logging.DEBUG: "\033[0;37m", logging.INFO: "\033[0;36m", logging.WARNING: "\033[0;33m",
                 logging.ERROR: "\033[0;31m", logging.CRITICAL: "\033[0;35m"}

    def emit(self, record):
        # 根据日志等级添加颜色
        color = self.COLOR_MAP.get(record.levelno)
        message = self.format(record)
        self.stream.write(f"{color}{message}\033[0m\n")


def log_set(log_level=logging.INFO, log_save: bool = False, save_path: str = "log.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # console
    handler = ColorHandler()
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # file
    if log_save:
        file_header = logging.FileHandler(save_path, encoding="utf-8")
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
