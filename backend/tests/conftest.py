"""
conftest.py — pytest configuration for SupportNova test suite.
Patches slow imports (sentence_transformers, faiss) for unit tests.
"""
import sys
from unittest.mock import MagicMock, patch

# ── Patch slow/optional heavy ML libraries so tests don't hang ────────────────
# sentence_transformers
if "sentence_transformers" not in sys.modules:
    st_mock = MagicMock()
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]] * 10
    st_mock.SentenceTransformer.return_value = mock_model
    sys.modules["sentence_transformers"] = st_mock

# faiss
if "faiss" not in sys.modules:
    faiss_mock = MagicMock()
    index_mock = MagicMock()
    index_mock.ntotal = 0
    index_mock.search.return_value = ([[]], [[]])
    faiss_mock.IndexFlatIP.return_value = index_mock
    sys.modules["faiss"] = faiss_mock

# PyMuPDF
if "fitz" not in sys.modules:
    sys.modules["fitz"] = MagicMock()

# pdfplumber
if "pdfplumber" not in sys.modules:
    sys.modules["pdfplumber"] = MagicMock()

# python-docx
if "docx" not in sys.modules:
    sys.modules["docx"] = MagicMock()

import pytest
from backend.security.rate_limiter import reset_rate_limits

@pytest.fixture(autouse=True)
def _clear_rate_limits_before_test():
    reset_rate_limits()

