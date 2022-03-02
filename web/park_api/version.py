import subprocess

from django.conf import settings


def get_commit_hash() -> str:
    """
    Return current commit hash

    or sequence of zeros if no git or repo is available
    """
    try:
        return subprocess.check_output(
            ["git", "rev-list", "--branches", "--max-count=1"],
            cwd=settings.BASE_DIR,
        ).strip().decode("utf-8")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        return "0" * 40
