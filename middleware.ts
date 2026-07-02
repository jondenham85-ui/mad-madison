import { withAuth } from 'next-auth/middleware'
import { NextResponse } from 'next/server'
export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token
    const ownerEmails = (process.env.OWNER_EMAILS || '').split(',').map(e => e.trim())
    if (!token?.email || !ownerEmails.includes(token.email)) {
      return NextResponse.redirect(new URL('/login', req.url))
    }
    return NextResponse.next()
  },
  { callbacks: { authorized: ({ token }) => !!token } }
)
export const config = { matcher: ['/dashboard/:path*','/chat/:path*','/shopify/:path*','/youtube/:path*','/social/:path*','/ads/:path*','/app-builder/:path*','/settings/:path*'] }
