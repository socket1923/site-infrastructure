(function(){
  const THEME_KEY = 'socket23-theme';
  const choices = ['system', 'dark', 'light'];
  const root = document.documentElement;
  const themeButton = document.getElementById('themeBtn');
  const themeLabel = document.getElementById('themeLabel');
  const media = window.matchMedia('(prefers-color-scheme: light)');

  function activeTheme(preference){
    return preference === 'system' ? (media.matches ? 'light' : 'dark') : preference;
  }

  function applyTheme(preference, persist){
    root.dataset.themePreference = preference;
    root.dataset.theme = activeTheme(preference);
    if(themeLabel) themeLabel.textContent = preference[0].toUpperCase() + preference.slice(1);
    if(themeButton){
      const next = choices[(choices.indexOf(preference) + 1) % choices.length];
      themeButton.setAttribute('aria-label', `Theme: ${preference}. Activate to use ${next}.`);
      themeButton.title = `Theme: ${preference}`;
    }
    if(persist){
      try { localStorage.setItem(THEME_KEY, preference); } catch (_) { /* Preference storage is optional. */ }
    }
  }

  applyTheme(root.dataset.themePreference || 'system', false);
  if(themeButton){
    themeButton.addEventListener('click', () => {
      const current = root.dataset.themePreference || 'system';
      applyTheme(choices[(choices.indexOf(current) + 1) % choices.length], true);
    });
  }
  media.addEventListener('change', () => {
    if((root.dataset.themePreference || 'system') === 'system') applyTheme('system', false);
  });

  const btn = document.getElementById('menuBtn');
  const menu = document.getElementById('menu');
  const year = document.getElementById('year');
  if(year) year.textContent = new Date().getFullYear();

  if(menu){
    const path = window.location.pathname === '/' ? '/' : window.location.pathname;
    const currentPath = path.startsWith('/work/') ? '/projects.html' : path;
    for(const link of menu.querySelectorAll('a')){
      if(link.getAttribute('href') === currentPath) link.setAttribute('aria-current', 'page');
    }
  }

  function closeMenu(){
    if(btn && menu){
      menu.setAttribute('data-state', 'closed');
      btn.setAttribute('aria-expanded', 'false');
    }
  }

  if(btn && menu){
    btn.addEventListener('click', () => {
      const open = menu.getAttribute('data-state') === 'open';
      menu.setAttribute('data-state', open ? 'closed' : 'open');
      btn.setAttribute('aria-expanded', (!open).toString());
    });
    menu.addEventListener('click', event => {
      if(event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', event => {
      if(event.key === 'Escape') closeMenu();
    });
  }

  const filterButtons = Array.from(document.querySelectorAll('[data-project-filter]'));
  const projectCards = Array.from(document.querySelectorAll('[data-project-category]'));
  const filterStatus = document.getElementById('filterStatus');
  if(filterButtons.length && projectCards.length){
    for(const filterButton of filterButtons){
      filterButton.addEventListener('click', () => {
        const filter = filterButton.dataset.projectFilter || 'all';
        let visible = 0;
        for(const card of projectCards){
          const categories = (card.dataset.projectCategory || '').split(' ');
          const show = filter === 'all' || categories.includes(filter);
          card.hidden = !show;
          if(show) visible += 1;
        }
        for(const candidate of filterButtons){
          candidate.setAttribute('aria-pressed', (candidate === filterButton).toString());
        }
        if(filterStatus) filterStatus.textContent = `${visible} project${visible === 1 ? '' : 's'} shown`;
      });
    }
  }
})();
