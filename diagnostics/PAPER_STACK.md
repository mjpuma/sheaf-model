# Research questions (not a paper queue)

Kilian / Christian (and related) listed **uses** of SHEAF — hindcast,
substitution, policy, tipping, endogenous network. Those are questions
the model might answer. They are **not** five papers that must be
written in order, and they are not a license to skip the market.

**Current work:** Gate 0 wheat on `agrimate_julia/`. Living queue:
[`diagnostics/DEVELOPMENT.md`](DEVELOPMENT.md).
**Do not** treat Gate 1 / Gate 2 as the next coding task.

| Question | What it is | What it is not |
|---|---|---|
| Gate 0 | Can the published 24-step Agrimate market, substitution off and AMIS prescribed, reproduce the authors’ wheat run? | A public-data reconstruction of unpublished inputs (that fails; J4/J8/J9) |
| Gate 1 | Does turning substitution on spill in the right direction without breaking Gate 0? | Fitting σ on 2008 |
| Gate 2 | Can exporters, sharing a type, choose state-contingent cuts on the 24-step clock (Headey 2011)? | An annual Nash. Clock: `diagnostics/GAME_CLOCK.md` |
| Who restricts, and when? | Positive game: types slow, actions `τ_t` | Estimating the game on the same episode used as the result |
| Just enough / club of the willing? | Normative variant of the same layer | A separate model |
| Does the network emerge? | Trade shares from costs and prices instead of FAOSTAT E0 | Required for Gate 0 (E0 is prescribed) |

**Do not re-run Gate 0 or Gate 1 to host the game.** Returning to Gate 0
after *market* consultation is a different decision (`DEVELOPMENT.md`).
