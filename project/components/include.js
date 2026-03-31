async function include(selector, file){
  const el=document.querySelector(selector);
  if(!el) return;
  const html=await fetch(file).then(r=>r.text());
  el.innerHTML=html;
}
include('#header','../components/header.html');
include('#footer','../components/footer.html');
