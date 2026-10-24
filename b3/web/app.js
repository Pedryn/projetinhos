const api = (path, opts)=>fetch(path, opts).then(r=>r.json()).catch(e=>{console.error(e);return{error:'network'}})
let currentUser = null

async function loadTickers(){
  const q = document.getElementById('input-search').value
  const sort = document.getElementById('select-sort').value
  const res = await api(`/api/tickers?q=${encodeURIComponent(q)}&sort=${encodeURIComponent(sort)}`)
  const tbody = document.querySelector('#tbl-tickers tbody')
  tbody.innerHTML = ''
  if(res.tickers){
    res.tickers.forEach(t=>{
      const tr = document.createElement('tr')
      tr.innerHTML = `
        <td>${t.ticker}</td>
        <td>${t.name}</td>
        <td class="${(t.change||0)>=0?'green':'red'}">${(t.close==null)?'—':`R$ ${t.close.toFixed(2)}`}</td>
      `
      tbody.appendChild(tr)
      tr.addEventListener('dblclick', ()=>showDetail(t.ticker))
    })
  }
}

async function showDetail(ticker){
  const res = await api(`/api/ticker/${ticker}`)
  const info = res.info || {}
  const modal = document.getElementById('modal')
  const title = document.getElementById('modal-title')
  const body = document.getElementById('modal-body')
  title.textContent = `${ticker}`

  const price = (info.currentPrice ?? info.regularMarketPrice ?? info.previousClose) || null
  const changePct = (info.regularMarketChangePercent ?? info.changePercent ?? info.regularMarketChange) || null
  const marketCap = info.marketCap || null
  const volume = info.volume || null
  const name = info.longName || info.shortName || info.short_name || ticker
  const summary = info.longBusinessSummary || info.description || ''

  const priceHtml = price !== null
    ? `<span class="${(changePct||0) >= 0 ? 'green' : 'red'}">R$ ${Number(price).toFixed(2)}</span>`
    : '—'

  body.innerHTML = `
    <div><strong>${name}</strong></div>
    <div><strong>Preço:</strong> ${priceHtml}</div>
    <div><strong>Variação (%):</strong> ${changePct!=null ? `${Number(changePct).toFixed(2)}%` : '—'}</div>
    <div><strong>Market cap:</strong> ${marketCap!=null ? Number(marketCap).toLocaleString() : '—'}</div>
    <div><strong>Volume:</strong> ${volume!=null ? Number(volume).toLocaleString() : '—'}</div>
    <div style="margin-top:8px"><strong>Resumo:</strong></div>
    <div style="max-height:200px;overflow:auto;font-size:13px;margin-top:6px">${summary || '<em>Não disponível</em>'}</div>
  `
  document.getElementById('modal-close').onclick = closeModal
  modal.style.display = 'flex'
}

function closeModal(){
  const modal = document.getElementById('modal')
  modal.style.animation = 'fadeOut 0.3s ease'
  setTimeout(()=>{
    modal.style.display='none'
    modal.style.animation = 'fadeIn 0.3s ease'
  },280)
}

/* === LOGIN / REGISTRO === */
document.getElementById('btn-login').addEventListener('click', ()=>openModal('login'))

async function openModal(type){
  const modal = document.getElementById('modal')
  const body = document.getElementById('modal-body')
  const title = document.getElementById('modal-title')
  title.textContent = (type=='login')?'Login':'Registrar'
  body.innerHTML = ''
  if(type=='login'){
    body.innerHTML = `
      <input id='m-email' placeholder='Email'>
      <input id='m-senha' placeholder='Senha' type='password'>
      <button id='m-login-btn' class='btn-primary'>Entrar</button>
      <button id='m-go-reg' class='btn-secondary'>Registrar</button>`
    document.getElementById('m-login-btn').addEventListener('click', async ()=>{
      const email = document.getElementById('m-email').value
      const senha = document.getElementById('m-senha').value
      const res = await api('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,senha})})
      if(res.error){alert('Erro de rede')}
      else if(res.id){currentUser = res;updateUserUI();closeModal()}
      else alert('Credenciais inválidas')
    })
    document.getElementById('m-go-reg').addEventListener('click', ()=>openModal('register'))
  } else {
    body.innerHTML = `
      <input id='r-nome' placeholder='Nome'>
      <input id='r-email' placeholder='Email'>
      <input id='r-senha' placeholder='Senha' type='password'>
      <button id='r-reg-btn' class='btn-primary'>Registrar</button>`
    document.getElementById('r-reg-btn').addEventListener('click', async ()=>{
      const nome=document.getElementById('r-nome').value
      const email=document.getElementById('r-email').value
      const senha=document.getElementById('r-senha').value
      const res=await api('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome,email,senha})})
      if(res.error){alert('Erro de rede')}
      else if(res.ok){alert('Registrado! Faça login'); openModal('login')}
      else alert('Erro')
    })
  }
  document.getElementById('modal-close').onclick = closeModal
  modal.style.display='flex'
}

/* === USUÁRIO === */
function updateUserUI(){
  const info=document.getElementById('user-info')
  const btnLogin=document.getElementById('btn-login')
  const btnLogout=document.getElementById('btn-logout')
  const btnMeus=document.getElementById('btn-meus-ativos')
  if(currentUser){
    info.textContent=`${currentUser.nome} (${currentUser.email})`
    btnLogin.style.display='none'
    btnLogout.style.display='inline'
    btnMeus.style.display='inline'
  }else{
    info.textContent='(não logado)'
    btnLogin.style.display='inline'
    btnLogout.style.display='none'
    btnMeus.style.display='none'
  }
}
document.getElementById('btn-logout').addEventListener('click', ()=>{currentUser=null;updateUserUI()})

/* === MEUS ATIVOS === */
document.getElementById('btn-meus-ativos').addEventListener('click', ()=>{
  document.getElementById('meus-ativos').style.display='flex'
  loadMeus()
})
document.getElementById('ma-close').addEventListener('click', ()=>{document.getElementById('meus-ativos').style.display='none'})

async function loadMeus(){
  if(!currentUser) return
  const res=await api(`/api/portfolio/${currentUser.id}`)
  const tbody=document.querySelector('#tbl-meus tbody')
  tbody.innerHTML=''
  if(res.positions){
    res.positions.forEach(p=>{
      const tr=document.createElement('tr')
      tr.innerHTML=`<td>${p.id}</td><td>${p.ticker}</td><td>${p.quantidade}</td><td>${p.preco_medio}</td><td><button data-id='${p.id}' class='btn-secondary ma-del'>Remover</button></td>`
      tbody.appendChild(tr)
    })
    document.querySelectorAll('.ma-del').forEach(b=>b.addEventListener('click',async(ev)=>{
      const id=ev.target.dataset.id
      await fetch(`/api/portfolio/${currentUser.id}/${id}`,{method:'DELETE'})
      loadMeus()
    }))
  }
}

document.getElementById('ma-add').addEventListener('click',async()=>{
  if(!currentUser){alert('Faça login');return}
  const t=document.getElementById('ma-ticker').value
  const q=document.getElementById('ma-quantidade').value
  const p=document.getElementById('ma-preco').value
  const res=await api(`/api/portfolio/${currentUser.id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker:t,quantidade:q,preco_medio:p})})
  if(res.ok){
    document.getElementById('ma-ticker').value=''
    document.getElementById('ma-quantidade').value=''
    document.getElementById('ma-preco').value=''
    loadMeus()
  }else alert('Erro')
})

/* === INIT === */
loadTickers()
updateUserUI()
