from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

import requests

from backend.data.core_publication_repository import CorePublicationRepository


SUPPORTED_EXTENSIONS = {".csv", ".json", ".jsonl"}
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s<>\"]+", re.IGNORECASE)
REQUEST_TIMEOUT_SECONDS = 15
