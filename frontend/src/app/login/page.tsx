'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence, type TargetAndTransition } from 'framer-motion'
import { Eye, EyeOff, Zap, Loader2 } from 'lucide-react'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useAuth } from '@/providers/AuthProvider'
import { APP_NAME } from '@/lib/brand'
import { cn } from '@/lib/utils/cn'

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.15 } },
}

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] } },
}

function AnimatedBlob({
  className,
  animate,
}: {
  className: string
  animate: TargetAndTransition
}) {
  return (
    <motion.div
      className={cn('pointer-events-none absolute rounded-full blur-3xl', className)}
      animate={animate}
      transition={{ duration: 12, repeat: Infinity, repeatType: 'mirror', ease: 'easeInOut' }}
    />
  )
}

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading, isAuthenticated } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [focused, setFocused] = useState<'email' | 'password' | null>(null)

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace('/dashboard')
    }
  }, [authLoading, isAuthenticated, router])

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-3"
        >
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-xs text-zinc-500">Loading workspace…</p>
        </motion.div>
      </div>
    )
  }

  if (isAuthenticated) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email.trim(), password)
    } catch {
      setError('Invalid email or password')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-zinc-50 px-4 dark:bg-zinc-950">
      {/* Subtle grid */}
      <div
        className={cn(
          'pointer-events-none absolute inset-0 bg-[size:48px_48px]',
          'bg-[linear-gradient(to_right,#80808014_1px,transparent_1px),linear-gradient(to_bottom,#80808014_1px,transparent_1px)]',
          'dark:bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)]',
        )}
      />

      {/* Animated ambient blobs */}
      <AnimatedBlob
        className="-left-40 -top-40 h-[480px] w-[480px] bg-purple-300/50 dark:bg-purple-600/25"
        animate={{ x: [0, 30, 0], y: [0, 20, 0], scale: [1, 1.08, 1] }}
      />
      <AnimatedBlob
        className="-bottom-40 -right-40 h-[520px] w-[520px] bg-blue-300/40 dark:bg-blue-600/20"
        animate={{ x: [0, -25, 0], y: [0, -30, 0], scale: [1, 1.1, 1] }}
      />
      <AnimatedBlob
        className="left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 bg-teal-300/30 dark:bg-teal-500/10"
        animate={{ scale: [1, 1.2, 1], opacity: [0.4, 0.7, 0.4] }}
      />

      {/* Theme toggle */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="absolute right-6 top-6 z-10"
      >
        <ThemeToggle />
      </motion.div>

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, y: 32, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Outer glow */}
        <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-blue-500/10 via-purple-500/5 to-transparent blur-sm dark:from-blue-500/20 dark:via-purple-500/10" />

        <div className="relative overflow-hidden rounded-2xl border border-zinc-200 bg-white/95 shadow-xl shadow-zinc-200/50 backdrop-blur-xl dark:border-zinc-800/80 dark:bg-zinc-900/90 dark:shadow-2xl dark:shadow-black/40">
          {/* Shimmer gradient top bar */}
          <div className="relative h-1 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 via-blue-500 to-teal-400" />
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
              animate={{ x: ['-100%', '200%'] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: 'linear', repeatDelay: 1 }}
            />
          </div>

          <motion.div
            variants={stagger}
            initial="hidden"
            animate="show"
            className="px-8 pb-8 pt-10"
          >
            {/* Logo */}
            <motion.div variants={fadeUp} className="mb-6 flex justify-center">
              <motion.div
                className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 shadow-lg shadow-blue-600/30"
                whileHover={{ scale: 1.05 }}
                transition={{ type: 'spring', stiffness: 400, damping: 17 }}
              >
                <motion.div
                  className="absolute inset-0 rounded-2xl bg-blue-400/30 blur-md"
                  animate={{ opacity: [0.4, 0.7, 0.4], scale: [1, 1.15, 1] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
                />
                <Zap className="relative h-7 w-7 text-white" />
              </motion.div>
            </motion.div>

            {/* Heading */}
            <motion.div variants={fadeUp} className="mb-8 text-center">
              <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                Welcome back
              </h1>
              <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                Sign in to your {APP_NAME} workspace
              </p>
            </motion.div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <motion.div variants={fadeUp}>
                <label htmlFor="email" className="sr-only">E-mail address</label>
                <motion.div
                  animate={{
                    boxShadow:
                      focused === 'email'
                        ? '0 0 0 2px rgba(59,130,246,0.35)'
                        : '0 0 0 0px rgba(59,130,246,0)',
                  }}
                  transition={{ duration: 0.2 }}
                  className="rounded-xl"
                >
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setFocused('email')}
                    onBlur={() => setFocused(null)}
                    placeholder="E-mail address"
                    className={cn(
                      'w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3.5 text-sm',
                      'text-zinc-900 placeholder-zinc-400',
                      'transition-colors focus:border-blue-500 focus:outline-none',
                      'dark:border-zinc-700/80 dark:bg-zinc-950/80 dark:text-zinc-100 dark:placeholder-zinc-500',
                      'dark:focus:border-blue-500/60',
                    )}
                  />
                </motion.div>
              </motion.div>

              {/* Password */}
              <motion.div variants={fadeUp}>
                <label htmlFor="password" className="sr-only">Password</label>
                <motion.div
                  animate={{
                    boxShadow:
                      focused === 'password'
                        ? '0 0 0 2px rgba(59,130,246,0.35)'
                        : '0 0 0 0px rgba(59,130,246,0)',
                  }}
                  transition={{ duration: 0.2 }}
                  className="relative rounded-xl"
                >
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocused('password')}
                    onBlur={() => setFocused(null)}
                    placeholder="Password"
                    className={cn(
                      'w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3.5 pr-11 text-sm',
                      'text-zinc-900 placeholder-zinc-400',
                      'transition-colors focus:border-blue-500 focus:outline-none',
                      'dark:border-zinc-700/80 dark:bg-zinc-950/80 dark:text-zinc-100 dark:placeholder-zinc-500',
                      'dark:focus:border-blue-500/60',
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </motion.div>
              </motion.div>

              {/* Error */}
              <AnimatePresence>
                {error && (
                  <motion.p
                    initial={{ opacity: 0, y: -8, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -8, height: 0 }}
                    className="overflow-hidden rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-600 dark:border-red-500/20 dark:bg-red-950/40 dark:text-red-400"
                  >
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>

              {/* Submit */}
              <motion.div variants={fadeUp}>
                <motion.button
                  type="submit"
                  disabled={submitting}
                  whileHover={{ scale: submitting ? 1 : 1.01 }}
                  whileTap={{ scale: submitting ? 1 : 0.98 }}
                  className={cn(
                    'relative w-full overflow-hidden rounded-xl py-3.5 text-sm font-semibold text-white',
                    'bg-blue-600 shadow-lg shadow-blue-600/25',
                    'disabled:cursor-not-allowed disabled:opacity-60',
                  )}
                >
                  {/* Button shimmer on hover */}
                  <motion.span
                    className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                    initial={{ x: '-100%' }}
                    whileHover={{ x: '200%' }}
                    transition={{ duration: 0.6 }}
                  />
                  <span className="relative flex items-center justify-center gap-2">
                    {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    {submitting ? 'Signing in…' : 'Sign in'}
                  </span>
                </motion.button>
              </motion.div>
            </form>
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
