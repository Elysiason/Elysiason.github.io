"""Import a folder and make absolute local image paths portable."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

def import_folder(source, category):
    source = Path(source).resolve()
    notes = (ROOT / 'notes').resolve()
    destination = (notes / category).resolve()
    if not source.is_dir():
        raise ValueError(f'找不到源目录: {source}')
    if not destination.is_relative_to(notes) or destination == notes:
        raise ValueError('分类必须是 notes 内的子文件夹名称')
    if destination.is_relative_to(source) or source.is_relative_to(notes):
        raise ValueError('请选择仓库 notes 之外的源目录')
    files = [p for p in source.rglob('*') if p.is_file() and not any(x.startswith('.') for x in p.relative_to(source).parts)]
    conflicts = [destination / p.relative_to(source) for p in files if (destination / p.relative_to(source)).exists()]
    if conflicts:
        raise ValueError(f'为避免覆盖已有笔记，请使用新的分类名称。已存在: {conflicts[0]}')
    pending = []
    attachments = {}
    for file in files:
        target = destination / file.relative_to(source)
        if file.suffix.lower() != '.md':
            pending.append((target, file.read_bytes()))
            continue
        def rewrite(match):
            value = match.group('path').strip('<>')
            decoded = unquote(value).replace('\\', '/')
            if decoded.startswith('file:'):
                decoded = urlsplit(decoded).path
                if re.match(r'^/[A-Za-z]:/', decoded):
                    decoded = decoded[1:]
            elif urlsplit(decoded).scheme and not re.match(r'^[A-Za-z]:/', decoded):
                return match.group(0)
            local = Path(decoded)
            local = local if local.is_absolute() else file.parent / local
            local = local.resolve()
            if local.is_relative_to(source) and not Path(decoded).is_absolute():
                return match.group(0)
            if not local.is_file():
                raise ValueError(f'{file}: 找不到图片 {value}')
            # Images outside the note tree become content-addressed attachments.
            data = local.read_bytes()
            name = hashlib.sha256(data).hexdigest()[:20] + local.suffix.lower()
            attachments[name] = data
            return match.group(0).replace(match.group('path'), '/_attachments/' + name)
        raw = file.read_text(encoding='utf-8-sig')
        # Keep fenced code examples unchanged.
        parts = re.split(r'(^\s*```[^\n]*\n[\s\S]*?^\s*```\s*$|^\s*~~~[^\n]*\n[\s\S]*?^\s*~~~\s*$)', raw, flags=re.M)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r'!\[[^\]]*\]\(\s*(?P<path><[^>]+>|[^\n)]+?)(?:\s+"[^"]*")?\s*\)', rewrite, parts[i])
            parts[i] = re.sub(r'<img\b[^>]*?\bsrc=[\"\'](?P<path>[^\"\']+)[\"\'][^>]*>', rewrite, parts[i], flags=re.I)
        pending.append((target, ''.join(parts).encode('utf-8')))
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for name, data in attachments.items():
        target = notes / '_attachments' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f'已导入 {len(files)} 个文件到 {destination}；转存 {len(attachments)} 张外部图片。')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='原始笔记文件夹')
    parser.add_argument('--category', required=True, help='导入后的分类名称')
    args = parser.parse_args()
    import_folder(args.source, args.category)
