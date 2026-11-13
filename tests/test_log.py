import logging

import log


def test_setup_is_idempotent_and_writes_to_file(tmp_path):
    lg = logging.getLogger("bot")
    for h in list(lg.handlers):
        lg.removeHandler(h)
    path = tmp_path / "bot.log"
    try:
        a = log.setup(str(path))
        b = log.setup(str(path))
        assert a is b and len(a.handlers) == 2
        a.debug("hello")
        for h in a.handlers:
            h.flush()
        assert path.read_text().count("hello") == 1
    finally:
        for h in list(lg.handlers):
            h.close()
            lg.removeHandler(h)
