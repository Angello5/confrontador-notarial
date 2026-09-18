"""Django settings for tests only."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-for-deployment")

from config.settings import *  # noqa: F403
