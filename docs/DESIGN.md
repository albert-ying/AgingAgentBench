# Website design

The page follows the BioLean site in `/Users/A.Y/programs/formalbio-merged/release/formalbio-site`.
Its `dist/assets/site.css` and `DESIGN.md` supply the layout and type system.
The page stays white in every system appearance.

## Tokens

- `--ground: #ffffff`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --ground`.
- `--panel: #f4f3f4`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --panel`.
- `--ink: #181114`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --ink`.
- `--ink-2: #544b52`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --ink-2`.
- `--ink-3: #6e676c`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --ink-3`.
- `--rule: #dcd9da`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --rule`.
- `--sans: Oxygen, "Helvetica Neue", Arial, sans-serif`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --sans`.
- `--mono: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, `:root --mono`.
- `--bar-clockbase: #33414E`. Source `Figure 4`, `ClockBase bar, per task`.
- `--bar-other: #B4B4B4`. Source `Figure 4`, `other systems, per task`.
- `--bar-chance: #8C8C8C`. Source `Figure 4`, `dashed chance line, per task`.

## Reference rules

These rules are copied from the reference. Each declaration records its
selector and value, including layout, type, links, focus, and controls.

- `:root`: `color-scheme: light;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `*, *::before, *::after`: `box-sizing: border-box;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `[hidden]`: `display: none !important;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `html`: `-webkit-text-size-adjust: 100%;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `body`: `margin: 0; background: var(--ground); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 26px; font-synthesis: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.wrap`: `max-width: 72rem; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 24px 48px; display: flex; flex-direction: column; gap: 48px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `main`: `display: flex; flex-direction: column; gap: 48px; min-width: 0;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `main > section, main > div, main > figure`: `min-width: 0;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `section`: `display: flex; flex-direction: column; gap: 16px; min-width: 0;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `h1, h2, h3`: `margin: 0; font-weight: 700; text-wrap: balance;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `h1`: `font-size: 36px; line-height: 44px; max-width: 30ch;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `h2`: `font-size: 24px; line-height: 30px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `h3`: `font-size: 18px; line-height: 26px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `p, ul, ol, dl, figure, pre`: `margin: 0;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `p, li, dd`: `max-width: 68ch;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `a`: `color: var(--ink); text-decoration: underline; text-underline-offset: 3px; text-decoration-thickness: 1px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `a:hover`: `text-decoration-thickness: 2px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `code, pre, kbd`: `font-family: var(--mono); font-size: 14px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `code, pre, kbd, textarea, .rel-chip, .sgraph text, .wgraph .mono`: `font-variant-ligatures: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `var, em, i, cite`: `font-style: normal;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.standfirst`: `font-size: 18px; line-height: 28px; max-width: 60ch;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.caption, figcaption`: `font-size: 12px; line-height: 18px; color: var(--ink-3);`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.num, .count, td.num`: `font-variant-numeric: tabular-nums;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.sha`: `white-space: nowrap;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.desig`: `font-size: 12px; color: var(--ink-3);`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `:focus-visible`: `outline: 2px solid var(--ink); outline-offset: 2px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.skip-link`: `position: absolute; left: 16px; top: -64px; padding: 8px 12px; background: var(--ground); color: var(--ink); border: 2px solid var(--ink); border-radius: 4px; z-index: 10;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.skip-link:focus`: `top: 8px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `main:focus`: `outline: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-head`: `display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 32px; padding-bottom: 16px; border-bottom: 1px solid var(--rule);`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.wordmark`: `font-weight: 700; font-size: 18px; text-decoration: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-nav ul`: `list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 24px; font-size: 14px; line-height: 20px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-nav a`: `text-decoration: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-nav a:hover`: `text-decoration: underline;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-nav a[aria-current="page"]`: `font-weight: 700; text-decoration: underline; text-decoration-thickness: 2px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-foot`: `border-top: 1px solid var(--rule); padding-top: 16px; font-size: 12px; line-height: 18px; color: var(--ink-2); display: flex; flex-direction: column; gap: 4px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.site-foot p`: `max-width: none;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.caption code, figcaption code, .site-foot code`: `font-size: 12px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.page-head`: `display: flex; flex-direction: column; gap: 12px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `button, .button`: `font: inherit; font-size: 14px; line-height: 20px; border-radius: 4px; padding: 6px 14px; cursor: pointer; border: 1px solid var(--ink); background: var(--ground); color: var(--ink);`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.table-scroll`: `overflow-x: auto; max-width: 100%;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `table`: `border-collapse: collapse; font-size: 14px; line-height: 20px; width: 100%;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `caption`: `text-align: left; font-size: 12px; line-height: 18px; color: var(--ink-3); padding-bottom: 8px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `th`: `text-align: left; font-weight: 700; vertical-align: bottom;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `th, td`: `padding: 8px 12px 8px 0; border-bottom: 1px solid var(--rule); vertical-align: top;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `td code, th code`: `font-size: 12px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.cmd-table td:first-child`: `min-width: 12rem;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `.cmd-table code .arg`: `white-space: nowrap;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `pre`: `background: var(--panel); border-radius: 4px; padding: 12px 16px; overflow-x: auto; max-width: 100%; font-size: 12px; line-height: 20px;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.
- `pre code`: `font-size: inherit;`. Source `/Users/A.Y/programs/formalbio-merged/release/formalbio-site/dist/assets/site.css`, same selector.

## Fonts

The @font-face rules are copied from `dist/assets/site.css`, with relative
URLs adjusted for this stylesheet. Oxygen regular and bold and JetBrains
Mono load from `assets/fonts/`. The WOFF files and OFL.txt are copied from
the reference `dist/assets/fonts/`. Font weights, ranges, and file names
are preserved in `style.css`.

## Layout

These widths are derived from the reference declarations using its body
font size for the default rem. Rendered review is performed separately.

At a viewport of 1440px, `.wrap` is 1152px wide with 16px side padding. The content is 1120px wide and begins 160px from the viewport edge. At a viewport of 390px, `.wrap` is 390px wide with 16px side padding. The content is 358px wide and begins 16px from the viewport edge.

The reference `.wrap` supplies the content width, safe-area side padding,
block padding, and gap between header and main. `main` supplies the gap
between sections. `section` supplies the gap within each section.
The `.site-head` rule sits below the wordmark and wrapping navigation.
The header does not stick. The `.page-head` gap separates the title and
standfirst. No enclosing section boxes are added.

The leaderboard retains its data columns, scale, interval geometry, row
order, and phone stacking from the existing builder. Its type and rules
use the reference table system. Bar colours follow the paper figure key,
and whiskers use ink. Plot dimensions remain those of the existing builder.
The responsive breakpoints follow the reference stylesheet at
`@media (max-width: 1023px)` and `@media (max-width: 639px)`.
The task image width and logo dimensions follow the task instruction.
The inline wordmark alignment and spacing follow reference `.control-row`.
The logo and favicon appear when the logo file exists at build time.
Rebuild after adding it.

## Source text

The question title and standfirst are requested content. The measurement
sentence and inventory come from README.md. The confidence-interval
parenthetical is a measurement annotation. Command paths come from
README.md and licence filenames come from DATA_LICENSE.md. Those strings
identify executable inputs and reuse terms. Numeric comparisons remain
in the builder.
