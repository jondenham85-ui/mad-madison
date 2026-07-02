"use client"
import { signIn } from 'next-auth/react'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{background:'#0a0a0f'}}>
      <div className="glass p-10 text-center max-w-sm w-full">
        <div className="text-5xl mb-4">🤠</div>
        <h1 className="text-2xl font-bold text-purple-300 mb-2">Mad Madison</h1>
        <p className="text-slate-400 mb-8">Owner-only access</p>
        <button
          onClick={() => signIn('google', { callbackUrl: '/dashboard' })}
          className="w-full py-3 px-6 rounded-xl font-semibold text-white"
          style={{background:'linear-gradient(135deg,#7c3aed,#a78bfa)'}}
        >
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
