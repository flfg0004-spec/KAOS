"""Tests for lib.feature_flags — including new UA flags."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_new_flags_exist():
    from lib.feature_flags import DEFAULT_FLAGS

    for flag in ("use_incremental_analysis", "use_enhanced_parallelism", "use_knowledge_tour", "use_domain_mapper"):
        assert flag in DEFAULT_FLAGS, f"Missing flag: {flag}"


def test_new_flags_default_true():
    from lib.feature_flags import is_enabled

    for flag in ("use_incremental_analysis", "use_enhanced_parallelism", "use_knowledge_tour", "use_domain_mapper"):
        assert is_enabled(flag) is True, f"{flag} should default to True"


def test_enable_new_flags():
    from lib.feature_flags import disable, enable, is_enabled

    for flag in ("use_incremental_analysis", "use_enhanced_parallelism", "use_knowledge_tour", "use_domain_mapper"):
        enable(flag)
        assert is_enabled(flag) is True
        disable(flag)
        assert is_enabled(flag) is False


def test_new_flags_in_list():
    from lib.feature_flags import list_flags

    flags = list_flags()
    for flag in ("use_incremental_analysis", "use_enhanced_parallelism", "use_knowledge_tour", "use_domain_mapper"):
        assert flag in flags
