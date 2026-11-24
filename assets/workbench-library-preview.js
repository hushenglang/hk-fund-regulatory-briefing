(()=>{
  'use strict';
  for(const button of document.querySelectorAll('[data-library-panel]'))button.addEventListener('click',()=>{
    for(const panel of document.querySelectorAll('[data-library-content]'))panel.hidden=panel.id!==button.dataset.libraryPanel;
    for(const peer of document.querySelectorAll('[data-library-panel]'))peer.setAttribute('aria-pressed',String(peer===button));
  });
})();
