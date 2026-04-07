"""루트 실행 호환을 위한 엔트리포인트 래퍼."""

from __future__ import annotations

import os
import sys


def main() -> None:
    """src 디렉터리를 import 경로에 추가한 뒤 실제 main()을 실행한다."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from pipeline import main as pipeline_main

    pipeline_main()


if __name__ == "__main__":
    main()
