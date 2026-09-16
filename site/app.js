(() => {
  const root = document.documentElement;
  let saved;
  try { saved = localStorage.getItem('notebook-theme'); } catch {}
  root.dataset.theme = saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const theme = document.querySelector('#theme');
  const updateTheme = () => theme.setAttribute('aria-label', root.dataset.theme === 'dark' ? '切换浅色模式' : '切换深色模式');
  updateTheme();
  theme.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('notebook-theme', root.dataset.theme); } catch {}
    updateTheme();
  });
  window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.math').forEach(el => {
      if (window.katex) window.katex.render(el.textContent, el, {displayMode: el.dataset.display === 'true', throwOnError: false, trust: false});
    });
  });
  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.className = 'copy-code'; button.textContent = '复制';
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); button.textContent = '已复制'; }
      catch { button.textContent = '请手动复制'; }
      setTimeout(() => { button.textContent = '复制'; }, 1800);
    });
    pre.append(button);
  });
  const search = document.querySelector('#search');
  if (!search) return;
  let category = new URLSearchParams(location.search).get('category') || '';
  const buttons = [...document.querySelectorAll('[data-category]')];
  if (!buttons.some(b => b.dataset.category === category)) category = '';
  let records;
  const grid = document.querySelector('#notes-grid');
  const cards = [...grid.children];
  function filter() {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    cards.forEach((card, i) => {
      const entry = records?.[i];
      const cat = entry?.category ?? card.querySelector('.card-category').textContent;
      const text = entry ? entry.title + ' ' + entry.text : card.textContent;
      card.hidden = Boolean((category && cat !== category) || (query && !text.toLocaleLowerCase().includes(query)));
      if (!card.hidden) count++;
    });
    buttons.forEach(button => {
      const selected = button.dataset.category === category;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', selected);
    });
    document.querySelector('#collection-title').textContent = category || '全部笔记';
    document.querySelector('#empty').hidden = count !== 0;
    document.querySelectorAll('.folder').forEach(a => a.classList.toggle('active', new URL(a.href).searchParams.get('category') === category));
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.category;
    history.replaceState(null, '', category ? '/?category=' + encodeURIComponent(category) : '/');
    filter();
  }));
  search.addEventListener('input', filter);
  document.addEventListener('keydown', e => {
    if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) { e.preventDefault(); search.focus(); }
    if (e.key === 'Escape') { search.value = ''; search.blur(); filter(); }
  });
  filter();
  fetch('/search.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(data => {records = data; filter();}).catch(() => { search.placeholder = '搜索标题或摘要…'; });
})();
