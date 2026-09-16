"""Build a portable, folder-based Markdown notebook: python scripts/build.py."""
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import html
import json
import re
import shutil
import markdown
import yaml
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / 'notes'
OUT = ROOT / 'dist'
esc = lambda value: html.escape(str(value), quote=True)

class MathPreprocessor(Preprocessor):
    def run(self, lines):
        source = '\n'.join(lines)
        # Protect code before handling TeX; math is stashed before Markdown parsing.
        pattern = r'(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1[^\n]*$|`+[^`\n]+`+|\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|(?<![\\$])\$(?!\s)([^\n$]+?)(?<!\s)\$(?!\$)|\\\((.+?)\\\)'
        def replace(match):
            if match.group(1) or match.group(0).startswith('`'):
                return match.group(0)
            display = match.group(2) is not None or match.group(3) is not None
            value = next(x for x in match.groups()[1:] if x is not None)
            tag = 'div' if display else 'span'
            return self.md.htmlStash.store(f'<{tag} class="math" data-display="{str(display).lower()}">{esc(value.strip())}</{tag}>')
        return re.sub(pattern, replace, source, flags=re.M).split('\n')

class MathExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MathPreprocessor(md), 'notebook_math', 29)

def note_url(path):
    return '/read/' + quote(path.with_suffix('.html').as_posix())

class Links(HTMLParser):
    def __init__(self, source, known):
        super().__init__(convert_charrefs=False)
        self.source, self.known, self.result = source, known, []
    def resolve(self, value):
        value = value.replace('\\', '/')
        parsed = urlsplit(value)
        if parsed.scheme == 'file' or re.match(r'^[A-Za-z]:/', value):
            raise ValueError(f'{self.source}: 本机绝对路径无法发布，请先运行 import_notes.py 导入: {value}')
        if parsed.scheme or parsed.netloc or not parsed.path:
            return value
        target = ((NOTES / unquote(parsed.path).lstrip('/')) if parsed.path.startswith('/') else self.source.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(NOTES.resolve()):
            raise ValueError(f'{self.source}: 路径超出 notes 目录: {value}')
        if not target.exists():
            raise ValueError(f'{self.source}: 找不到链接或图片: {value}')
        rel = target.relative_to(NOTES.resolve())
        if any(part.startswith('.') for part in rel.parts):
            raise ValueError(f'{self.source}: 不能引用隐藏文件: {value}')
        if target.suffix.lower() == '.md':
            if rel not in self.known:
                raise ValueError(f'未发布的笔记: {value}')
            url = note_url(rel)
        else:
            url = '/content/' + quote(rel.as_posix())
        return url + ('?' + parsed.query if parsed.query else '') + ('#' + parsed.fragment if parsed.fragment else '')
    def handle_starttag(self, tag, attrs):
        values = []
        for key, value in attrs:
            if value is not None and ((tag == 'a' and key == 'href') or (tag in ('img', 'source', 'video', 'audio') and key == 'src')):
                value = self.resolve(value)
            values.append(key if value is None else f'{key}="{esc(value)}"')
        if tag == 'img':
            values.append('loading="lazy"')
        self.result.append('<' + tag + (' ' + ' '.join(values) if values else '') + '>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag): self.result.append(f'</{tag}>')
    def handle_data(self, data): self.result.append(data)
    def handle_entityref(self, name): self.result.append(f'&{name};')
    def handle_charref(self, name): self.result.append(f'&#{name};')
    def handle_comment(self, data): self.result.append(f'<!--{data}-->')

def plain(value):
    return html.unescape(re.sub('<[^>]+>', ' ', value))

def shell(title, body, active='', toc=''):
    nav = ''.join(f'<a class="folder {"active" if c == active else ""}" href="/?category={quote(c)}"><span>▱ &nbsp;{esc(c)}</span><small>{sum(n["category"] == c for n in records):02}</small></a>' for c in categories)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Elysiason 的学习笔记，记录、连接与理解。"><title>{esc(title)} · Elysiason</title><link rel="icon" href="/assets/icon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css"><link rel="stylesheet" href="/lib/katex/{katex_css}"><script src="/assets/app.js" defer></script><script src="/assets/katex.js" defer></script></head>
<body><aside class="sidebar"><a class="brand" href="/"><span class="brand-icon">E.</span><span>Elysiason<small>LEARNING NOTEBOOK</small></span></a><div class="side-intro">把学过的知识，<br>变成自己的理解。</div><a class="all-link" href="/">▦ &nbsp; 全部笔记 <small>{len(records):02}</small></a><div class="nav-label">知识分类</div><nav aria-label="笔记分类">{nav}</nav><div class="side-bottom"><span class="status-dot"></span> 持续学习，慢慢积累<a href="https://github.com/Elysiason/Elysiason.github.io">GitHub ↗</a></div></aside><div class="workspace"><header class="topbar"><span>个人知识库 <span class="muted">/ &nbsp; 学习笔记</span></span><button id="theme" class="icon-button" aria-label="切换深色模式">◐</button></header>{body}<footer>写下来，是理解的开始。<span>ELYSiASON / NOTES</span></footer></div>{toc}</body></html>'''

def build():
    global records, categories, katex_css
    records = []
    if not NOTES.is_dir():
        raise ValueError('找不到 notes/ 目录，请先放入 Markdown 笔记。')
    sources = sorted(p for p in NOTES.rglob('*') if p.suffix.lower() == '.md' and not any(x.startswith('.') for x in p.relative_to(NOTES).parts))
    known = {p.relative_to(NOTES) for p in sources}
    for source in sources:
        raw = source.read_text(encoding='utf-8-sig')
        metadata = {}
        if raw.startswith('---\n'):
            front = re.match(r'^---\n(.*?)\n---(?:\n|$)', raw, re.S)
            if front:
                metadata = yaml.safe_load(front.group(1)) or {}
                if not isinstance(metadata, dict):
                    raise ValueError(f'{source}: YAML 元数据必须为键值对')
                raw = raw[front.end():]
        title_match = re.search(r'^#\s+(.+)$', raw, re.M)
        title = str(metadata.get('title') or (title_match.group(1).strip() if title_match else source.stem))
        if title_match:
            raw = raw[:title_match.start()] + raw[title_match.end():]
        md = markdown.Markdown(extensions=['extra', 'toc', 'sane_lists', MathExtension()], extension_configs={'toc': {'permalink': False}})
        rendered = md.convert(raw)
        links = Links(source, known)
        links.feed(rendered)
        rendered = ''.join(links.result)
        rel = source.relative_to(NOTES)
        category = rel.parent.as_posix() if rel.parent != Path('.') else '未分类'
        text = re.sub(r'\s+', ' ', plain(rendered)).strip()
        records.append(dict(title=title, category=category, url=note_url(rel), path=rel.as_posix(), excerpt=text[:120], text=text, minutes=max(1, round(len(text)/500)), body=rendered, toc=md.toc))
    categories = sorted({n['category'] for n in records})
    katex_css = next((ROOT / 'lib/katex').glob('*.css')).name
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'site', OUT / 'assets')
    shutil.copytree(ROOT / 'lib/katex', OUT / 'lib/katex')
    shutil.copyfile(next((ROOT / 'js').glob('katex.bundle.*.js')), OUT / 'assets/katex.js')
    for source in NOTES.rglob('*'):
        if source.is_file() and source.suffix.lower() != '.md' and not any(x.startswith('.') for x in source.relative_to(NOTES).parts):
            target = OUT / 'content' / source.relative_to(NOTES)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    cards = ''.join(f'<a class="note-card" href="{n["url"]}"><span class="card-category">{esc(n["category"])}</span><h2>{esc(n["title"])}</h2><p>{esc(n["excerpt"])}</p><div class="card-bottom"><span>{n["minutes"]} 分钟阅读</span><span>阅读笔记 ↗</span></div></a>' for n in records)
    home = f'''<main class="home"><section class="hero"><div class="eyebrow">THE GARDEN OF KNOWLEDGE</div><h1>记录所学，<br>让知识<span>生长。</span></h1><p>一些思考，一些探索，一点点积累。<br>在这里，把零散的知识连接成自己的地图。</p><div class="hero-stats"><strong>{len(records):02}</strong> 篇笔记 <i></i><strong>{len(categories):02}</strong> 个分类</div><div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><span class="art-dot"></span><span class="art-star">✳</span><span class="art-caption">STAY CURIOUS.<br>KEEP GROWING.</span></div></section><section class="collection"><div class="collection-top"><div><div class="eyebrow">EXPLORE THE NOTES</div><h2 id="collection-title">全部笔记 <span id="result-count">{len(records)}</span></h2></div><label class="search"><span>⌕</span><input id="search" type="search" placeholder="搜索标题或笔记内容…" aria-label="搜索笔记"><kbd>/</kbd></label></div><div class="filters" id="filters"><button data-category="" class="selected">全部</button>{''.join(f'<button data-category="{esc(c)}">{esc(c)}</button>' for c in categories)}</div><div id="notes-grid" class="notes-grid">{cards}</div><p id="empty" hidden>没有找到相关笔记，试试其他关键词。</p><p class="collection-end">每一篇笔记，都是理解世界的一小步。</p></section></main>'''
    (OUT / 'index.html').write_text(shell('学习笔记', home), encoding='utf-8')
    for n in records:
        body = f'<main class="reading"><a class="back" href="/?category={quote(n["category"])}">← 返回 {esc(n["category"])}</a><div class="eyebrow">{esc(n["category"])}</div><h1>{esc(n["title"])}</h1><div class="reading-meta">{n["minutes"]} 分钟阅读 <span>·</span> {esc(n["path"])}</div><div class="article-layout"><article class="prose">{n["body"]}</article><aside class="toc-panel"><div class="nav-label">本页目录</div>{n["toc"]}<a class="to-top" href="#">↑ 回到顶部</a></aside></div></main>'
        target = OUT / 'read' / Path(n['path']).with_suffix('.html')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(shell(n['title'], body, n['category']), encoding='utf-8')
    (OUT / 'search.json').write_text(json.dumps([{k:v for k,v in n.items() if k not in ('body','toc')} for n in records], ensure_ascii=False), encoding='utf-8')
    (OUT / '404.html').write_text(shell('页面未找到', '<main class="reading"><div class="eyebrow">404 / NOT FOUND</div><h1>这页笔记还没有写下。</h1><a href="/">← 返回全部笔记</a></main>'), encoding='utf-8')
    (OUT / '.nojekyll').touch()
    for old, new in {'post/first': '随记/First.md', 'post/jacobi-method': '数值分析/Jacobi Method.md'}.items():
        if Path(new) in known:
            target = OUT / old / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            url = note_url(Path(new))
            target.write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={url}"><title>笔记已迁移</title><a href="{url}">阅读笔记</a></html>', encoding='utf-8')
    print(f'Built {len(records)} notes in {len(categories)} categories → {OUT}')

if __name__ == '__main__': build()
