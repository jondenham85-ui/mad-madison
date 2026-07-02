import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/Sidebar'

export default async function YoutubePage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>📺 YouTube Analytics</h1>
        <div className="glass" style={{padding:'1.5rem'}}>
          <p style={{color:'#64748b'}}>Connect your YouTube API key in settings to see analytics here.</p>
        </div>
      </main>
    </div>
  )
}
