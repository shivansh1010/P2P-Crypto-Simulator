"""This module is used to initialize the logger for the application."""
import logging
import coloredlogs


class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """
    def filter(self, record):
        from network import Network  # Avoid circular import
        record.simulation_time = round(Network.instance.time if Network.instance else 0.00, 2)
        record.simulation_time = f'{record.simulation_time:.2f}'
        return True

log = logging.getLogger('main')
log.addFilter(ContextFilter())


def init_logger(level):
    """initialize logger"""
    log_format = '[%(simulation_time)7s] %(levelname)-8s:  %(message)s'
    coloredlogs.install(fmt=log_format, level=level, logger=log)
    log.handlers[0].flush()
