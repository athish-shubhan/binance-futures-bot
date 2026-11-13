import logging
import sys


def setup(path="bot.log"):
    """Return the shared "bot" logger: everything to a file, warnings to stdout.

    Safe to call more than once; handlers are attached only the first time, so
    repeated calls do not duplicate every log line.
    """
    lg = logging.getLogger("bot")
    lg.setLevel(logging.DEBUG)
    if lg.handlers:
        return lg
    fh = logging.FileHandler(path)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.WARNING)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    lg.addHandler(fh)
    lg.addHandler(sh)
    return lg
