document.addEventListener('DOMContentLoaded',function(){
  var b=document.querySelector('.menu-btn'),n=document.getElementById('nav-links');
  if(b&&n){b.addEventListener('click',function(){
    var open=b.getAttribute('aria-expanded')==='true';
    b.setAttribute('aria-expanded',open?'false':'true');n.classList.toggle('open',open?false:true);});}
});
