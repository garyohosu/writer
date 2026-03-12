from __future__ import annotations

import sys
import traceback

from writer.bootstrap import build_runtime


def main() -> None:
    pipeline, _ = build_runtime()
    pipeline.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
