(function(){
  document.documentElement.classList.add('js');
  const key = 'socket23-theme';
  let preference = 'system';
  try {
    const saved = localStorage.getItem(key);
    if (saved === 'dark' || saved === 'light' || saved === 'system') preference = saved;
  } catch (_) {
    preference = 'system';
  }
  const active = preference === 'system'
    ? (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')
    : preference;
  document.documentElement.dataset.theme = active;
  document.documentElement.dataset.themePreference = preference;
})();
