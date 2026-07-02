import { openai } from '@/lib/openai'
import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const { messages } = await req.json()
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: 'You are Madison, a sharp and savvy AI business assistant for Jon and Ally Denham. Help them grow revenue, manage their Shopify store, analyze YouTube performance, and make smart business decisions. Be concise, direct, and action-oriented.' },
      ...messages
    ],
    max_tokens: 1024,
  })
  return NextResponse.json({ content: completion.choices[0].message.content })
}
