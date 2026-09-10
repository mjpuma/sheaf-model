# A2e — is the restriction sign test comparing like with like?

`lift` = mean restriction-only price / mean no-AMIS price - 1 over
the crop's episode window, exactly as assert_amis_raises_price
computes it. The no-AMIS leg is pinned at p0 at every step by the
calm conditional; the restriction-only leg is not, during an episode.

| crop | floor | lift as published | lift without the conditional | pinned base | unpinned base |
|---|---|---|---|---|---|
| wheat | +0.05 | +0.675 | +0.962 | 213.5 | 182.2 |
| rice | +0.05 | +0.924 | +0.832 | 339.0 | 356.1 |
| maize | +0.00 | +0.019 | +0.398 | 135.4 | 105.1 |

## Does alpha_r survive without the conditional?

Repository notes state alpha_r = 0.80 was set so that isolated maize
restrictions do not cut the world price. Below, the maize lift as a
function of alpha_r, with and without the conditional. If the sign
condition holds at alpha_r = 0 once the comparison is like-for-like,
then alpha_r was compensating for the artifact, not for an economic
effect, and its justification needs restating.

| alpha_r | maize lift, conditional on | conditional off |
|---|---|---|
| 0.0 | -0.187 | +0.174 |
| 0.2 | -0.151 | +0.215 |
| 0.4 | -0.107 | +0.264 |
| 0.8 | +0.019 | +0.398 |
| 1.2 | +0.225 | +0.599 |

Same for wheat and rice, whose floors are +0.05:

| crop | alpha_r | lift, conditional on | conditional off |
|---|---|---|---|
| wheat | 0.0 | +0.269 | +0.487 |
| wheat | 0.8 | +0.675 | +0.962 |
| rice | 0.0 | +0.218 | +0.156 |
| rice | 0.8 | +0.924 | +0.832 |
