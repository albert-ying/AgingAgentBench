#!/usr/bin/env python3
"""Build the AgingAgentBench GitHub Pages site from released reference files.

Run from any directory. Uses only the Python standard library. Numeric text is
registered with its source and checked after reading the generated HTML back.
Existing outputs are preserved at the task's dated backup path before changes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs'
REF = ROOT / 'reference_results'
REPOSITORY = 'https://github.com/albert-ying/AgingAgentBench'
PUBLIC = 'https://albert-ying.github.io/AgingAgentBench/'
BACKUP = '.bak-2026-11-13r'
REFERENCE = 'website_local_2026-11-07/clockbase-site-deploy-2026-10-18/frontend'
# Values measured from the named ClockBase reference, not a new design system.
TOKENS = {
    'cb-bg': ('#eef3f5', 'src/styles.css', ':root --cb-bg'),
    'cb-surface': ('#ffffff', 'src/styles.css', ':root --cb-surface'),
    'cb-text': ('#10232c', 'src/styles.css', ':root --cb-text'),
    'cb-muted': ('#4f6470', 'src/styles.css', ':root --cb-muted'),
    'cb-line': ('rgba(16, 45, 60, 0.22)', 'src/styles.css', ':root --cb-line'),
    'cb-accent': ('#0d4f93', 'src/styles.css', ':root --cb-accent'),
    'cb-sans': ('"IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif', 'src/styles.css', ':root --cb-sans'),
    'cb-mono': ('"IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace', 'src/styles.css', ':root --cb-mono'),
    'page-width': ('1320px', 'src/styles.css', '.cb-page max-width'),
    'page-pad': ('24px', 'src/styles.css', '.cb-page horizontal padding'),
    'page-pad-wide': ('40px', 'src/styles.css', '.cb-page desktop horizontal padding'),
    'title-size': ('30px', 'src/styles.css', '.cb-title font-size'),
    'title-size-wide': ('34px', 'src/styles.css', '.cb-title desktop font-size'),
    'heading-size': ('28px', 'src/styles.css', '.cb-h2 font-size'),
    'heading-size-wide': ('32px', 'src/styles.css', '.cb-h2 desktop font-size'),
    'heading-weight': ('600', 'src/styles.css', '.cb-title and .cb-h2 font-weight'),
    'heading-leading': ('1.15', 'src/styles.css', '.cb-title and .cb-h2 line-height'),
    'heading-tracking': ('-0.015em', 'src/styles.css', '.cb-title and .cb-h2 letter-spacing'),
    'lede-size': ('16px', 'src/styles.css', '.cb-lede font-size'),
    'lede-leading': ('1.6', 'src/styles.css', '.cb-lede line-height'),
    'lede-width': ('72ch', 'src/styles.css', '.cb-lede max-width'),
    'row-size': ('13px', 'src/components/Benchmark.jsx', 'Leaderboard row text-[13px]'),
    'body-size': ('14px', 'src/components/Benchmark.jsx', 'Agent reruns table text-[14px]'),
    'axis-size': ('11px', 'src/components/Benchmark.jsx', 'Leaderboard axis text-[11px]'),
    'label-weight': ('500', 'src/components/Benchmark.jsx', 'Agent reruns th font-medium'),
    'label-size': ('12px', 'src/components/Benchmark.jsx', 'Leaderboard header text-[12px]'),
    'bar-height': ('16px', 'src/components/Benchmark.jsx', 'Leaderboard h-4'),
    'bar-muted': ('color-mix(in srgb, var(--cb-muted) 42%, transparent)', 'src/components/Benchmark.jsx', 'Leaderboard non-ClockBase bar background'),
    'whisker-width': ('1.5px', 'src/components/Benchmark.jsx', 'Leaderboard interval stroke'),
}
FONT_URL = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap'
DARK = {'cb-bg': '#061820', 'cb-surface': '#0a222c', 'cb-text': '#e4edf1', 'cb-muted': '#8fa6b2', 'cb-line': 'rgba(150, 200, 220, 0.22)', 'cb-accent': '#9fc9f0'}

CSS = '''
* { box-sizing: border-box; }
html { background: var(--cb-bg); color: var(--cb-text); color-scheme: light; }
body { margin: 0; font-family: var(--cb-sans); -webkit-font-smoothing: antialiased; line-height: var(--lede-leading); font-size: var(--lede-size); }
a { color: var(--cb-accent); text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
a:focus-visible, summary:focus-visible { outline: 2px solid var(--cb-accent); outline-offset: 4px; }
main { max-width: var(--page-width); margin: 0 auto; padding: 40px var(--page-pad) 64px; min-width: 0; }
h1, h2 { font-weight: var(--heading-weight); line-height: var(--heading-leading); letter-spacing: var(--heading-tracking); }
h1 { font-size: var(--title-size); margin: 0 0 10px; }
h2 { font-size: var(--heading-size); margin: 0 0 20px; }
h3 { font-size: var(--lede-size); margin: 24px 0 10px; font-weight: var(--heading-weight); }
p { margin: 0 0 16px; }
header > p { font-size: var(--lede-size); line-height: var(--lede-leading); max-width: var(--lede-width); color: var(--cb-muted); margin-bottom: 28px; }
section { margin-top: 40px; }
.leaderboard { margin: 0; }
.board-grid { display: grid; grid-template-columns: 200px minmax(0, 1fr) 140px 78px 78px 116px; column-gap: 16px; align-items: center; }
.board-head { color: var(--cb-muted); font-size: var(--label-size); align-items: end; padding: 0 0 8px; border-bottom: 1px solid var(--cb-line); }
.board-head > span:nth-child(n+3) { text-align: right; }
.board-head small { display: block; font: inherit; }
.board-row { font-size: var(--row-size); padding: 12px 0; border-bottom: 1px solid var(--cb-line); }
.system { line-height: 1.4; min-width: 0; }
.lead .system, .lead .score, .lead .class-count { color: var(--cb-accent); font-weight: 600; }
.bar { position: relative; height: var(--bar-height); min-width: 0; }
.fill { position: absolute; inset: 0 auto 0 0; width: var(--estimate); background: var(--bar-muted); }
.lead .fill { background: var(--cb-accent); }
.chance { position: absolute; top: -6px; bottom: -6px; left: var(--chance); border-left: 1px dashed var(--cb-muted); }
.interval { position: absolute; top: 50%; height: var(--whisker-width); left: var(--low); width: calc(var(--high) - var(--low)); background: var(--cb-text); transform: translateY(-50%); }
.cap { position: absolute; top: -4px; bottom: -4px; width: var(--whisker-width); background: var(--cb-text); transform: translateX(-50%); }
.cap-low { left: var(--low); } .cap-high { left: var(--high); }
.score, .class-count { text-align: right; font-family: var(--cb-mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
.ci { color: var(--cb-muted); font-size: var(--label-size); font-weight: 400; }
.mobile-counts { display: none; }
.axis { grid-column: 2; position: relative; height: 28px; font: var(--axis-size) var(--cb-mono); color: var(--cb-muted); }
.tick { position: absolute; top: 4px; left: var(--tick); transform: translateX(-50%); }
.tick:first-child { transform: none; } .tick:last-child { transform: translateX(-100%); }
figcaption { font-size: var(--row-size); color: var(--cb-muted); max-width: 90ch; margin-top: 12px; }
.method { max-width: 90ch; font-size: var(--body-size); color: var(--cb-muted); margin-top: 8px; }
.downloads { display: flex; flex-wrap: wrap; gap: 8px 24px; margin: 20px 0 0; font-size: var(--body-size); }
table { border-collapse: collapse; width: 100%; font-size: var(--body-size); }
caption { text-align: left; margin-bottom: 12px; color: var(--cb-muted); font-size: var(--body-size); }
th { font-weight: var(--label-weight); color: var(--cb-muted); text-align: left; }
th, td { padding: 10px 16px 10px 0; border-bottom: 1px solid var(--cb-line); vertical-align: top; }
th:last-child, td:last-child { padding-right: 0; }
td.numeric { font-family: var(--cb-mono); font-size: var(--row-size); font-variant-numeric: tabular-nums; white-space: nowrap; }
.reruns th:first-child { width: 30%; }
.reruns th:nth-child(2) { width: 30%; }
.note { color: var(--cb-muted); font-size: var(--row-size); margin-top: 12px; max-width: 90ch; }
.task { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 100ch; }
.task dt { font-weight: var(--label-weight); margin: 0 0 10px; }
.task dd { margin: 0; }
.task dl { margin: 0; }
.task ul { margin: 0; padding-left: 20px; }
.task li { margin: 0 0 6px; }
.task-image { display: block; max-width: 100%; width: 100%; height: auto; margin: 24px 0; }
.task-image[hidden] { display: none; }
.prose { max-width: 90ch; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; margin: 16px 0; padding: 14px 0 14px 20px; border-left: 2px solid var(--cb-line); font-size: var(--row-size); line-height: 1.8; }
code, pre { font-family: var(--cb-mono); }
code { overflow-wrap: anywhere; }
summary { cursor: pointer; color: var(--cb-accent); text-decoration: underline; text-underline-offset: 3px; }
details { margin-top: 20px; }
details p { margin-top: 12px; }
.license-copy { font-size: var(--body-size); max-width: 90ch; }
footer { margin-top: 40px; font-size: var(--body-size); display: flex; flex-wrap: wrap; gap: 8px 24px; }
@media (min-width: 768px) {
  main { padding: 40px var(--page-pad-wide) 80px; }
  h1 { font-size: var(--title-size-wide); } h2 { font-size: var(--heading-size-wide); }
}
@media (max-width: 1023px) {
  .board-grid { grid-template-columns: minmax(0, 1fr) auto; gap: 8px 16px; }
  .bar-head, .class-head, .class-count { display: none; }
  .board-head .score-head { grid-column: 2; }
  .system { grid-column: 1; grid-row: 1; }
  .score { grid-column: 2; grid-row: 1; }
  .bar { grid-column: 1 / -1; grid-row: 2; }
  .mobile-counts { display: block; grid-column: 1 / -1; grid-row: 3; font-size: var(--label-size); color: var(--cb-muted); }
  .axis { grid-column: 1 / -1; }
}
@media (max-width: 600px) {
  .board-head { align-items: end; } .board-row { padding: 14px 0; }
  .board-row .system { max-width: 22ch; }
  .score .ci { display: block; }
  .mobile-counts { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 2px 10px; }
  .reruns thead, .expert thead { display: none; }
  .reruns tr, .expert tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 6px 12px; padding: 14px 0; border-bottom: 1px solid var(--cb-line); }
  .reruns td, .expert td { border: 0; padding: 0; }
  .reruns td:first-child, .expert td:first-child { grid-column: 1 / -1; font-weight: var(--label-weight); }
  .reruns td:nth-child(2), .expert td:nth-child(2) { grid-column: 1; }
  .reruns td:nth-child(3), .expert td:nth-child(3) { grid-column: 2; }
  .reruns td:nth-child(4), .expert td:nth-child(4) { grid-column: 1 / -1; }
  td[data-label]::before { content: attr(data-label) ' '; color: var(--cb-muted); font: var(--label-size) var(--cb-sans); }
  .task { grid-template-columns: 1fr; gap: 24px; }
  section { margin-top: 36px; }
}
'''


def escape(value):
    return html.escape(str(value), quote=True)


def save(path, content):
    """Preserve the first pre-change version, including on repeated builds."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text() == content:
                return
            backup = Path(str(path) + BACKUP)
            if not backup.exists():
                subprocess.run(['/bin/cp', '-f', str(path), str(backup)], check=True)
        path.write_text(content)
        if path.read_text() != content:
            raise OSError('saved content did not match')
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f'Cannot write {path}: {exc}') from exc


class Builder:
    def __init__(self):
        self.inputs = {}
        self.numbers = []
        self.checks = []

    def read(self, name):
        path = ROOT / name
        try:
            text = path.read_text()
        except OSError as exc:
            raise RuntimeError(f'Cannot read required source {path}: {exc}') from exc
        self.inputs[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mtime_ns': path.stat().st_mtime_ns}
        return text

    def check(self, name, computed, source, source_path):
        if isinstance(computed, float) and isinstance(source, (int, float)):
            passed = math.isclose(computed, source, rel_tol=1e-12, abs_tol=1e-12)
        else:
            passed = computed == source
        self.checks.append({'name': name, 'computed': computed, 'source': source, 'source_path': source_path, 'passed': passed})
        if not passed:
            raise ValueError(f'Source mismatch for {name}: {computed!r} != {source!r} at {source_path}')

    def number(self, value, source, key, fmt='int'):
        if fmt == 'int':
            display = str(int(value))
        elif fmt == 'decimal':
            display = f'{value:.2f}'
        elif fmt == 'percent':
            display = f'{value * 100:.2f}%'
        elif fmt == 'confidence':
            display = f'{value * 100:g}%'
        else:
            display = str(value)
        index = len(self.numbers)
        self.numbers.append({'id': str(index), 'value': value, 'display': display, 'source': source, 'key': key, 'format': fmt})
        return f'<span data-number="{index}">{escape(display)}</span>'

    def sourced_text(self, text, source, key):
        """Register numerals in prose, commands, license text and model names."""
        pieces = []; cursor = 0
        for match in re.finditer(r'\d+(?:[.,]\d+)*', text):
            pieces.append(escape(text[cursor:match.start()]))
            pieces.append(self.number(match.group(), source, key, 'literal'))
            cursor = match.end()
        pieces.append(escape(text[cursor:]))
        return ''.join(pieces)

    def json(self, name, data):
        save(SITE / 'data' / name, json.dumps(data, indent=2, ensure_ascii=False) + '\n')

    def build(self, check_output):
        readme = self.read('README.md')
        license_text = self.read('DATA_LICENSE.md')
        citation_text = self.read('CITATION.cff')
        paper = json.loads(self.read('reference_results/paper_metrics.json'))
        reproduced = json.loads(self.read('reference_results/reproduced_metrics.json'))
        cohorts = json.loads(self.read('reference_results/cohorts.json'))
        s18 = list(csv.DictReader(self.read('reference_results/supplementary_table_s18.csv').splitlines()))
        psource = 'reference_results/paper_metrics.json'
        rsource = 'reference_results/reproduced_metrics.json'
        n = self.number
        def pn(v, k, fmt='int'): return n(v, psource, k, fmt)
        def rn(v, k, fmt='int'): return n(v, rsource, k, fmt)
        def ci(v, source, key):
            return f'{n(v[0], source, key + "/low", "decimal")} to {n(v[1], source, key + "/high", "decimal")}'
        def percent_ci(v, source, key):
            return f'{n(v[0], source, key + "/low", "percent")} to {n(v[1], source, key + "/high", "percent")}'
        # The task sentence is copied from the README, with the decided name.
        intro = re.search(r'(?:AgingAgentBench|ClockEffectBench) measures.*?GEO data\.', readme, re.S)
        if not intro:
            raise ValueError('README measurement sentence is missing')
        intro = ' '.join(intro.group().split()).replace('ClockEffectBench', 'AgingAgentBench')
        intro = intro.replace('AgingAgentBench measures', 'The benchmark measures', 1)   # the title already names it
        inventory = re.search(r'dataset contains (\d+) contrasts from (\d+) papers on (\d+)\s+GEO series', readme)
        if not inventory:
            raise ValueError('README published-effects inventory is missing')
        totals = dict(zip(['contrasts', 'papers', 'series'], map(int, inventory.groups())))
        main_key = next(k for k in cohorts if k.startswith('main'))
        task_key = next(k for k in cohorts if k.startswith('agent_task'))
        level = reproduced['published']['clockbase_paper_groups@' + main_key]['bootstrap']['level']
        level_display = n(level, rsource, 'published/clockbase_paper_groups/bootstrap/level', 'confidence')
        self.check('main cohort inventory', len(cohorts[main_key]), paper['published_group_comparison']['records'], psource + '/published_group_comparison/records')
        labels = {
            'S0': 'Always higher', 'S3': 'ClockBase with Welch tests',
            'S3c': "ClockBase with the paper's groups",
            'S3r': 'ClockBase with individual readers',
        }
        files = {'S0': 'constant_higher', 'S3': 'clockbase_paper_groups_welch', 'S3c': 'clockbase_paper_groups', 'S3r': 'clockbase_paper_groups_individual_readers'}
        for system in paper['three_way']:
            if system.startswith('S4:'):
                model = system.split(':')[-1]
                labels[system] = model.replace('gpt-', 'GPT-', 1).replace('-astra', ' Astra').replace('-luna', ' Luna').replace('-sol', ' Sol') + ' without data'
                files[system] = 'language_model_' + model.replace('-', '_').replace('.', '_')
        systems = []
        for system, metric in paper['three_way'].items():
            key = files[system] + '@' + main_key
            result = reproduced['published'][key]
            predictions = list(csv.DictReader(self.read('reference_results/' + files[system] + '.csv').splitlines()))
            submitted = len({r['record_id'] for r in predictions} & set(cohorts[main_key]))
            self.check(system + ' CSV submitted coverage', submitted, result['submitted'], rsource + '/published/' + key + '/submitted')
            for field in ['balanced_accuracy', 'balanced_accuracy_interval']:
                a, b = metric[field], result[field]
                if isinstance(a, list):
                    for i, (x, y) in enumerate(zip(a, b)):
                        self.check(system + '/' + field + '/' + str(i), y, x, psource + '/three_way/' + system + '/' + field)
                else:
                    self.check(system + '/' + field, b, a, psource + '/three_way/' + system + '/' + field)
            for cls, pair in metric['recall'].items():
                self.check(system + '/recall/' + cls, result['recall']['not significant' if cls == 'none' else cls], pair, psource + '/three_way/' + system + '/recall/' + cls)
            self.check(system + '/balanced_accuracy from recalls', sum(a / b for a,b in metric['recall'].values()) / len(metric['recall']), metric['balanced_accuracy'], psource + '/three_way/' + system)
            systems.append({'id': system, 'name': labels[system], **metric, 'prediction_file': files[system] + '.csv'})
        systems.sort(key=lambda x: (x['id'] != 'S3c', -x['balanced_accuracy']))
        classes = [('lower', 'Decreases'), ('higher', 'Increases'), ('none', 'No significant difference')]
        chance = paper['three_way']['S0']['balanced_accuracy']
        self.check('chance from classes', 1 / len(classes), chance, psource + '/three_way/S0/balanced_accuracy')
        heads = ''.join(f'<span class="class-head">{label}<small>of {pn(systems[0]["recall"][cls][1], "three_way/S3c/recall/"+cls+"/denominator")} published</small></span>' for cls, label in classes)
        rows = []
        for row in systems:
            ident = row['id']; key = 'three_way/' + ident
            low, high = row['balanced_accuracy_interval']
            counts = [f'{pn(row["recall"][cls][0], key+"/recall/"+cls+"/numerator")}/{pn(row["recall"][cls][1], key+"/recall/"+cls+"/denominator")}' for cls, _ in classes]
            name = self.sourced_text(row['name'], psource, key)
            style = f'--estimate:{row["balanced_accuracy"] * 100}%;--low:{low * 100}%;--high:{high * 100}%;--chance:{chance * 100}%'
            rows.append(f'''<div class="board-grid board-row{' lead' if ident == 'S3c' else ''}" style="{style}">
<span class="system">{name}</span><div class="bar" aria-hidden="true"><span class="fill"></span><span class="chance"></span><span class="interval"></span><span class="cap cap-low"></span><span class="cap cap-high"></span></div>
<span class="score">{pn(row['balanced_accuracy'], key+'/balanced_accuracy', 'decimal')} <span class="ci">({ci(row['balanced_accuracy_interval'], psource, key+'/balanced_accuracy_interval')})</span></span>
{''.join('<span class="class-count">'+count+'</span>' for count in counts)}
<span class="mobile-counts">{''.join('<span>'+label+' '+count+'</span>' for (_,label), count in zip(classes,counts))}</span></div>''')
        endpoints = [paper['three_way']['S0']['recall']['lower'][0], max(paper['three_way']['S0']['balanced_accuracy_interval']) * len(classes)]
        ticks = [endpoints[0] + (endpoints[1]-endpoints[0]) * i / 4 for i in range(5)]
        axis = ''.join(f'<span class="tick" style="--tick:{v*100}%">{pn(v, "derived scale endpoints from three_way/S0", "literal")}</span>' for v in ticks)
        # Published call intervals use the source's own-coverage paper bootstrap.
        reruns = []
        for framework, group in paper['reruns'].items():
            for system, metric in group['own_coverage'].items():
                if not (system.startswith('R:') and system.endswith(':raw')):
                    continue
                model = system.split(':')[1]
                stem = 'agent_' + framework + '_' + model.replace('-', '_').replace('.', '_') + '_raw'
                result = reproduced['published'][stem + '@' + task_key]
                path = f'reruns/{framework}/own_coverage/{system}'
                for field, target in [('call_agreement', 'call_agreement'), ('call_n', 'scored'), ('covered', 'submitted')]:
                    self.check(path + '/' + field, result[target], metric[field], psource + '/' + path + '/' + field)
                predictions = list(csv.DictReader(self.read('reference_results/' + stem + '.csv').splitlines()))
                self.check(stem + ' CSV submitted coverage', len({r['record_id'] for r in predictions} & set(cohorts[task_key])), result['submitted'], rsource + '/published/' + stem + '@' + task_key)
                display_model = model.replace('gpt-', 'GPT-', 1).replace('-astra', ' Astra').replace('-sol', ' Sol').replace('-luna', ' Luna')
                if model.startswith('claude-'):
                    parts = model.split('-'); display_model = ' '.join(x.title() for x in parts[:-2]) + ' ' + '.'.join(parts[-2:])
                label = {'codex':'Codex', 'claude_code':'Claude Code', 'biomni':'Biomni'}[framework] + ' with ' + display_model
                candidates = [(i,r) for i,r in enumerate(s18) if r['measure']=='Agent reruns: three-way call agrees' and 'each system on the results it covers' in r['note'] and r['stage'].endswith('reported result') and r['stage'].startswith({'codex':'Codex', 'claude_code':'Claude Code', 'biomni':'Biomni'}[framework]) and display_model in r['stage']]
                if len(candidates) != 1:
                    raise ValueError('Cannot resolve supplementary source for ' + label)
                sindex, supplemental = candidates[0]
                self.check(stem+' supplementary denominator', result['scored'], int(supplemental['denominator']), 'reference_results/supplementary_table_s18.csv/row/'+str(sindex))
                self.check(stem+' supplementary numerator', sum(pair[0] for pair in result['recall'].values()), int(supplemental['numerator']), 'reference_results/supplementary_table_s18.csv/row/'+str(sindex))
                reruns.append({'name':label,'source_path':path,'published_call_agreement':metric['call_agreement'],'interval':metric['call_agreement_interval'],'n':metric['call_n'],'direction_matches':result['direction_agreement'],'supplementary_row':sindex,'reproduced_key':stem+'@'+task_key})
        stored = paper['reruns']['codex']['own_coverage']['S1']
        stored_result = reproduced['published']['clockbase_agent_stored@' + task_key]
        self.read('reference_results/clockbase_agent_stored.csv')
        self.check('stored agent call agreement', stored_result['call_agreement'], stored['call_agreement'], psource+'/reruns/codex/own_coverage/S1')
        reruns.insert(0, {'name':'Stored ClockBase agent','source_path':'reruns/codex/own_coverage/S1','published_call_agreement':stored['call_agreement'],'interval':stored['call_agreement_interval'],'n':stored['call_n'],'direction_matches':stored_result['direction_agreement'],'reproduced_key':'clockbase_agent_stored@'+task_key})
        rerun_rows = []
        for row in reruns:
            k = row['source_path']
            rerun_rows.append(f'<tr><td>{self.sourced_text(row["name"], psource, k)}</td><td class="numeric" data-label="Agreement">{pn(row["published_call_agreement"], k+"/call_agreement", "percent")}<br><span class="ci">{percent_ci(row["interval"], psource, k+"/call_agreement_interval")}</span></td><td class="numeric" data-label="n">{pn(row["n"], k+"/call_n")}</td><td class="numeric" data-label="Direction">{rn(row["direction_matches"][0], "published/"+row["reproduced_key"]+"/direction_agreement/numerator")}/{rn(row["direction_matches"][1], "published/"+row["reproduced_key"]+"/direction_agreement/denominator")}</td></tr>')
        experts = []
        truth = list(csv.DictReader(self.read('reference_results/expert_truth.csv').splitlines()))
        candidates = {r['record_id']:r for r in csv.DictReader(self.read('reference_results/expert_candidate.csv').splitlines())}
        for modality, name in [('A1', 'Mouse RNA-seq'), ('A2', 'Human DNA methylation')]:
            for scope, scope_name in [('labels confirmed','Confirmed orientation'), ('all released rows','All orientations')]:
                key = f'{modality}.candidate.{scope}'; metric = reproduced['expert'][key]
                matches = sum(pair[0] for pair in metric['recall'].values())
                selected = [r for r in truth if r['record_id'].startswith('expert|'+modality+':') and r['record_id'] in candidates and (scope != 'labels confirmed' or r.get('label_unconfirmed','').lower() == 'false') and r.get('published_call')]
                # Validate final candidate agreement against frozen expert calls.
                if not selected: raise ValueError('Expert truth rows missing: '+key)
                if selected:
                    computed = sum(r['published_call'] == candidates[r['record_id']]['call'] for r in selected)
                    self.check(key+' CSV n',len(selected),metric['scored'],rsource+'/expert/'+key)
                    self.check(key+' CSV matches',computed,matches,rsource+'/expert/'+key)
                self.check(key+' agreement from matches',matches/metric['scored'],metric['call_agreement'],rsource+'/expert/'+key+'/call_agreement')
                experts.append({'name':name,'scope':scope_name,'key':key,'matches':matches,'n':metric['scored'],'agreement':metric['call_agreement']})
        expert_rows = ''.join(f'<tr><td>{row["name"]}</td><td>{row["scope"]}</td><td class="numeric" data-label="Agreement">{rn(row["agreement"], "expert/"+row["key"]+"/call_agreement", "percent")}</td><td class="numeric" data-label="Matches">{rn(row["matches"], "expert/"+row["key"]+"/recall diagonal sum")}/{rn(row["n"], "expert/"+row["key"]+"/scored")}</td></tr>' for row in experts)
        # Read exact installation and scoring commands from the quick-start block.
        quick_start = re.search(r'## Quick start.*?```sh\n(.*?)```', readme, re.S)
        if not quick_start:
            raise ValueError('README quick-start commands are missing')
        commands = quick_start.group(1).strip()
        commands = '\n'.join(line for line in commands.splitlines() if not line.startswith('pytest'))
        renamed_fallback = 'clockeffectbench' in commands
        commands = commands.replace('clockeffectbench', 'agingagentbench')
        # CFF preferred citation is a bounded YAML subset, so no YAML dependency.
        preferred = citation_text.split('preferred-citation:',1)[1]
        cff = {key: re.search(r'^  '+key+r':\s*(.+)$', preferred, re.M).group(1).strip('"') for key in ['title','journal','year','doi']}
        family = re.search(r'family-names:\s*"?([^"\n]+)', preferred).group(1)
        citation = f'{family} K, et al. {cff["title"]}. {cff["journal"]} ({cff["year"]}).'
        # Render license paragraphs with source links and inline code preserved.
        license_text = license_text.replace('ClockEffectBench','AgingAgentBench')
        paras = re.split(r'\n\s*\n', license_text.strip())[1:]
        license_html = []
        for paragraph in paras:
            text = ' '.join(paragraph.split())
            pieces = []; cursor = 0
            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
                pieces.append(self.sourced_text(text[cursor:match.start()], 'DATA_LICENSE.md', 'license paragraphs'))
                href = match.group(2)
                if not href.startswith('https://'): href = REPOSITORY + '/blob/main/' + href
                pieces.append('<a href="'+escape(href)+'">'+self.sourced_text(match.group(1), 'DATA_LICENSE.md', 'license link label')+'</a>')
                cursor = match.end()
            pieces.append(self.sourced_text(text[cursor:], 'DATA_LICENSE.md', 'license paragraphs'))
            rendered = ''.join(pieces)
            rendered = re.sub(r'`([^`]+)`',r'<code>\1</code>',rendered)
            license_html.append('<p>'+rendered+'</p>')
        description = intro
        img = '<img class="task-image" src="assets/task.png" width="1600" height="900" alt="A benchmark task from public study inputs to an aging-clock call and comparison with the published result"'+('' if (SITE/'assets/task.png').is_file() else ' hidden')+'>'
        main_n = n(len(cohorts[main_key]),'reference_results/cohorts.json', main_key+'/length')
        published_papers = pn(paper['published_group_comparison']['papers'],'published_group_comparison/papers')
        task_n = n(len(cohorts[task_key]),'reference_results/cohorts.json',task_key+'/length')
        task_summary = re.search(r'cohort contains (\d+) published results on the task.s clocks\s+from (\d+) papers and (\d+) series',readme)
        if not task_summary:
            raise ValueError('README agent task summary is missing')
        task_papers = n(int(task_summary.group(2)),'README.md','agent task papers')
        task_series = n(int(task_summary.group(3)),'README.md','agent task series')
        html_text = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgingAgentBench</title><meta name="description" content="{escape(description)}">
<link rel="canonical" href="{PUBLIC}"><meta property="og:type" content="website"><meta property="og:title" content="AgingAgentBench"><meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{PUBLIC}"><meta property="og:image" content="{PUBLIC}assets/card.png"><meta property="og:image:width" content="1600"><meta property="og:image:height" content="900"><meta property="og:image:alt" content="AgingAgentBench published aging-clock effect benchmark">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="AgingAgentBench"><meta name="twitter:description" content="{escape(description)}"><meta name="twitter:image" content="{PUBLIC}assets/card.png"><meta name="twitter:image:alt" content="AgingAgentBench published aging-clock effect benchmark">
<link rel="stylesheet" href="{escape(FONT_URL)}"><link rel="stylesheet" href="style.css"><link rel="icon" href="data:,"></head>
<body><main><header><h1>AgingAgentBench</h1><p>{escape(intro)}</p></header>
<figure class="leaderboard" aria-label="Shared comparison of recovery of published calls">
<div class="board-grid board-head"><span>System</span><span class="bar-head">Balanced accuracy</span><span class="score-head">Balanced accuracy<br>({level_display} CI)</span>{heads}</div>
{''.join(rows)}<div class="board-grid"><div class="axis">{axis}</div></div>
<figcaption>Balanced accuracy is the mean recall over the published classes. Whiskers show the confidence interval from resampling papers. The dashed line marks chance at {pn(chance,'three_way/S0/balanced_accuracy','decimal')}.</figcaption></figure>
<p class="method">Every system is scored on the same {main_n} human DNA methylation results from {published_papers} papers using the paper's groups. Language models receive study descriptions and group definitions without data. The constant rule always answers higher.</p>
<nav class="downloads" aria-label="Benchmark resources"><a href="{REPOSITORY}">Repository</a><a href="{REPOSITORY}/blob/main/data/published.csv">Published effects CSV</a><a href="data/leaderboard.json">Leaderboard JSON</a></nav>
<section aria-labelledby="reruns"><h2 id="reruns">Agent reruns</h2><table class="reruns"><caption>Reported calls on {task_series} benchmark series with {task_n} published results from {task_papers} papers. Each system is scored on the results it covers.</caption><thead><tr><th scope="col">System</th><th scope="col">Published-call agreement<br>({level_display} CI)</th><th scope="col">n</th><th scope="col">Direction matches</th></tr></thead><tbody>{''.join(rerun_rows)}</tbody></table><p class="note">Intervals resample papers. Direction matches use published significant results. <a href="data/agent-reruns.json">Agent rerun JSON</a></p></section>
<section aria-labelledby="expert"><h2 id="expert">Expert annotation agreement</h2><table class="expert"><thead><tr><th scope="col">Modality</th><th scope="col">Arm orientation</th><th scope="col">Agreement</th><th scope="col">Matches</th></tr></thead><tbody>{expert_rows}</tbody></table><p class="note">Final candidate calls are compared with calls from complete expert-defined groups, using the same clock outputs and test rules. <a href="data/expert-agreement.json">Expert agreement JSON</a></p></section>
<section aria-labelledby="task"><h2 id="task">The task</h2><div class="task"><dl><dt>Inputs</dt><dd><ul><li>Public GEO molecular data and sample annotation.</li><li>Study description, case and control groups, clock, and measure.</li><li>Answer-free task records with a preserved <code>record_id</code>.</li></ul></dd></dl><dl><dt>Returns</dt><dd><ul><li><code>higher</code>, <code>lower</code>, or <code>not significant</code>.</li><li>Optional direction and P value for direction AUROC.</li><li>Optional signed effect with units for effect-size scoring.</li></ul></dd></dl></div>{img}<p class="prose">Compare the case group with the control group using the specified clock and measure. Use the paper's significance threshold, or P &lt; {self.sourced_text(re.search(r'P &lt; ([\d.]+)|P < ([\d.]+)',readme).group(0).split()[-1],'README.md','Evaluate your system significance threshold')} when it states none. Balanced accuracy scores the mean recall of the published classes present. Missing predictions are abstentions; coverage and metric denominators are reported. Keep reference outcomes in the scoring environment.</p></section>
<section aria-labelledby="use"><h2 id="use">Use it</h2><pre><code>{self.sourced_text(commands,'README.md','Quick start shell block')}</code></pre><p class="prose">Install from a local checkout of the <a href="{REPOSITORY}">repository</a>. Submit predictions with the task identifiers and calls. <a href="{REPOSITORY}/blob/main/README.md#evaluate-your-system">Prediction format and scoring options</a></p></section>
<section aria-labelledby="data"><h2 id="data">Data</h2><p class="prose">The published-effects dataset contains {n(totals['contrasts'],'README.md','dataset contrasts')} contrasts from {n(totals['papers'],'README.md','dataset papers')} papers on {n(totals['series'],'README.md','dataset GEO series')} GEO series. The reference is what each paper reports for its clock, measure, and groups.</p><p class="downloads"><a href="{REPOSITORY}/blob/main/data/tasks.jsonl">Task records</a><a href="{REPOSITORY}/tree/main/reference_results">Reference predictions</a><a href="{REPOSITORY}/blob/main/reference_results/supplementary_table_s18.csv">Supplementary source table</a><a href="data/provenance.json">Data provenance</a></p></section>
<section aria-labelledby="license"><h2 id="license">License</h2><p class="prose">Code is licensed under <a href="{REPOSITORY}/blob/main/LICENSE">MIT</a>. The data compilation and numerical outputs use <a href="https://creativecommons.org/licenses/by/4.0/">{self.sourced_text('CC BY '+re.search(r'CC BY ([\d.]+)',license_text).group(1),'DATA_LICENSE.md','compilation license')}</a>.</p><details><summary>Data reuse terms</summary><div class="license-copy">{''.join(license_html)}</div></details></section>
<section aria-labelledby="citation"><h2 id="citation">Citation</h2><p class="prose">{self.sourced_text(citation,'CITATION.cff','preferred-citation')} <a href="https://doi.org/{escape(cff['doi'])}">{self.sourced_text(cff['doi'],'CITATION.cff','preferred-citation/doi')}</a></p></section>
<footer><a href="{REPOSITORY}/blob/main/CITATION.cff">Citation file</a><a href="data/site-numbers.json">Site numbers JSON</a></footer></main></body></html>\n'''
        root_css = ':root {\n' + ''.join(f'  --{key}: {value};\n' for key,(value,_,_) in TOKENS.items()) + '}\n'
        dark_css = '@media (prefers-color-scheme: dark) {\n  :root {\n' + ''.join(f'    --{key}: {value};\n' for key,value in DARK.items()) + '  }\n  html { color-scheme: dark; }\n}\n'
        save(SITE/'index.html',html_text)
        save(SITE/'style.css',root_css+CSS+dark_css)
        save(SITE/'.nojekyll','')
        self.json('leaderboard.json',{'cohort':main_key,'records':len(cohorts[main_key]),'papers':paper['published_group_comparison']['papers'],'confidence_level':level,'chance':chance,'systems':systems})
        self.json('agent-reruns.json',{'cohort':task_key,'records':len(cohorts[task_key]),'interval_method':'paper bootstrap','systems':reruns})
        self.json('expert-agreement.json',{'prediction_variant':'expert_candidate.csv','systems':experts})
        self.json('site-numbers.json',self.numbers)
        self.json('provenance.json',{'inputs':self.inputs,'inventory':totals,'command_rename_fallback':renamed_fallback,'citation':cff,'number_format':'Metrics retain full precision in JSON. Displayed metrics use decimal or percent formatting.','image_slot':'task.png remains hidden when absent at build time; rerun builder after adding it.'})
        token_lines = [f'- `--{key}: {value}`. Source `{REFERENCE}/{file}`, `{selector}`.' for key,(value,file,selector) in TOKENS.items()]
        token_lines += [f'- Dark `--{key}: {value}`. Source `{REFERENCE}/src/styles.css`, `html[data-theme="dark"]`.' for key,value in DARK.items()]
        design = '# Website design\n\nThe working surface follows the ClockBase benchmark named in the task.\nThe leaderboard opens the page. Section order carries the explanation.\n\n## Tokens\n\n'+'\n'.join(token_lines)+'\n\n## Typography\n\nThe single Google Fonts stylesheet is copied from `'+REFERENCE+'/index.html`:\n\n`'+FONT_URL+'`\n\nThe stylesheet supplies IBM Plex Sans and IBM Plex Mono with system fallbacks.\n\n## Layout\n\n`'+REFERENCE+'/src/components/Benchmark.jsx`, `Leaderboard`, supplies the ranked bars, ClockBase-first ordering, class columns, chance line, and interval whiskers. The system column widens to fit the additional source variants. Phones stack the system and value above a full-width bar, followed by class matches. Row rules separate observations as in the reference. The neutral ground and one accent follow the source theme tokens. Dark mode follows the system preference without JavaScript. The source dark background gradients are omitted because this page is a static working surface.\n\n## Style checks\n\nThe title sentence and image dimensions are explicit task requirements. The title sentence is the README measurement sentence, not a marketing tagline. The task image is hidden when absent at build time. Rebuild after adding it. No script, decorative card, shadow, icon, or motion is used. Data tables and the command block have boundaries defined by their contents.\n\nThe style checker reports a trailing parenthetical on the agreement column. This is a confidence-interval abbreviation with its confidence level, copied from the reference table; it is a unit of the measurement, not a subtitle. It also flags the prediction filename in the command and the expert filenames in the license. The command is copied from README.md and must be executable. DATA_LICENSE.md assigns distinct terms to the named expert files, so those exact paths are necessary for reuse. These findings are retained with their source evidence.\n'
        save(SITE/'DESIGN.md',design)
        # Parse the saved file and compare every registered numeral with the text.
        class NumericParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True); self.active=[]; self.seen={}; self.headings=[]; self.heading=None; self.stack=[]; self.visible=[]; self.in_body=False; self.tag_stack=[]; self.command=[]; self.in_pre=False
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=='body': self.in_body=True
                if tag=='pre': self.in_pre=True
                if tag=='span': self.stack.append(attrs.get('data-number'))
                if tag in ['h1','h2','h3']: self.heading=[]
            def handle_data(self,data):
                if self.stack and self.stack[-1] is not None: self.seen.setdefault(self.stack[-1],[]).append(data)
                if self.heading is not None:self.heading.append(data)
                if self.in_body:self.visible.append(data)
                if self.in_pre:self.command.append(data)
            def handle_endtag(self,tag):
                if tag=='span' and self.stack:self.stack.pop()
                if tag in ['h1','h2','h3'] and self.heading is not None:
                    self.headings.append(''.join(self.heading));self.heading=None
                if tag=='body':self.in_body=False
                if tag=='pre':self.in_pre=False
        parser=NumericParser();parser.feed((SITE/'index.html').read_text());parser.close()
        self.check('saved console command matches README', ''.join(parser.command), commands, 'README.md/Quick start')
        for number in self.numbers:
            observed=parser.seen.get(number['id'],[])
            self.check('saved HTML number '+number['id'],observed,[number['display']] * len(parser.seen.get(number['id'],[])),number['source']+'/'+number['key'])
            if not parser.seen.get(number['id']): raise ValueError('Numeric text missing from saved HTML: '+number['id'])
        # Unregistered digits are permitted only inside explanatory source strings
        # already registered by sourced_text; all visible numeric text is spanned.
        visible_numeric_tokens=[token for chunk in parser.visible for token in re.findall(r'\d+(?:[.,]\d+)*',chunk)]
        registered_numeric_tokens=[]
        for chunks in parser.seen.values():
            for chunk in chunks: registered_numeric_tokens.extend(re.findall(r'\d+(?:[.,]\d+)*',chunk))
        self.check('all visible numeric tokens registered',sorted(visible_numeric_tokens),sorted(registered_numeric_tokens),'docs/index.html/body')
        save(SITE/'data/headings.md','\n\n'.join('# '+heading for heading in parser.headings)+'\n')
        check={'passed':all(c['passed'] for c in self.checks),'inputs':self.inputs,'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file() and BACKUP not in p.name},'checks':self.checks,'numbers':self.numbers,'command_rename_fallback':renamed_fallback,'known_source_difference':'Archived expert_conclusions error counts differ from final candidate results. Expert agreement uses reproduced_metrics expert candidate recall counts and expert_candidate.csv; expert intervals are not displayed.'}
        save(check_output,json.dumps(check,indent=2,ensure_ascii=False)+'\n')
        print('Built '+str(SITE/'index.html'))
        print('Number comparison passed: '+str(check_output))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-output',type=Path,default=ROOT.parent/'agingagentbench_2026-11-13/site_number_check.json')
    args=parser.parse_args()
    try:
        Builder().build(args.check_output)
    except (OSError,ValueError,KeyError,RuntimeError,StopIteration,IndexError,AttributeError) as exc:
        print('Site build failed: '+str(exc),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
