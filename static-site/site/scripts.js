(function(){
  const btn = document.getElementById('menuBtn');
  const menu = document.getElementById('menu');
  const year = document.getElementById('year');

  if(year) year.textContent = new Date().getFullYear();

  if(btn && menu){
    btn.addEventListener('click', () => {
      const open = menu.getAttribute('data-state') === 'open';
      menu.setAttribute('data-state', open ? 'closed' : 'open');
      btn.setAttribute('aria-expanded', (!open).toString());
    });
  }
})();
