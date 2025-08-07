#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Give Dolores information about Jon Claude Haines
info = """From internet search about Jon Claude Haines:

PERSONAL BACKGROUND:
- Lives in Chester, Connecticut
- Wife: Caitlin
- Moved to Chester about 6 years ago (as of 2020)
- Grew up in Westhampton, Long Island
- Fascinated by computers since early teens
- Played tenor saxophone in high school
- Served 4 years in the Navy after high school

PROFESSIONAL:
- Computer expert and tech specialist
- Runs Sea Robin Tech (previously Woodland Technologies)
- Started working for companies setting up websites in the 1990s
- Initially focused on creating business websites in the medical field
- Now helps local nonprofits with technology

COMMUNITY INVOLVEMENT:
- Sets up Zoom sessions for addiction services in Madison
- Helps with French classes at Ivoryton Library
- Supports New Horizons Band with electronic reunions

LEARN: [personal] Jon Claude Haines lives in Chester, Connecticut with wife Caitlin
LEARN: [professional] Jon runs Sea Robin Tech, specializing in web and tech support
LEARN: [background] Jon served in the Navy and played tenor saxophone
LEARN: [interests] Jon has been fascinated by computers since his early teens
LEARN: [community] Jon actively helps local nonprofits with technology needs"""

task_id = ask_dolores(
    "learn_about_user",
    info,
    "Initial information about Jon Claude Haines from web search"
)

print(f"Teaching Dolores about Jon (task #{task_id})...")
result = wait_for_dolores(task_id, timeout=30)

if result:
    print("\nDolores learned:")
    print(result)