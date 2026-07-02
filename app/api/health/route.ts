import { NextResponse } from 'next/server'
export async function GET() {
  return NextResponse.json({ status: 'ok', app: 'mad-madison', ts: new Date().toISOString() })
}
