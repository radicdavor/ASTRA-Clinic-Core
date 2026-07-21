# Production Safety Foundation — frontend build warning analysis

## Scope

This note records the Phase H review of frontend build warnings observed while validating the production-safety track.

## Tailwind warning

Observed warning:

```text
The `content` option in your Tailwind CSS configuration is missing or empty.
```

Repository findings:

- `frontend/src/styles.css` does not use `@tailwind` directives.
- The frontend package does not directly depend on `tailwindcss`.
- No `tailwind.config.*` or PostCSS config exists in `frontend/` or the repository root.
- The warning appears during local Vite/Playwright output, but no repository-owned Tailwind configuration can be corrected in this track.

Mitigation implemented:

- Do not add a dummy Tailwind configuration.
- Do not introduce Tailwind as a new styling dependency.
- Keep the current handwritten CSS system.
- Add an explicit empty `frontend/postcss.config.cjs` so Vite/PostCSS does not pick up ambient or transitive Tailwind configuration.
- The production build no longer emits the Tailwind warning.

## Bundle warning

Observed warning:

```text
Some chunks are larger than 500 kB after minification.
```

Repository finding:

- The production build previously emitted one large application chunk around 642 kB.

Mitigation implemented:

- `frontend/vite.config.ts` now defines explicit Rollup manual chunks for:
  - React/router runtime
  - icon library
  - Program 1 synthetic surfaces
  - patient-journey workspace surfaces
  - operations pages

Reasoning:

- This is a low-risk split of stable vendor code.
- It avoids hiding the warning by merely increasing `chunkSizeWarningLimit`.
- It does not change runtime API behavior or clinical workflow behavior.
- The production build no longer emits the chunk-size warning.

Deferred:

- Route-level lazy loading remains a future performance task.
- Bundle analyzer integration is not added in this safety increment.
