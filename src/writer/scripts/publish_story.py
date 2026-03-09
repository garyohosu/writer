from __future__ import annotations

from writer.bootstrap import build_runtime
from writer.publish_story_script import PublishStoryScript


def main() -> None:
    _, publish_service = build_runtime()
    script = PublishStoryScript(publish_service)
    script.run()


if __name__ == "__main__":
    main()
