import { AuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
const ownerEmails = (process.env.OWNER_EMAILS || '').split(',').map(e => e.trim())
export const authOptions: AuthOptions = {
  providers: [GoogleProvider({ clientId: process.env.GOOGLE_CLIENT_ID!, clientSecret: process.env.GOOGLE_CLIENT_SECRET! })],
  callbacks: {
    async signIn({ user }) { return ownerEmails.includes(user.email || '') },
    async session({ session }) { return session },
  },
  pages: { signIn: '/login', error: '/login' },
}
