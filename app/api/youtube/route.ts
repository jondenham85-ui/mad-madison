import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const apiKey = process.env.YOUTUBE_API_KEY
  if (!apiKey) return NextResponse.json({ error: 'YouTube API key not set' }, { status: 500 })
  const res = await fetch('https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true&key=' + apiKey)
  const data = await res.json()
  return NextResponse.json(data)
}
