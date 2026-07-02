import { createOrder, captureOrder, getTransactions } from '@/lib/paypal'
import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const { action, amount, orderId } = await req.json()
  try {
    if (action === 'create') {
      const order = await createOrder(amount)
      return NextResponse.json(order)
    }
    if (action === 'capture') {
      const capture = await captureOrder(orderId)
      return NextResponse.json(capture)
    }
    return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
  } catch (e) {
    return NextResponse.json({ error: 'PayPal error' }, { status: 500 })
  }
}

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('.')[0] + 'Z'
  const end = new Date().toISOString().split('.')[0] + 'Z'
  try {
    const data = await getTransactions(start, end)
    return NextResponse.json(data)
  } catch(e) {
    return NextResponse.json({ error: 'Could not fetch transactions' }, { status: 500 })
  }
}
