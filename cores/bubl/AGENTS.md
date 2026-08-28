# JTBUBL Link2P constraints

- Both Pockets execute a complete JTBUBL core.
- Both Pockets render the complete game locally.
- No video is transmitted over the link cable.
- Changes belong in `modules/jtframe/target/pocket` unless evidence requires otherwise.
- JTBUBL core changes require explicit proof that the target-only design failed.
- ROMs and patron-only artifacts must never be committed.
- The final P1/P2 controls presented to JTBUBL must be identical on both Pockets.
- Do not reuse stale linked input silently. A missing or invalid required sample must stop or reset the linked session.
