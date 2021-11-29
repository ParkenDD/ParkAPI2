import datetime
import sys


def log(*args, **kwargs):
    """
    print() to stderr.
    """
    kwargs["file"] = sys.stderr
    print(datetime.datetime.now(), *args, **kwargs)
