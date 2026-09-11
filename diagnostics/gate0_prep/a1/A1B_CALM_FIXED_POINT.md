# A1b — why the calm branch has work to do

The matched configuration (no harvest anomaly, no AMIS, no demand
shifter) is the one in which the note claims p* = p0 follows by
algebra. Below, what the pieces of eq (16) actually do in that run.

## The trade-weighted offer price in a matched run

p* = omega*p_tr + (1-omega)*p_scar. In a matched run p_scar = p0
exactly, so p* = p0 requires p_tr = p0.

### wheat  (omega = 0.70, theta = 0.70, p0 = 213.5 $/t)
- p_tr / p0: mean 0.813, range 0.722-0.964
- so omega*p_tr + (1-omega)*p0 would sit at 0.869 x p0 on average, up to 0.975 x p0
- realised fill in the matched run: mean 0.536, per-step min 0.001, max 0.998
- **target fill theta = 0.70 versus realised mean 0.536** -> asks are pushed DOWN every step even with no shock

### maize  (omega = 0.80, theta = 0.70, p0 = 135.4 $/t)
- p_tr / p0: mean 0.713, range 0.694-0.933
- so omega*p_tr + (1-omega)*p0 would sit at 0.771 x p0 on average, up to 0.946 x p0
- realised fill in the matched run: mean 0.315, per-step min 0.000, max 0.998
- **target fill theta = 0.70 versus realised mean 0.315** -> asks are pushed DOWN every step even with no shock

### rice  (omega = 0.72, theta = 0.70, p0 = 339.0 $/t)
- p_tr / p0: mean 0.958, range 0.726-1.099
- so omega*p_tr + (1-omega)*p0 would sit at 0.970 x p0 on average, up to 1.071 x p0
- realised fill in the matched run: mean 0.623, per-step min 0.001, max 1.000
- **target fill theta = 0.70 versus realised mean 0.623** -> asks are pushed DOWN every step even with no shock

## Does re-targeting theta remove the need for the branch?

Set ask_target_fill to the realised matched-run mean fill, disable the
calm branch, and re-measure the drift that assert_twin_identity
tolerates at 2%. This is calibration to the model's own calm state,
not to a crisis window.

### wheat
- theta 0.70 -> 0.536
- drift, branch off, theta as shipped:   24.806%  FAIL
- drift, branch off, theta re-targeted:  19.692%  FAIL
- drift, branch on,  theta re-targeted:   1.098%  (sanity: the branch pins this regardless)

### maize
- theta 0.70 -> 0.315
- drift, branch off, theta as shipped:   32.961%  FAIL
- drift, branch off, theta re-targeted:  19.832%  FAIL
- drift, branch on,  theta re-targeted:   1.911%  (sanity: the branch pins this regardless)

### rice
- theta 0.70 -> 0.623
- drift, branch off, theta as shipped:   20.243%  FAIL
- drift, branch off, theta re-targeted:  17.724%  FAIL
- drift, branch on,  theta re-targeted:   0.942%  (sanity: the branch pins this regardless)

## What re-targeting theta does to the official scores

Reported for completeness. A change that improves a crisis score is
not thereby justified; per CLAUDE.md the 2007/08 window is not a
fitting target. These numbers exist so the cost of the fix is visible.

### wheat
- as shipped         corr +0.720   2007/08 x2.27   2010/11 x1.45
- theta re-targeted  corr +0.724   2007/08 x2.37   2010/11 x1.33
- observed            2007/08 x1.82   2010/11 x1.16

### maize
- as shipped         corr +0.712   2007/08 x1.97   2010/11 x1.70
- theta re-targeted  corr +0.650   2007/08 x2.27   2010/11 x0.95
- observed            2007/08 x1.84   2010/11 x1.44

### rice
- as shipped         corr +0.678   2007/08 x1.72   2010/11 x0.82
- theta re-targeted  corr +0.673   2007/08 x1.70   2010/11 x0.82
- observed            2007/08 x1.84   2010/11 x0.79

