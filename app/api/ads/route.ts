import { openai } from '@/lib/openai'
import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const { product, audience, budget, platform } = await req.json()
  const prompt = 'Create a compelling ad campaign for: Product: ' + product + ', Target audience: ' + audience + ', Budget: ' + budget + ', Platform: ' + platform + '. Include: headline, body copy, call to action, and targeting suggestions.'
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 800,
  })
  return NextResponse.json({ campaign: completion.choices[0].message.content })
}
