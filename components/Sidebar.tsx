"use client"
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/chat', label: 'AI Chat', icon: '🤖' },
  { href: '/shopify', label: 'Shopify', icon: '🛍️' },
  { href: '/youtube', label: 'YouTube', icon: '📺' },
  { href: '/social', label: 'Social', icon: '📣' },
  { href: '/ads', label: 'Ads', icon: '📢' },
  { href: '/app-builder', label: 'App Builder', icon: '🔧' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { data: session } = useSession()
  return (
    <aside style={{width:220,minHeight:'100vh',background:'#13131a',borderRight:'1px solid #1e1e2e',display:'flex',flexDirection:'column',padding:'1.5rem 0'}}>
      <div style={{padding:'0 1.5rem 2rem',borderBottom:'1px solid #1e1e2e'}}>
        <div style={{fontSize:28}}>🤠</div>
        <div style={{color:'#a78bfa',fontWeight:700,fontSize:16}}>Mad Madison</div>
        <div style={{color:'#64748b',fontSize:12,marginTop:4}}>{session?.user?.email}</div>
      </div>
      <nav style={{flex:1,padding:'1rem 0'}}>
        {nav.map(item => (
          <Link key={item.href} href={item.href} style={{
            display:'flex',alignItems:'center',gap:10,padding:'0.65rem 1.5rem',
            color: pathname===item.href ? '#a78bfa' : '#94a3b8',
            background: pathname===item.href ? 'rgba(167,139,250,0.1)' : 'transparent',
            textDecoration:'none',fontSize:14,fontWeight: pathname===item.href ? 600 : 400,
            borderLeft: pathname===item.href ? '3px solid #a78bfa' : '3px solid transparent',
          }}>
            <span>{item.icon}</span>{item.label}
          </Link>
        ))}
      </nav>
      <div style={{padding:'1rem 1.5rem',borderTop:'1px solid #1e1e2e'}}>
        <button onClick={() => signOut({ callbackUrl: '/login' })} style={{
          width:'100%',padding:'0.5rem',borderRadius:8,border:'1px solid #1e1e2e',
          background:'transparent',color:'#64748b',cursor:'pointer',fontSize:13
        }}>Sign Out</button>
      </div>
    </aside>
  )
}
