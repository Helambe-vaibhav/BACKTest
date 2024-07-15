import logging
import logging.handlers
import queue
import threading

class ThreadSafeLogger:
    def __init__(self, logname, logpath):
        self.logname = logname
        self.logpath = logpath
        self.log_queue = queue.Queue()

        # Create a queue handler and set the formatter
        self.queue_handler = logging.handlers.QueueHandler(self.log_queue)

        # Create a file handler to write logs to a file
        self.file_handler = logging.FileHandler(self.logpath)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler.setFormatter(formatter)

        # Create a queue listener that listens for log records and handles them
        self.queue_listener = logging.handlers.QueueListener(self.log_queue, self.file_handler)
        self.queue_listener.start()

        # Create and configure the logger
        self.logger = logging.getLogger(self.logname)
        self.logger.setLevel(logging.DEBUG)  # Adjust the level as needed
        self.logger.addHandler(self.queue_handler)

    def get_logger(self):
        return self.logger

    def stop_listener(self):
        self.queue_listener.stop()
        self.file_handler.close()

# Usage example
# if __name__ == "__main__":
    # # Create a ThreadSafeLogger instance
    # ts_logger = ThreadSafeLogger("MyLogger", "my_log.log")
    #
    # # Get the configured logger
    # logger = ts_logger.get_logger()
    #
    # # Log some messages
    # logger.debug("This is a debug message")
    # logger.info("This is an info message")
    # logger.warning("This is a warning message")
    # logger.error("This is an error message")
    # logger.critical("This is a critical message")
    #
    # # Stop the listener and close the file handler
    # ts_logger.stop_listener()
