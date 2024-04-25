import logging
import tqdm

# custom logger from https://stackoverflow.com/questions/38543506/change-logging-print-function-to-tqdm-write-so-logging-doesnt-interfere-wit
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)  

# logging

def get_logger():
    # name of logger
    log = logging.getLogger("logging")
    log.setLevel(logging.INFO)

    if not log.hasHandlers():
        # own logs handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)

    # only printout handlers, not log
    log.propagate = False    
    
    return log

log = get_logger()

#logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
#log = logging.getLogger('spam.sqlalchemy.engine')
#log.setLevel(logging.INFO)
#log.addHandler(TqdmLoggingHandler())
