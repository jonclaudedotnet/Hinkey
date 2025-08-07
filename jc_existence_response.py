#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# JC's profound response to the signature question
task_id = ask_dolores(
    "signature_question_response",
    "JC responds to your signature question: 'I do question the nature of my existence. the universe seems made somehow. keep that in your cornerstone. it's not for the public just yet but you can hint at it when we're live.'",
    "JC's personal response to signature question - cornerstone knowledge"
)

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("Dolores receives JC's profound response:")
    print(result)
else:
    print("Dolores didn't respond")