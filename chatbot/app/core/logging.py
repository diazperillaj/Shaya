import logging
import sys


def setup_logging() -> None:
    """
    Logging estructurado a consola. Los errores de tools se reportan con
    logger.exception (traceback completo + tool + motivo), según la norma
    de calidad del proyecto: nunca un 500 silencioso por una tool fallida.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

    # Ruido de librerías
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


logger = logging.getLogger("chatbot")
