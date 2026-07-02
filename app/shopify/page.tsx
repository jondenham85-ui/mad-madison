import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/Sidebar'

export default async function ShopifyPage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')
  let orders = null
  try {
    const res = await fetch(process.env.NEXTAUTH_URL + '/api/shopify', { cache: 'no-store' })
    orders = await res.json()
  } catch(e) {}
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <main style={{flex:1,padding:'2rem'}}>
        <h1 style={{color:'#a78bfa',fontSize:24,fontWeight:700,marginBottom:24}}>🛍️ Shopify Orders</h1>
        <div className="glass" style={{padding:'1.5rem'}}>
          {orders?.data?.orders?.edges?.length ? (
            orders.data.orders.edges.map((e:any) => (
              <div key={e.node.id} style={{padding:'1rem 0',borderBottom:'1px solid #1e1e2e'}}>
                <div style={{color:'#f1f5f9',fontWeight:600}}>{e.node.name}</div>
                <div style={{color:'#64748b',fontSize:13}}>{e.node.displayFinancialStatus} — {e.node.totalPriceSet?.shopMoney?.amount} {e.node.totalPriceSet?.shopMoney?.currencyCode}</div>
              </div>
            ))
          ) : (
            <p style={{color:'#64748b'}}>No orders found or Shopify not connected yet.</p>
          )}
        </div>
      </main>
    </div>
  )
}
