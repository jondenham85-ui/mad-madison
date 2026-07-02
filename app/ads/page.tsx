import Sidebar from '@/components/Sidebar'
export default function AdsPage() {
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>📢 Ad Campaigns</h1>
        <div className="glass" style={{padding:'1.5rem'}}>
          <p style={{color:'#64748b'}}>Generate and manage ad campaigns with AI assistance here.</p>
        </div>
      </main>
    </div>
  )
}
