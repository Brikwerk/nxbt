import logging
from datetime import datetime


def create_logger(debug=False, log_to_file=False, disable_logging=False):

    logger = logging.getLogger('nxbt')

    if disable_logging:
        null_handler = logging.NullHandler()
        logger.addHandler(null_handler)
        return logger

    if debug:
        logger.setLevel(logging.DEBUG)

    if log_to_file:
        file_handler = logging.FileHandler(f'./nxbt {datetime.now()}.log')
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        logger.addHandler(file_handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        logger.addHandler(stream_handler)

    return logger
