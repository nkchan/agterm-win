"""Entry point for `python -m agterm`."""
from __future__ import annotations
import logging
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gio, Gtk

from .window import AgTermWindow

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")


def main() -> int:
    app = Gtk.Application(
        application_id="com.github.nkchan.agterm_win",
        flags=Gio.ApplicationFlags.FLAGS_NONE,
    )
    app.connect("activate", lambda a: AgTermWindow(a).present())
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
