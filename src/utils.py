import logging
import os
from datetime import datetime
import sys

def setup_logger(name='bia_logger'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Handler para consola
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Asegura carpeta de logs
        os.makedirs('logs', exist_ok=True)

        # Handler para archivo (con timestamp)
        log_file = f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
