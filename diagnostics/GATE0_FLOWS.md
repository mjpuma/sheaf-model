# Gate 0 flow diagrams

**Companion to** [`GATE0_DISCUSSION.md`](GATE0_DISCUSSION.md).
**Host:** `sheaf/dynamic_crop.py` (`_simulate_window`).
**Status:** pictures of the *current* map and of *options*. Not a rewrite list.

**Figures in the repo:** [`figures/gate0_flows/`](../figures/gate0_flows/).
**Organized writeup:** [`overleaf/gate0_discussion/`](../overleaf/gate0_discussion/)
(four figures, symbols with units, map \(F\) and how it is solved).
The 19 SVGs remain in this folder as a spare atlas; the Overleaf note
does not include them all.

Accent boxes in the option diagrams are what would **change**. Everything
else stays the current fortnight unless the diagram is a different object
(Agrimate NLPs, yearly QP).

---

## 1. Current Gate 0 — one fortnight

Incoming state: last world \(p\), last asks \(q\), stocks \(S\), harvest \(H\).
Outgoing: new \(p\), new \(q\), new \(S\). No inner solve.

```mermaid
flowchart TB
  state_in["p, q, S, H in"]
  twin["twin free, unmet"]
  demand["d from last p<br/>isoelastic flex + industrial"]
  hexp["H^exp = φ H + (1-φ) Hseas"]
  target["T = L + s<br/>world lean clock"]
  offers["O = surplus above d+T, times 1-τ"]
  importd["D = food gap + λ rebuild"]
  trade["Armington min(O Ã, D S)<br/>+ residual pool"]
  stocks["S' then soft-clip toward W"]
  asks["q ← fill, blockage, pull to p"]
  pscar["p^scar ∝ r^η × tightness"]
  pstar["p* = ω p^tr + (1-ω) p^scar"]
  pout["p out, AR smoother"]
  next["next fortnight"]

  state_in --> demand
  state_in --> hexp
  hexp --> target
  demand --> offers
  demand --> importd
  target --> offers
  target --> importd
  offers --> trade
  importd --> trade
  trade --> stocks
  trade --> asks
  stocks --> asks
  twin --> pscar
  stocks --> pscar
  asks --> pstar
  pscar --> pstar
  pstar --> pout
  pout --> next
  asks --> next
  stocks --> next
```

Demand uses **last** step’s \(p\). Twin is a **separate** run of the same
map (climatology harvest, mean flex, no industrial, \(\tau\equiv 0\)).
Calm: twin-match \(\Rightarrow p^\star=p_0\).

---

## 2. Baselines — what feeds that map

Four objects. Scarcity uses the **twin**. \(p_0\) is the numeraire.

```mermaid
flowchart TB
  psd["2005 PSD stocks"]
  hseas["Hseas = window-mean PSD × calendar"]
  p0["p0 = start-year Pink Sheet mean"]
  spin["2-year spin-up<br/>Hseas, mean flex, τ = 0"]
  s0["opening S"]
  twin["twin run of the same map"]
  ftwin["free_twin, unmet_twin"]
  lowess["treatment H = Hseas × (1+LOWESS)"]
  treat["treatment fortnight map"]
  pt["p path"]

  psd --> spin
  hseas --> spin
  spin --> s0
  s0 --> twin
  hseas --> twin
  p0 --> twin
  twin --> ftwin
  hseas --> lowess
  s0 --> treat
  lowess --> treat
  p0 --> treat
  ftwin --> treat
  treat --> pt
```

Twin holds \(p=p_0\) so `free_twin` is physical, not a second price path.

### Option B2 — 4-year spin-up

Same diagram; only the spin-up box lengthens (Agrimate ~4 years). Named
sensitivity. Do not retune \(\eta\) to compensate.

### Option B3 — Nash / SPE rest as “baseline”

```mermaid
flowchart TB
  data["FAOSTAT / PSD year"]
  nash["annual Nash or SPE rest"]
  rest["resting p, S"]
  treat["24-step treatment"]
  pt["p path"]

  data --> nash --> rest --> treat --> pt
```

That rest is a **different object** from the current twin (same map, no
shock). It is the parked yearly host, or Agrimate’s periodic Nash — not a
rename of `free_twin`.

---

## 3. Price maps

### P0 — keep the sequential map (current)

Same as §1. \(p\) is not a DE. The ask law is the only piece that looks like
\(\mathrm{d}q/\mathrm{d}t\).

### P2 — same-step consistency

Demand uses **this** step’s \(p\). Dashed edge is a new inner loop
(root-find or one Jacobi step).

```mermaid
flowchart TB
  state_in["q, S, H in"]
  demand["d from this p"]
  target["T = L + s"]
  offers["O"]
  importd["D"]
  trade["Armington"]
  stocks["S', W"]
  asks["ask update"]
  pscar["p^scar"]
  pstar["p*"]
  pout["p out"]

  state_in --> demand
  demand --> offers
  demand --> importd
  target --> offers
  target --> importd
  offers --> trade
  importd --> trade
  trade --> stocks
  trade --> asks
  stocks --> pscar
  asks --> pstar
  pscar --> pstar
  pstar --> pout
  pstar -.-> demand
```

### P3 — ask markup FOC; world \(p\) still inverse-demand flavored

Same as §1 except the ask box becomes an exporter FOC (may collapse
\(\alpha,\theta,\beta\)). World \(p\) still blended.

### P4 — Agrimate-style per-region NLPs (different object)

```mermaid
flowchart TB
  H["harvest in"]
  tau["policy τ known"]
  sup["supplier NLP<br/>store vs sell, export price"]
  con["consumer NLP<br/>CES under budget"]
  pur["purchaser NLP<br/>CES across suppliers"]
  S["S'"]
  pexp["export price"]
  pdom["domestic price"]
  pworld["paper world p<br/>accounting aggregate"]

  H --> tau --> sup
  sup --> con --> pur --> S
  sup --> pexp
  con --> pdom
  pexp --> pworld
  pdom --> pworld
```

No world \(p\) as a primitive. Do not clone this as Gate 0.

### P5 — yearly SPE as heartbeat (parked host)

```mermaid
flowchart TB
  Ep["E[p] last year"]
  stor["storage rule"]
  qp["spatial QP<br/>p is a multiplier"]
  p["p_year, shipments"]
  next["next year"]

  Ep --> stor --> qp --> p --> next
```

Already failed as the 2007/08 heartbeat. Parked in `sheaf.annual`.

### P6 — continuous DE

Not drawn. Integrating the same reduced-form gains in continuous time
does not add an object.

---

## 4. Optimization principle — what *produces* \(p\)

Three different requests. The boxes that emit \(p\) change; the rest of
the fortnight may not.

```mermaid
flowchart LR
  subgraph o0["O0 current"]
    map["sequential map"] --> p0["p"]
  end
  subgraph o1["O1 characterize"]
    pot["if map = FOC of a potential"] --> p1["p"]
  end
  subgraph o_spe["O5 SPE"]
    qp["QP / market clear"] --> p2["p"]
  end
  subgraph o_ag["O4 agents"]
    nlp["three NLPs"] --> p3["p_dom, p_exp"]
  end
```

O0/O1 are documentation + math, zero solver. O2 (same-step) and O3 (ask
FOC) reuse §3. O4/O5 are different models.

---

## 5. Storage — how grain is split

### S0 — current cover rule (no agent)

```mermaid
flowchart TB
  avail["avail = S + H"]
  eat["eat d"]
  hold["hold T = L + s"]
  offer["offer leftover × (1-τ)"]
  trade["Armington"]
  sp["S'"]
  w["soft drain of max(0, S'-W)"]

  avail --> eat
  avail --> hold
  avail --> offer
  offer --> trade
  eat --> sp
  trade --> sp
  sp --> w
```

They do not dump this step because \(T\) withholds cover, not because of
an Euler. No carrying cost \(r\).

### S2 — one-line store vs sell

```mermaid
flowchart TB
  avail["avail = S + H"]
  foc["store vs sell FOC<br/>E[p] vs (1+r) p"]
  offer["offer"]
  hold["hold"]
  trade["Armington"]
  sp["S'"]

  avail --> foc
  foc --> offer
  foc --> hold
  offer --> trade
  hold --> sp
  trade --> sp
```

### S4 — Agrimate commercial supplier

```mermaid
flowchart TB
  H["harvest"]
  tau["policy known"]
  nlp["supplier NLP<br/>finite-horizon profit"]
  sell["sell domestic + export"]
  store["store"]

  H --> tau --> nlp
  nlp --> sell
  nlp --> store
```

Strategic storage in Agrimate is a **different** agent (partial-adjustment
refill). SHEAF Gate 2 `gov_stu` is not that agent.

Country-specific STU (S3) is not redrawn: tried, rejected (China maize ~×3).
Deaton–Laroque RE (S5) is off the table as a Gate 0 test.

---

## 6. Commercial representation

### Current — rules, not agents

The §1 and §5-S0 diagrams *are* the commercial layer: a partition plus
Armington. Destination mix is \(\tilde A \propto A(p_0/q)^\gamma\), not a
purchaser CES.

### Agrimate — three programs

Same as §3-P4. Purchaser, not the supplier, allocates across markets.

### T1 — domestic vs export price

```mermaid
flowchart TB
  tau["τ > 0"]
  p["one world p"]
  pdom["p_domestic"]
  pexp["p_export / ask"]
  d["demand on p_dom"]
  o["offers at p_exp"]

  tau --> pdom
  tau --> pexp
  p -. current, no split .-> tau
  pdom --> d
  pexp --> o
```

A ban still does not create a cheaper domestic CPI under the current map.
T1 is a later-layer (Gate 2 welfare) option, not a Pink Sheet requirement.

---

## 7. Foresight

```mermaid
flowchart TB
  subgraph e0["E0 current"]
    h0["H^exp = φ-blend this step"]
    p0["demand uses last p"]
    l0["world lean clock"]
  end
  subgraph e1["E1 = P2"]
    h1["φ-blend harvest"]
    p1["demand uses this p"]
    l1["world lean clock"]
  end
  subgraph e2["E2 country lean"]
    h2["φ-blend harvest"]
    p2["demand uses last p"]
    l2["lean clock on i's calendar"]
  end
  subgraph e4["E4 off the table"]
    h4["10-year / RE path"]
  end
```

E0 already matches “not 10-year foresight.” E2 is the live modeling
choice (world hungry season vs national crop calendar). E3 waits until
Agrimate’s expectation module is named in their code.

---

## 8. How a diagram becomes a decision

1. Names first (baseline objects, offer vs ask vs \(p\)).
2. If the option diagram is the **same boxes** with an honest label, that
   is keep + writeup (P0, S0, O0).
3. If a **dashed inner edge** or **FOC box** appears, that is a named
   sensitivity (P2, P3, S2) — characterize the current law first.
4. If the diagram is a **different object** (P4, P5, S4), it is not Gate 0
   unless we explicitly replace the host.

Discussion order stays: names → honesty → storage principle → price
principle → knob isolations. See [`GATE0_DISCUSSION.md`](GATE0_DISCUSSION.md) §13.
