"""Runtime configuration with safe local-development defaults."""

import os

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "jenga_session")
SESSION_ENGINEER_IDLE_MINUTES = int(os.getenv("SESSION_ENGINEER_IDLE_MINUTES", "20"))
SESSION_CUSTOMER_IDLE_MINUTES = int(os.getenv("SESSION_CUSTOMER_IDLE_MINUTES", "45"))
SESSION_ABSOLUTE_HOURS = int(os.getenv("SESSION_ABSOLUTE_HOURS", "8"))
MAX_MEDIA_BYTES = 8 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/webm"}
