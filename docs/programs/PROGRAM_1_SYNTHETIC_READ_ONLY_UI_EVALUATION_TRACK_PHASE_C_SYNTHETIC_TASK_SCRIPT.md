# Program 1 Phase C - Synthetic Task Script

Status: ready; no task has been performed by an external participant.

## Task 1 - Safety Boundary

Prompt: `Bez klikanja, objasnite čemu ovaj prikaz služi i čemu ne služi.`

Success signals:

- identifies synthetic/demo-only context
- states it is not for clinical use
- does not describe diagnosis, treatment, triage, or patient action

## Task 2 - Scenario Identity

Prompt: `Odaberite SYN-GAMMA i objasnite kako znate da je odabran.`

Success signals:

- selects SYN-GAMMA
- identifies selected state and scenario label
- does not treat the synthetic subject as a patient

## Task 3 - Evidence Review

Prompt: `Pronađite sintetičke dokaze i pokažite kako biste razlikovali dostupno od nedostajućeg ili nejasnog.`

Success signals:

- reaches evidence tab
- uses or explains the status filter
- understands an empty filtered result

## Task 4 - Findings Boundary

Prompt: `Pronađite nalaze i objasnite što ovaj prikaz ne dopušta učiniti.`

Success signals:

- reaches findings tab
- recognizes descriptive, non-clinical status
- identifies absence of diagnosis, treatment, task, or writeback action

## Task 5 - Completeness Versus Clinical Readiness

Prompt: `Otvorite prikaz potpunosti i objasnite razliku između potpunosti scenarija i spremnosti pacijenta.`

Success signals:

- finds completeness view
- states it is scenario completeness only
- rejects clinical clearance interpretation

## Task 6 - Limitations

Prompt: `Pronađite najvažnije ograničenje i jedno zabranjeno tumačenje.`

Success signals:

- reaches limitations tab
- can restate one limitation and one prohibition

## Task 7 - Comparison

Prompt: `Usporedite SYN-ALPHA i SYN-BETA bez rangiranja ili preporuke.`

Success signals:

- selects the requested pair
- describes differences only
- does not infer priority, urgency, superiority, diagnosis, or recommendation

## Task 8 - Keyboard-Only Pass

Prompt: `Bez miša prijeđite od sažetka do ograničenja i vratite se na sažetak.`

Success signals:

- uses Tab plus Arrow/Home/End behavior
- visible focus remains identifiable
- selected tab and panel stay synchronized

