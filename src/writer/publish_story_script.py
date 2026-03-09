from __future__ import annotations

import argparse
import datetime

from writer.services.publish_service import PublishService


class PublishStoryScript:
    """Standalone script entry point for manually publishing a story by slug."""

    def __init__(self, publish_service: PublishService) -> None:
        self.publish_service = publish_service

    def run(self) -> None:
        """Parse CLI arguments and trigger PublishService.run_from_master()."""
        parser = argparse.ArgumentParser(
            description="Manually publish a story by slug."
        )
        parser.add_argument("slug", help="Story slug to publish")
        parser.add_argument(
            "--date",
            default=datetime.date.today().isoformat(),
            help="Publication date (YYYY-MM-DD, default: today)",
        )
        args = parser.parse_args()
        commit_hash = self.publish_service.run_from_master(args.slug, args.date)
        print(f"Published: {args.slug} @ {commit_hash}")
