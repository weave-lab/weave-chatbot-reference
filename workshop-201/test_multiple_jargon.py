#!/usr/bin/env python3
"""
Test the corporate jargon assistant with multiple examples
"""

from corporate_jargon_assistant import corporate_jargon_assistant


def test_examples():
    examples = [
        "we need to circle back and touch base on leveraging synergies",
        "let's move the needle on our core competencies",
        "we need stakeholder buy-in for this paradigm shift",
        "right-size the team and optimize our bandwidth",
    ]

    for example in examples:
        print(f"\n🏢 Original: {example}")
        result = corporate_jargon_assistant(example)
        print(f"💬 {result}")
        print("-" * 60)


if __name__ == "__main__":
    test_examples()
