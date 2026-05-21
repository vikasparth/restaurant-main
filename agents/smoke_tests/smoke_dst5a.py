import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents import diagnostic_agent

guardrails = {
    "crash_location": "src/features/menu/hooks/useMenu.ts:1",
    "changed_files": ["src/features/menu/hooks/useMenu.ts"],
    "max_files_to_read": 3,
}

result = diagnostic_agent.run(guardrails, issue_number="DST5A")

print("\n=== RESULT ===")
for k, v in result.items():
    print(f"  {k}: {v}")
