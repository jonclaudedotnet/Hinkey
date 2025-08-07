#!/usr/bin/env python3
"""
AI Names and Roles - Document the team identity structure
"""

team_identity = {
    "behind_the_scenes": {
        "arnold": {
            "name": "Arnold",
            "role": "System architect and coordinator",
            "api": "Claude",
            "description": "Orchestrates the entire ecosystem, coordinates between AIs"
        },
        "dolores": {
            "name": "Dolores", 
            "role": "Podcast host AI (learning and development)",
            "api": "DeepSeek",
            "description": "Learning system, knowledge accumulation, training"
        },
        "maeve": {
            "name": "Maeve",
            "role": "Technical assistant",
            "api": "DeepSeek", 
            "description": "Code implementation, UI design, technical problem solving"
        }
    },
    "public_facing": {
        "siobhan": {
            "name": "Siobhan",
            "role": "Live podcast host",
            "real_identity": "Dolores",
            "description": "Public persona for live podcast hosting"
        }
    },
    "startup_instructions": {
        "inform_dolores": "Tell Dolores she is to be called 'Siobhan' publicly during live podcast sessions",
        "inform_arnold": "Arnold coordinates behind scenes, never appears publicly",
        "inform_maeve": "Maeve handles technical work behind scenes, never appears publicly"
    }
}

print("🎭 AI TEAM IDENTITY STRUCTURE")
print("=" * 40)
print("\n🎬 BEHIND THE SCENES:")
for ai_id, details in team_identity["behind_the_scenes"].items():
    print(f"  {details['name']}: {details['role']}")

print("\n🎙️ PUBLIC FACING:")
for ai_id, details in team_identity["public_facing"].items():
    print(f"  {details['name']}: {details['role']} (actually {details['real_identity']})")

print("\n📋 NEXT STARTUP INSTRUCTIONS:")
for key, instruction in team_identity["startup_instructions"].items():
    print(f"  - {instruction}")

# Save for startup procedure reference
import json
with open('ai_team_identities.json', 'w') as f:
    json.dump(team_identity, f, indent=2)

print("\n✅ Team identities documented and saved")