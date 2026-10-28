<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Known Pitfalls

- 2026-10-29: A healthy standalone API proxy can coexist with an unusable UI.
  Next.js URL normalization can turn next-intl rewrites into redirects back to
  the requested page when the bind host differs from localhost. Keep the
  documented `skipProxyUrlNormalize` setting and exercise the actual built
  server, including authentication and localized login pages. `npm run build`
  runs this regression after assembling the standalone artifact;
  `npm run test:standalone` reruns it against an existing build. A mocked
  middleware test or a health response alone cannot prove page routing works.
  The regression reads `basePath` from the built artifact; qualify a prefixed
  build with `NEXT_PUBLIC_BASE_PATH=/hindsight npm run build`. Keep the explicit
  root matcher: the catch-all does not match a bare base path without a slash.
