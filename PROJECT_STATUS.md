# PhysicsMind — Project Status

## Decisions
- ₹0 starting budget; free API quota only.
- Windows, 8 GB RAM, no dedicated GPU.
- Streamlit chat-first MVP.
- OpenRouter optional free-model API; no paid fallback.
- SymPy for deterministic calculations.
- SQLite feedback after each assistant response.
- Never train automatically on raw feedback.
- Token efficiency: deterministic code first, LLM only when needed.

## Current implementation
- Friendly chat-style interface with session conversation history.
- Three quick-start questions.
- Narrow deterministic parser for vertical maximum-height questions.
- Optional LLM tutor for general physics questions.
- Per-answer feedback with issue category and optional comment.
- Local SQLite feedback storage.

## Limitations
- General chat needs an OpenRouter key.
- Natural-language solver coverage is currently narrow.
- No image upload, broad RAG, simulations or adaptive learning yet.
- LLM answers are not independently verified.
- Conversation history is session-only; feedback persists locally.

## Next tasks
1. Test chat UI and feedback locally.
2. Add structured LLM question extraction.
3. Add formula applicability rules and independent verification.
4. Expand deterministic solver topics.
5. Add image input and visual learning later.

## Token/cost policy
- Use Python/SymPy for deterministic work.
- Keep LLM prompts compact.
- No paid model fallback.
- Validate feedback before adding examples to evaluation data.
