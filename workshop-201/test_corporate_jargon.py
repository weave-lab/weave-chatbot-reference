#!/usr/bin/env python3
"""
Test script for the Corporate Jargon De-Goobler assistant
"""

from corporate_jargon_assistant import corporate_jargon_assistant


def test_corporate_jargon():
    """Test the corporate jargon assistant with example text"""

    # Original example from the user request
    test_text = "We need to leverage our synergies to actionize a paradigm shift and touch base offline."

    print("🔍 Testing Corporate Jargon De-Goobler")
    print("=" * 50)
    print(f"Original: {test_text}")
    print("\nTranslation:")

    try:
        result = corporate_jargon_assistant(test_text)
        print(result)
        print("\n" + "=" * 50)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during test: {e}")

    # Additional test examples
    additional_tests = [
        "Let's circle back on this initiative and ensure we have stakeholder buy-in before we move the needle.",
        "We need to right-size the team and optimize our bandwidth for maximum ROI.",
        "This is a game changer that will drive synergies across our core competencies.",
    ]

    print("\n🧪 Additional Test Cases:")
    print("=" * 50)

    for i, test in enumerate(additional_tests, 1):
        print(f"\nTest {i}: {test}")
        print("Translation:")
        try:
            result = corporate_jargon_assistant(test)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_corporate_jargon()
