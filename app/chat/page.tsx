"use client"
import { useState } from 'react'
import Sidebar from '@/components/Sidebar'

export default function ChatPage() {
  const [messages, setMessages] = useState<{role:string,content:string}[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function send() {
    if (!input.trim()) return
    const newMsgs = [...messages, {role:'user',content:input}]
    setMessages(newMsgs)
    setInput('')
    setLoading(true)
    const res = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({messages:newMsgs}) })
    const data = await res.json()
    setMessages([...newMsgs, {role:'assistant',content:data.content}])
    setLoading(false)
  }

  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem',display:'flex',flexDirection:'column'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>🤖 AI Chat (GPT-4o)</h1>
        <div className="glass" style={{flex:1,padding:'1.5rem',overflowY:'auto',marginBottom:16,minHeight:400}}>
          {messages.map((m,i) => (
            <div key={i} style={{marginBottom:16,textAlign:m.role==='user'?'right':'left'}}>
              <span style={{
                display:'inline-block',padding:'0.6rem 1rem',borderRadius:12,maxWidth:'75%',
                background:m.role==='user'?'#7c3aed':'#1e1e2e',color:'#f1f5f9',fontSize:14
              }}>{m.content}</span>
            </div>
          ))}
          {loading && <div style={{color:'#a78bfa',fontSize:14}}>Madison is thinking...</div>}
        </div>
        <div style={{display:'flex',gap:12}}>
          <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()}
            placeholder="Ask Madison anything..."
            style={{flex:1,padding:'0.75rem 1rem',borderRadius:10,border:'1px solid #1e1e2e',background:'#13131a',color:'#f1f5f9',fontSize:14}} />
          <button onClick={send} style={{padding:'0.75rem 1.5rem',borderRadius:10,background:'#7c3aed',color:'#fff',fontWeight:600,border:'none',cursor:'pointer'}}>Send</button>
        </div>
      </main>
    </div>
  )
}
