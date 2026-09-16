from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import markdown
from scripts import build, import_notes


class NotebookTests(unittest.TestCase):
    def render(self, source):
        return markdown.markdown(source, extensions=['extra', build.MathExtension()])

    def test_math_and_code(self):
        rendered = self.render('行内 $x_i^2$\n\n$$\n\\frac{1}{2}\n$$\n\n```latex\n$$x$$\n```\n\n`$y$`')
        self.assertEqual(rendered.count('class="math"'), 2)
        self.assertIn('data-display="true"', rendered)
        self.assertIn('\\frac{1}{2}', rendered)
        self.assertIn('$$x$$', rendered)
        self.assertIn('<code>$y$</code>', rendered)

    def test_nested_unicode_links_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / '数学/线性代数'
            folder.mkdir(parents=True)
            source = folder / '笔记.md'
            source.touch()
            (folder / '图 1.svg').touch()
            with patch.object(build, 'NOTES', root):
                links = build.Links(source, {source.relative_to(root)})
                self.assertTrue(links.resolve('图%201.svg').startswith('/content/'))
                self.assertTrue(links.resolve('笔记.md#公式').startswith('/read/'))
                with self.assertRaises(ValueError): links.resolve('missing.png')
                with self.assertRaises(ValueError): links.resolve('../../../outside.png')
                with self.assertRaises(ValueError): links.resolve('C:/images/a.png')

    def test_import_absolute_image_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'incoming'
            source.mkdir()
            image = root / 'outside.png'
            image.write_bytes(b'image fixture')
            (source / '笔记.md').write_text(f'# 标题\n\n![图]({image.as_posix()})', encoding='utf-8')
            repository = root / 'repo'
            with patch.object(import_notes, 'ROOT', repository):
                import_notes.import_folder(source, '数学')
                result = repository / 'notes/数学/笔记.md'
                self.assertIn('/_attachments/', result.read_text(encoding='utf-8'))
                self.assertEqual(len(list((repository / 'notes/_attachments').iterdir())), 1)
                with self.assertRaises(ValueError): import_notes.import_folder(source, '数学')

    def test_complete_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notes = root / 'notes'
            (notes / '数学/深入').mkdir(parents=True)
            (notes / '数学/深入/标题.md').write_text('---\ntitle: 自定义标题\n---\n# 标题\n\n$$x^2$$', encoding='utf-8')
            with patch.object(build, 'NOTES', notes), patch.object(build, 'OUT', root / 'dist'):
                build.build()
            self.assertIn('自定义标题', (root / 'dist/index.html').read_text(encoding='utf-8'))
            self.assertTrue((root / 'dist/read/数学/深入/标题.html').exists())
            self.assertIn('数学/深入', (root / 'dist/search.json').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
