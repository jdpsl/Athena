#!/usr/bin/env python3
"""Test the skills system."""

from pathlib import Path
from athena.skills.loader import SkillLoader
from athena.skills.skill import Skill

def test_skill_loading():
    """Test that skills can be loaded from .athena/skills/."""
    print("Testing Skill System\n")
    print("=" * 60)

    # Create skill loader
    loader = SkillLoader(working_directory=".")

    # Discover skills
    print("\n1. Discovering skills...")
    skills = loader.discover_skills()

    print(f"   Found {len(skills)} skill(s)")

    if not skills:
        print("   ❌ No skills found!")
        print("\n   Expected skills in .athena/skills/:")
        print("   - security-audit/SKILL.md")
        print("   - code-reviewer/SKILL.md")
        return False

    # List discovered skills
    print("\n2. Loaded skills:")
    for name, skill in skills.items():
        print(f"\n   ✓ {name}")
        print(f"     Description: {skill.description[:80]}...")
        print(f"     Allowed tools: {', '.join(skill.allowed_tools) if skill.allowed_tools else 'All'}")
        print(f"     Path: {skill.skill_path}")

    # Test individual skill loading
    print("\n3. Testing individual skill loading...")

    # Test security-audit skill
    if "security-audit" in skills:
        skill = skills["security-audit"]
        print(f"\n   ✓ security-audit skill loaded")
        print(f"     Name: {skill.name}")
        print(f"     Has instructions: {len(skill.instructions) > 0}")
        print(f"     Instruction length: {len(skill.instructions)} chars")
        print(f"     Allowed tools: {skill.allowed_tools}")

        # Test system prompt generation
        prompt = skill.get_system_prompt()
        print(f"     System prompt length: {len(prompt)} chars")
        print(f"     Starts with: {prompt[:50]}...")
    else:
        print("   ❌ security-audit skill not found")

    # Test code-reviewer skill
    if "code-reviewer" in skills:
        skill = skills["code-reviewer"]
        print(f"\n   ✓ code-reviewer skill loaded")
        print(f"     Name: {skill.name}")
        print(f"     Has instructions: {len(skill.instructions) > 0}")
        print(f"     Instruction length: {len(skill.instructions)} chars")
        print(f"     Allowed tools: {skill.allowed_tools}")
    else:
        print("   ❌ code-reviewer skill not found")

    # Test get_skill method
    print("\n4. Testing get_skill() method...")
    skill = loader.get_skill("security-audit")
    if skill:
        print(f"   ✓ get_skill('security-audit') works")
    else:
        print(f"   ❌ get_skill('security-audit') returned None")

    skill = loader.get_skill("nonexistent")
    if skill is None:
        print(f"   ✓ get_skill('nonexistent') correctly returns None")
    else:
        print(f"   ❌ get_skill('nonexistent') should return None")

    print("\n" + "=" * 60)
    print("✅ All skill system tests passed!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = test_skill_loading()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
