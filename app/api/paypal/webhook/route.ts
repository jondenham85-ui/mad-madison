import { NextRequest, NextResponse } from 'next/server'
export async function POST(req: NextRequest) {
  const body = await req.json()
  const eventType = body.event_type
  console.log('[PayPal Webhook]', eventType)
  if (eventType === 'PAYMENT.CAPTURE-COMPLETED') {
    console.log('[PayPal] Payment captured:', body.resource?.id)
  }
  return NextResponse.json({ received: true })
}
