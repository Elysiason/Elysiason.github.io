# Elysiason · 学习笔记

一个直接从普通 Markdown 文件夹生成的静态笔记网站。简洁文章列表、深色模式、手机阅读、全文搜索、自动分类、文章目录，以及离线打包的 KaTeX 公式支持。

## 日常使用

1. 把 Markdown 笔记及其图片复制到 `notes/分类名称/`。多层文件夹会显示为 `数学/线性代数` 这样的分类；根目录笔记归入“未分类”。
2. 图片使用相对路径，如 `![图](images/示意图.png)`；Markdown 笔记之间也可以使用相对链接。中文和空格文件名受支持。
3. 提交并推送到 `main`，GitHub Actions 自动构建并发布到 https://elysiason.github.io/。

不要求 front matter；标题取 `# 一级标题`，否则取文件名。已有 YAML front matter 可以保留，支持 `title`。所有非隐藏 Markdown 都会公开发布，草稿请留在 `notes/` 之外。隐藏文件不会被打包。

数学公式直接写 `$x^2$` 或 `$$...$$`，也支持 `\(...\)` 和 `\[...\]`。代码块内的美元符号会保持原样。公式库和字体随站点打包，不需要 CDN。

## 一次性设置 GitHub Pages

在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。然后推送 `main`，或在 Actions 中手动运行 **Publish notebook**。工作流只上传 `dist/`，根目录旧 Hugo 产物不再参与发布。

## 本地预览

需要 Python 3.12 或更新版本。在仓库目录运行：

```powershell
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/serve.py
```

打开 http://localhost:8000 。修改笔记后重新执行构建，再刷新网页。不要双击 `dist/index.html`，站点需要 HTTP 服务才能正确加载根路径资源与搜索。

Windows 也可以双击 `preview.cmd`。预览服务固定了 SVG 等资源的 MIME 类型，避免 Windows 文件关联导致图片无法显示。

## 导入电脑上的笔记

如果图片使用本地绝对路径，或者放在原笔记目录外，先执行：

```powershell
python scripts/import_notes.py "D:\我的学习笔记" --category "课程笔记"
python scripts/build.py
```

原始文件不会改动。工具复制目录，并把 Markdown 图片和 HTML `<img src>` 中的外部本地图片转存到 `notes/_attachments/`。为避免覆盖，目标分类里已有同名文件时会停止。建议日常直接编辑导入后的 `notes/`，使用相对路径。引用式图片、Obsidian `![[...]]` 和编辑器私有语法请先转换为标准 Markdown；不承诺兼容全部编辑器扩展。

找不到图片或笔记链接时，构建会报出源文件及路径，避免发布后才发现图片丢失。网页图片 URL 会保留原样，是否可访问取决于原网站。

## 维护

- `notes/`：你日常维护的笔记和图片。
- `scripts/build.py`：Markdown 转换、路径校验、分类和搜索索引。
- `site/`：页面样式与交互。
- `.github/workflows/pages.yml`：自动构建和部署。
- `python -m unittest discover -s tests`：公式、路径、导入和构建回归检查。

原有 First、Jacobi Method 已迁移到 Markdown，旧文章 URL 自动跳转。原文内容保留，没有替作者修改学术论述。
