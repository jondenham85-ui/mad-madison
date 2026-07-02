import { getOrders } from '@/lib/shopify'
import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  try {
    const orders = await getOrders(20)
    return NextResponse.json(orders)
  } catch (e) {
    return NextResponse.json({ error: 'Shopify not configured' }, { status: 500 })
  }
}
