from __future__ import annotations

from writer.bootstrap import build_runtime


def main() -> None:
    pipeline, _ = build_runtime()
    pipeline.run()


if __name__ == "__main__":
    main()
