#!/usr/bin/env python3
"""Test loading AIFlow skill from .claude/skills/ directory."""

from athena.skills.loader import SkillLoader


def test_aiflow_skill_discovery():
    """Test that Athena can discover Claude Code skills."""
    print("\n" + "=" * 60)
    print("Testing AIFlow Skill Discovery")
    print("=" * 60)

    # Create loader for the aiflow project directory
    loader = SkillLoader(working_directory="/Users/oo/Desktop/aiflow")

    # Discover skills
    print("\n📋 Discovering skills from:")
    print("  1. ~/.athena/skills/ (global Athena)")
    print("  2. ~/.claude/skills/ (global Claude Code)")
    print("  3. /Users/oo/Desktop/aiflow/.athena/skills/ (project Athena)")
    print("  4. /Users/oo/Desktop/aiflow/.claude/skills/ (project Claude Code)")

    skills = loader.discover_skills()

    print(f"\n✓ Found {len(skills)} skill(s):")
    for name, skill in skills.items():
        print(f"\n  • {name}")
        print(f"    Description: {skill.description[:80]}...")
        print(f"    Allowed Tools: {', '.join(skill.allowed_tools) if skill.allowed_tools else 'None'}")
        print(f"    Model: {skill.model or 'Default'}")
        print(f"    Location: {skill.skill_path}")
        print(f"    Instructions: {len(skill.instructions)} chars")

    # Test getting the aiflow skill specifically
    print("\n" + "=" * 60)
    print("Testing AIFlow Skill Retrieval")
    print("=" * 60)

    aiflow_skill = loader.get_skill("aiflow")

    if aiflow_skill:
        print("\n✅ Successfully loaded 'aiflow' skill!")
        print(f"\nName: {aiflow_skill.name}")
        print(f"Description: {aiflow_skill.description}")
        print(f"Allowed Tools: {aiflow_skill.allowed_tools}")
        print(f"Model: {aiflow_skill.model}")
        print(f"\nSystem Prompt Preview:")
        print("-" * 60)
        prompt = aiflow_skill.get_system_prompt()
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 60)
    else:
        print("\n❌ Failed to load 'aiflow' skill")

    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_aiflow_skill_discovery()
