document.addEventListener('DOMContentLoaded',function(){
  var b=document.querySelector('.menu-btn'),n=document.getElementById('nav-links');
  if(b&&n){b.addEventListener('click',function(){
    var open=b.getAttribute('aria-expanded')==='true';
    b.setAttribute('aria-expanded',open?'false':'true');n.classList.toggle('open',open?false:true);});}
});
document.addEventListener('DOMContentLoaded',function(){
  var K='f4p-consent';
  function apply(v){var s=v==='granted'?'granted':'denied';
    if(typeof gtag==='function'){gtag('consent','update',{'ad_storage':s,'ad_user_data':s,'ad_personalization':s,'analytics_storage':s});}}
  function show(){
    if(document.querySelector('.consent-bar')){return;}
    var d=document.createElement('div');d.className='consent-bar';d.setAttribute('role','region');d.setAttribute('aria-label','Cookie choice');
    d.innerHTML='<p>Flo 4 Paws uses Google Analytics and Google Ads cookies to see how this site is used and whether adverts bring people here. Nothing is stored until you choose. <a href="/cookie-policy/">Cookie policy</a></p>'
      +'<div class="consent-actions"><button type="button" class="btn line" data-c="denied">Decline</button><button type="button" class="btn mint" data-c="granted">Accept</button></div>';
    d.addEventListener('click',function(e){var b=e.target.closest('button[data-c]');if(!b){return;}
      var v=b.getAttribute('data-c');try{localStorage.setItem(K,v);}catch(x){}apply(v);d.remove();});
    document.body.appendChild(d);}
  var v=null;try{v=localStorage.getItem(K);}catch(x){}
  if(v!=='granted'&&v!=='denied'){show();}
  var r=document.getElementById('consent-reset');
  if(r){r.addEventListener('click',function(){try{localStorage.removeItem(K);}catch(x){}apply('denied');show();});}
  var f=document.querySelector('a[href="https://app.flo4paws.co.uk/intake-form/flo4paws/"]');
  if(f){f.addEventListener('click',function(){if(typeof gtag==='function'){gtag('event','intake_form_start');}});}
});
