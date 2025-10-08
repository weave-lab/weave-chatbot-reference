#!/usr/bin/env python3
"""
Direct test of the Corporate Jargon Assistant
"""

from corporate_jargon_assistant import corporate_jargon_assistant


def test_direct():
    test_phrase = "leverage our existing synergies"
    print(f"Testing: {test_phrase}")
    result = corporate_jargon_assistant(test_phrase)
    print(f"Result: {result}")


if __name__ == "__main__":
    test_direct()
