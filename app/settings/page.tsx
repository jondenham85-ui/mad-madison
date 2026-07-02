import Sidebar from '@/components/Sidebar'
export default function SettingsPage() {
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>⚙️ Settings</h1>
        <div className="glass" style={{padding:'1.5rem',marginBottom:20}}>
          <h2 style={{color:'#e2e8f0',marginBottom:16,fontSize:16}}>Environment Configuration</h2>
          <p style={{color:'#64748b',fontSize:14}}>Configure your API keys and environment variables in your Railway dashboard.</p>
        </div>
        <div className="glass" style={{padding:'1.5rem'}}>
          <h2 style={{color:'#e2e8f0',marginBottom:16,fontSize:16}}>PayPal</h2>
          <p style={{color:'#64748b',fontSize:14}}>PayPal webhooks endpoint: /api/paypal/webhook</p>
        </div>
      </main>
    </div>
  )
}
