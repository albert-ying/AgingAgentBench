# Website design

The working surface follows the ClockBase benchmark named in the task.
The leaderboard opens the page. Section order carries the explanation.

## Tokens

- `--cb-bg: #eef3f5`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-bg`.
- `--cb-surface: #ffffff`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-surface`.
- `--cb-text: #10232c`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-text`.
- `--cb-muted: #4f6470`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-muted`.
- `--cb-line: rgba(16, 45, 60, 0.22)`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-line`.
- `--cb-accent: #0d4f93`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-accent`.
- `--cb-sans: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-sans`.
- `--cb-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `:root --cb-mono`.
- `--page-width: 1320px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-page max-width`.
- `--page-pad: 24px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-page horizontal padding`.
- `--page-pad-wide: 40px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-page desktop horizontal padding`.
- `--title-size: 30px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-title font-size`.
- `--title-size-wide: 34px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-title desktop font-size`.
- `--heading-size: 28px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-h2 font-size`.
- `--heading-size-wide: 32px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-h2 desktop font-size`.
- `--heading-weight: 600`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-title and .cb-h2 font-weight`.
- `--heading-leading: 1.15`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-title and .cb-h2 line-height`.
- `--heading-tracking: -0.015em`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-title and .cb-h2 letter-spacing`.
- `--lede-size: 16px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-lede font-size`.
- `--lede-leading: 1.6`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-lede line-height`.
- `--lede-width: 72ch`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `.cb-lede max-width`.
- `--row-size: 13px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard row text-[13px]`.
- `--body-size: 14px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Agent reruns table text-[14px]`.
- `--axis-size: 11px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard axis text-[11px]`.
- `--label-weight: 500`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Agent reruns th font-medium`.
- `--label-size: 12px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard header text-[12px]`.
- `--bar-height: 16px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard h-4`.
- `--bar-muted: color-mix(in srgb, var(--cb-muted) 42%, transparent)`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard non-ClockBase bar background`.
- `--whisker-width: 1.5px`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard interval stroke`.
- Dark `--cb-bg: #061820`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.
- Dark `--cb-surface: #0a222c`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.
- Dark `--cb-text: #e4edf1`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.
- Dark `--cb-muted: #8fa6b2`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.
- Dark `--cb-line: rgba(150, 200, 220, 0.22)`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.
- Dark `--cb-accent: #9fc9f0`. Source `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/styles.css`, `html[data-theme="dark"]`.

## Typography

The single Google Fonts stylesheet is copied from `website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/index.html`:

`https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap`

The stylesheet supplies IBM Plex Sans and IBM Plex Mono with system fallbacks.

## Layout

`website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend/src/components/Benchmark.jsx`, `Leaderboard`, supplies the ranked bars, ClockBase-first ordering, class columns, chance line, and interval whiskers. The system column widens to fit the additional source variants. Phones stack the system and value above a full-width bar, followed by class matches. Row rules separate observations as in the reference. The neutral ground and one accent follow the source theme tokens. Dark mode follows the system preference without JavaScript. The source dark background gradients are omitted because this page is a static working surface.

## Style checks

The title sentence and image dimensions are explicit task requirements. The title sentence is the README measurement sentence, not a marketing tagline. The task image is hidden when absent at build time. Rebuild after adding it. No script, decorative card, shadow, icon, or motion is used. Data tables and the command block have boundaries defined by their contents.

The style checker reports a trailing parenthetical on the agreement column. This is a confidence-interval abbreviation with its confidence level, copied from the reference table; it is a unit of the measurement, not a subtitle. It also flags the prediction filename in the command and the expert filenames in the license. The command is copied from README.md and must be executable. DATA_LICENSE.md assigns distinct terms to the named expert files, so those exact paths are necessary for reuse. These findings are retained with their source evidence.
