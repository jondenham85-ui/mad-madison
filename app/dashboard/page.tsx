import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/Sidebar'

export default async function Dashboard() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:28,fontWeight:700,marginBottom:8}}>Revenue Dashboard</h1>
        <p style={{color:'#64748b',marginBottom:32}}>Welcome back, {session.user?.name}! 🤠</p>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:20}}>
          {[
            {label:'Total Revenue',value:'$0.00',icon:'💰'},
            {label:'PayPal Balance', value: '$0.00',icon:'💳'},
            {label:'Shopify Orders', value:'0',icon:'🛍️'},
            {label:'YouTube Views', value:'0',icon:'📺'},
          ].map(card => (
            <div key={card.label} className="glass" style={{padding:'1.5rem'}}>
              <div style={{fontSize:32,marginBottom:8}}>{card.icon}</div>
              <div style={{color:'#64748b',fontSize:13}}>{card.label}</div>
              <div style={{color:'#f1f5f9',fontSize:26,fontWeight:700,marginTop:4}}>{card.value}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
