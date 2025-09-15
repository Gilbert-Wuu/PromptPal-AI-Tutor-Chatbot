## 1. Why proficiency adaptation matters
- Brief on mixed proficiency among FH employees and risk of mismatch (overwhelm vs boredom).

## 2. Proficiency levels & personas
- Beginner: little/no AI background. Needs plain language, concrete examples.
- Intermediate: some exposure; wants mental models and limited jargon.
- Advanced: comfortable with APIs/model docs; wants depth, knobs, benchmarks.

## 3. Adaptation strategies
- Progressive disclosure (surface → depth)
- Scaffolding & just-in-time hints
- Mode switching (Beginner / Intermediate / Advanced)
- Pre-assessment & on-the-fly adaptation (quiz, behavior signals)
- Multimodal explainers (text, code, diagram, sandbox)
- “Explain this at my level” and “why” buttons

## 4. UX patterns for the POC
- Toggle for level, expandable sections, examples that scale in complexity,
  glossary tooltips, safe defaults, expert shortcuts.

## 5. Content policy & safety considerations
- Avoid hallucination, overconfidence; level-appropriate warnings and citations.

## 6. Metrics & success criteria
- Task completion time, hint usage, level switches, satisfaction by level,
  novice error rate ↓, expert friction ↓.

## 7. Risks & mitigations
- Misclassification of level → quick override UI
- Beginners overwhelmed → guardrails, definitions inline
- Experts constrained → “show advanced controls” & deep links

## 8. Integration notes for architecture
- Proficiency state stored per session/user
- Content components accept `proficiency` prop to alter depth/examples
- Telemetry events for adaptation loops

## 9. Next steps
- Add preflight micro-quiz
- Instrumentation plan
- Draft 3 leveled examples for the same concept (e.g., RAG)

