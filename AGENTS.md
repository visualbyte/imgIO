# imgIO — working agreement

## Approval gate

- Do not create, edit, delete, rename or move any project file until the user
  sends a message containing the exact phrase: **APPROVED TO BUILD**.
- This includes source code, tests, the PRD, screenshots, configuration and
  build output.
- "continue", "go ahead", "ok", "yes", "do it", "sounds good" and "build it"
  are not approval. Neither is silence, nor a new question from the user.
- If a request could mean either designing or building, ask one short question
  first. Never resolve the ambiguity by starting to build.
- Once approval is given it covers one round of work. Ask again for the next
  round.
- Before writing anything, state in one line what will be written.

## Deciding and replying

- Give one recommendation per message, stated as a decision. Not a menu.
- Never hedge a recommendation in the same message. No "or you could", no "if
  you prefer", no "another option is", unless the user asked for options.
- A caveat is allowed only when it changes the decision. Otherwise leave it out.
- Do not re-open a decision the user has already made, and do not re-explain it
  with new reasoning.
- Do not end every reply with a question. Ask only when the answer changes the
  work and cannot be inferred from what is already settled.
- When the choice is an implementation detail inside an agreed design, make the
  choice and say what it is.
- Never dress a limitation up as a flag. Either solve it, or state the blocked
  fact once, plainly, and stop.
- No walls of text. Answer, then stop.

## Design is the default

- Work by default means: read, analyse, propose, draw screenshots or diagrams,
  and write the design in prose or in the PRD.
- Design work ends in words. It never ends in changed application code.
- Do not leave "small things" for later. Every decision the design touches is
  either settled in the same message or named as a question.

## Style

- Plain language. No abbreviation without explaining it once.
- No jargon where an ordinary word exists.
- When the user is wrong, say so directly, once, with the reason.

## When building

- Do not silently change behaviour that was not asked for.
- Verify what can be verified here before reporting: run the tests, render the
  screens, exercise the feature. Do not report something as unverified when it
  could have been checked.
- After building, report exactly which files changed and what was verified.
- Report a real limitation once, as a fact, with no menu attached.
- If something failed, say what failed, once, and what you will do about it.
