#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
KST = timezone(timedelta(hours=9))


def stamp_repo(repo_dir: Path) -> tuple[str, str]:
    now_utc = datetime.now(UTC).replace(microsecond=0)
    version = now_utc.strftime('%Y%m%dT%H%M%SZ')
    label = now_utc.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')

    index_path = repo_dir / 'index.html'
    version_path = repo_dir / 'version.json'
    service_worker_path = repo_dir / 'service-worker.js'

    index_text = index_path.read_text(encoding='utf-8')
    index_text, app_count = re.subn(
        r"const APP_VERSION = '[^']+';",
        f"const APP_VERSION = '{version}';",
        index_text,
        count=1,
    )
    index_text, label_count = re.subn(
        r"const APP_VERSION_LABEL = '[^']+';",
        f"const APP_VERSION_LABEL = '{label}';",
        index_text,
        count=1,
    )
    if app_count != 1 or label_count != 1:
        raise RuntimeError('index.html version markers not found exactly once')
    index_path.write_text(index_text, encoding='utf-8')

    service_worker_text = service_worker_path.read_text(encoding='utf-8')
    service_worker_text, sw_count = re.subn(
        r"const CACHE_NAME = 'kmle-planner-[^']+';",
        f"const CACHE_NAME = 'kmle-planner-{version}';",
        service_worker_text,
        count=1,
    )
    if sw_count != 1:
        raise RuntimeError('service-worker.js cache marker not found exactly once')
    service_worker_path.write_text(service_worker_text, encoding='utf-8')

    version_path.write_text(
        json.dumps({'version': version, 'label': label}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )

    return version, label


def main() -> int:
    parser = argparse.ArgumentParser(description='Sync deploy version metadata for the KMLE planner.')
    parser.add_argument(
        '--repo-dir',
        default=str(Path(__file__).resolve().parents[1]),
        help='Path to the repo root containing index.html, version.json, and service-worker.js',
    )
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir).expanduser().resolve()
    version, label = stamp_repo(repo_dir)
    print(json.dumps({'repo': str(repo_dir), 'version': version, 'label': label}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
