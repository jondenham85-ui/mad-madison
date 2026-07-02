import Sidebar from '@/components/Sidebar'
export default function AppBuilderPage() {
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>🔧 App Builder</h1>
        <div className="glass" style={{padding:'1.5rem'}}>
          <p style={{color:'#64748b'}}>Build custom mini-apps and automations powered by AI.</p>
        </div>
      </main>
    </div>
  )
}
