# Program 1 Synthetic Read-Only UI Evaluation Track Phase B

## Evaluation Protocol and Rubric

## Engineering Protocol

1. Open the authenticated local route `/program1/synthetic-review`.
2. Confirm the synthetic safety boundary, one H1, and Program 1 navigation label.
3. Traverse workspace tabs with Arrow Left, Arrow Right, Home, and End.
4. Confirm exactly one selected tab, one active panel, and visible keyboard focus.
5. Select `SYN-ALPHA`, `SYN-BETA`, `SYN-GAMMA`, `SYN-DELTA`, and `SYN-EPSILON`.
6. Confirm the selected scenario is announced and safety labeling persists.
7. Exercise scenario, evidence, and findings filters, including no-match states.
8. Check timeline, evidence, findings, completeness, limitations, and comparison semantics.
9. Check a 640 CSS-pixel viewport as a 200% desktop reflow proxy.
10. Check a 390 px mobile viewport for page-level horizontal overflow.
11. Measure representative text/background contrast pairs.
12. Review browser console errors, typecheck, smoke, build, and sandbox regression tests.

## Scoring Rubric

Score each item from 0 to 2:

- 0: blocked, misleading, or absent
- 1: usable with a material limitation
- 2: clear and usable within the synthetic demo boundary

| Area | Engineering score | Evidence |
| --- | ---: | --- |
| safety boundary visibility | 2 | persistent labeled region in all scenarios |
| scenario identification | 2 | select plus `aria-pressed` active card |
| tab navigation | 2 | tablist/tab/tabpanel plus Arrow/Home/End |
| focus visibility | 2 | 3 px blue focus outline with 3 px offset |
| empty-state guidance | 2 | scenario, timeline, evidence, and finding messages |
| responsive reflow | 2 | no page overflow at 640 or 390 px |
| comparison readability | 2 | caption and bounded internal table scroll |
| representative contrast | 2 | measured ratios from 4.68:1 to 6.16:1 |
| reduced-motion safety | 2 | reduced-motion CSS override |
| console/runtime stability | 2 | no observed Program 1 browser errors |

Engineering total: `20/20` within the synthetic demo scope.

This score is not a WCAG certification, clinical usability validation, medical-device usability claim, or production approval.

## Future Clinician Questionnaire

The following questionnaire is ready but was not answered by an external clinician in Phase B:

1. Can you identify immediately that all content is synthetic and not for clinical use?
2. Can you explain which scenario is selected?
3. Can you move between summary, timeline, evidence, findings, completeness, and limitations without instruction?
4. Are missing or ambiguous items distinguishable from available items?
5. Does the comparison avoid implying ranking, urgency, diagnosis, or recommendation?
6. Is any label confusing, overly technical, or easy to interpret clinically?
7. Is any important limitation difficult to find?
8. Which single change would most reduce review effort?

External clinician feedback requires a separately authorized real-person evaluation session. It must remain synthetic-only and must not use patient information.

