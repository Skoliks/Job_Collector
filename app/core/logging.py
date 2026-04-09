import logging

def logger_setup():
    logging.basicConfig(
        level=logging.INFO, 
        filename="py_log.log",
        filemode="w",
        format= "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )