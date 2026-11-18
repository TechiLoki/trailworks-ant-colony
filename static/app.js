'use strict';
const $ = id => document.getElementById(id);
const canvas = $('field'), ctx = canvas.getContext('2d');
let state, running = false, busy = false;
async function request(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  state = result; render();
}
function render() {
  if (!state) return;
  const sx=canvas.width/state.width, sy=canvas.height/state.height;
  ctx.fillStyle='#091213'; ctx.fillRect(0,0,canvas.width,canvas.height);
  if ($('trails').checked) for(let i=0;i<state.home.length;i++) {
    const home=state.home[i], food=state.trail[i];
    if(home+food<0.1) continue;
    ctx.fillStyle=`rgba(${food>home?65:45},${food>home?190:115},${food>home?100:210},${Math.min(.8,Math.log1p(home+food)/6)})`;
    ctx.fillRect((i%state.width)*sx,Math.floor(i/state.width)*sy,sx,sy);
  }
  ctx.fillStyle='#51605a';
  for(const [x,y] of state.walls) ctx.fillRect(x*sx,y*sy,sx,sy);
  for(const [x,y,n] of state.food) {
    ctx.fillStyle='#a8df83';ctx.beginPath();ctx.arc((x+.5)*sx,(y+.5)*sy,7+Math.log1p(n),0,Math.PI*2);ctx.fill();
  }
  ctx.fillStyle='#e6a65b';ctx.beginPath();ctx.arc((state.nest[0]+.5)*sx,(state.nest[1]+.5)*sy,20,0,Math.PI*2);ctx.fill();
  for(const [x,y,carrying] of state.ants) {
    ctx.fillStyle=carrying?'#e2f9a2':'#f3e8ce';ctx.fillRect((x+.5)*sx-1.5,(y+.5)*sy-1.5,3,3);
  }
  for(const key of ['tick','delivered','remaining','carrying']) $(key).textContent=state[key].toLocaleString();
}
async function action(path,data) {
  if(busy) return;
  busy=true; $('error').textContent='';
  try { await request(path,data); }
  catch(error) {running=false; $('error').textContent=error.message;}
  finally {busy=false;updateStatus();}
}
function updateStatus(){ $('play').textContent=running?'Pause':'Run';$('status').textContent=running?'Running':'Paused'; }
$('play').onclick=()=>{running=!running;updateStatus();};
$('step').onclick=()=>{running=false;action('/api/step',{steps:1});};
$('reset').onclick=()=>{running=false;action('/api/reset',{population:Number($('population').value),seed:Number($('seed').value),evaporation:Number($('evaporation').value)});};
$('trails').onchange=render;
canvas.onclick=event=>{
  if(!state) return;
  const box=canvas.getBoundingClientRect();
  action('/api/food',{x:Math.floor((event.clientX-box.left)/box.width*state.width),y:Math.floor((event.clientY-box.top)/box.height*state.height)});
};
async function loop(){if(running&&!busy) await action('/api/step',{steps:Number($('speed').value)});setTimeout(loop,40);}
action('/api/state').then(loop);
