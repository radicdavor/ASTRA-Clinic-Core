# Codex Architecture Bible Instructions

`docs/ASTRA_ARCHITECTURE_BIBLE.md` is the highest architectural reference for ASTRA Clinic Core.

Before every implementation, Codex must read it and check the requested change against these questions:

1. Is the change aligned with ASTRA's philosophy?
2. Does it increase simplicity, or only increase the number of functions?
3. Can it be implemented inside the existing Clinic Core model?
4. Does it preserve the unified language of the system?
5. Does it respect security, audit and AI rules?

If the answer is negative or unclear, Codex must explain the architectural conflict before implementing.

Do not change the Architecture Bible directly unless the maintainer explicitly requests that exact edit.

If the Bible should be clarified, create or update `docs/ARCHITECTURE_CHANGE_PROPOSAL.md` with the proposed change and rationale.

