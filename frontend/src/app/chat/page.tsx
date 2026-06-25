'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Bot, User, MessageSquare, Database, BarChart3, Plus, ChevronLeft, ArrowRight, Zap, MoreVertical, Edit2, Trash2, Check, X, Loader2, Copy } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils/cn'
import { useChatSessions, useChatMessages, useSendChatMessage, useRenameSession, useDeleteSession } from '@/hooks/useChat'
import { useAuth } from '@/providers/AuthProvider'
import type { ChatSession } from '@/lib/api/chat'
import { APP_NAME } from '@/lib/brand'

function ToolBadge({ tool }: { tool: string }) {
  if (tool === 'market_data') {
    return (
      <span className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:border-indigo-800/30 dark:bg-indigo-900/20 dark:text-indigo-300">
        <BarChart3 className="h-3.5 w-3.5" /> Checked Market Data
      </span>
    )
  }
  if (tool === 'text_to_sql') {
    return (
      <span className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 dark:border-amber-800/30 dark:bg-amber-900/20 dark:text-amber-300">
        <Database className="h-3.5 w-3.5" /> Queried Database
      </span>
    )
  }
  return null
}

export default function ChatPage() {
  const router = useRouter()
  const { user } = useAuth()
  
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { data: sessions } = useChatSessions()
  const { data: messages, isLoading: isMessagesLoading } = useChatMessages(activeSessionId)
  const sendMutation = useSendChatMessage()

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const renameMutation = useRenameSession()
  const deleteMutation = useDeleteSession()

  const handleCopy = (id: string, content: string) => {
    navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const SUGGESTIONS = [
    "Show active trades",
    "What's my best performing ticker?",
    "Did I enter any positions today?",
    "Explain how the EMA strategy works"
  ]

  const handleRenameStart = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditingTitle(session.title || 'New Conversation')
    setMenuOpenId(null)
  }

  const handleRenameSave = (e: React.MouseEvent | React.KeyboardEvent, sessionId: string) => {
    e.stopPropagation()
    if (editingTitle.trim()) {
      renameMutation.mutate({ sessionId, title: editingTitle.trim() })
    }
    setEditingSessionId(null)
  }

  const handleRenameCancel = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSessionId(null)
  }

  const handleDelete = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this chat?')) {
      deleteMutation.mutate(sessionId)
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
      }
    }
    setMenuOpenId(null)
  }

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, sendMutation.isPending])

  // Focus input when session changes
  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 100)
  }, [activeSessionId])

  const handleSend = () => {
    if (!inputValue.trim() || sendMutation.isPending) return
    const message = inputValue.trim()
    setInputValue('')
    
    sendMutation.mutate(
      { message, sessionId: activeSessionId || undefined },
      {
        onSuccess: (data) => {
          if (!activeSessionId) {
            setActiveSessionId(data.session_id)
          }
        },
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const startNewChat = () => {
    setActiveSessionId(null)
    setInputValue('')
    inputRef.current?.focus()
  }

  if (!user) return null

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white dark:bg-zinc-950 font-sans">
      
      {/* ── Left Sidebar (History) ── */}
      <aside className="flex w-[260px] shrink-0 flex-col border-r border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        {/* Top: App Logo & Back Button */}
        <div className="flex shrink-0 items-center gap-3 border-b border-zinc-200 p-4 dark:border-zinc-800">
          <button 
            onClick={() => router.push('/dashboard')}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-200 text-zinc-600 transition-colors hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
            title="Back to Dashboard"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-blue-600">
              <Zap className="h-3 w-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{APP_NAME}</span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="flex w-full items-center gap-2 rounded-lg bg-white px-3 py-2.5 text-sm font-medium text-zinc-900 shadow-sm ring-1 ring-zinc-200 transition-colors hover:bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-100 dark:ring-zinc-700 dark:hover:bg-zinc-700/80"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto px-3 pb-4">
          <div className="space-y-1">
            {sessions?.map((session: ChatSession) => {
              const isActive = activeSessionId === session.id
              const isEditing = editingSessionId === session.id
              const isMenuOpen = menuOpenId === session.id
              const isRenaming = renameMutation.isPending && renameMutation.variables?.sessionId === session.id
              const isDeleting = deleteMutation.isPending && deleteMutation.variables === session.id
              const isLoading = isRenaming || isDeleting

              if (isEditing) {
                return (
                  <div key={session.id} className="flex items-center gap-1 rounded-lg bg-zinc-200 px-2 py-1.5 dark:bg-zinc-800">
                    <input
                      autoFocus
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRenameSave(e, session.id)}
                      className="min-w-0 flex-1 rounded bg-white px-2 py-1 text-sm text-zinc-900 outline-none ring-1 ring-blue-500 dark:bg-zinc-900 dark:text-zinc-100"
                    />
                    <button onClick={(e) => handleRenameSave(e, session.id)} className="p-1 text-green-600 hover:bg-zinc-300 dark:text-green-500 dark:hover:bg-zinc-700 rounded">
                      <Check className="h-4 w-4" />
                    </button>
                    <button onClick={handleRenameCancel} className="p-1 text-red-600 hover:bg-zinc-300 dark:text-red-500 dark:hover:bg-zinc-700 rounded">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                )
              }

              return (
                <div key={session.id} className="relative">
                  <button
                    onClick={() => setActiveSessionId(session.id)}
                    disabled={isLoading}
                    className={cn(
                      'group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-colors',
                      isActive
                        ? 'bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100'
                        : 'text-zinc-600 hover:bg-zinc-200/50 dark:text-zinc-400 dark:hover:bg-zinc-800/50',
                      isLoading && 'opacity-60 cursor-not-allowed'
                    )}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-zinc-500" />
                    ) : (
                      <MessageSquare className={cn("h-4 w-4 shrink-0", isActive ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-400 dark:text-zinc-500")} />
                    )}
                    <span className="truncate flex-1">{session.title || 'New Conversation'}</span>
                    
                    <div className={cn("flex items-center", (isActive || isMenuOpen) && !isLoading ? "opacity-100" : "opacity-0 group-hover:opacity-100")}>
                      <div
                        onClick={(e) => { e.stopPropagation(); setMenuOpenId(isMenuOpen ? null : session.id) }}
                        className="p-1 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 rounded hover:bg-zinc-300 dark:hover:bg-zinc-700"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </div>
                    </div>
                  </button>

                  {isMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setMenuOpenId(null)} />
                      <div className="absolute right-0 top-full z-20 mt-1 w-32 rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-zinc-800 dark:ring-white/10">
                        <button
                          onClick={(e) => handleRenameStart(e, session)}
                          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-700"
                        >
                          <Edit2 className="h-4 w-4" /> Rename
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, session.id)}
                          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                        >
                          <Trash2 className="h-4 w-4" /> Delete
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Bottom: User Profile */}
        <div className="shrink-0 border-t border-zinc-200 p-3 dark:border-zinc-800">
          <div className="flex items-center gap-2 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">{user.username}</p>
              <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">TradeBot User</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ── */}
      <main className="flex flex-1 flex-col">
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {(!activeSessionId || (messages?.length === 0 && !isMessagesLoading)) && !sendMutation.isPending && (
            <div className="flex h-full flex-col items-center justify-center p-8">
              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 dark:bg-blue-900/20">
                <Bot className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h1 className="mb-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
                How can I help you trade today?
              </h1>
              <p className="max-w-md text-center text-sm text-zinc-500 dark:text-zinc-400 mb-8">
                I can analyze live market data, query your past paper trades, and explain trading strategies.
              </p>
              
              <div className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                {SUGGESTIONS.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputValue(suggestion)
                      setTimeout(() => inputRef.current?.focus(), 0)
                    }}
                    className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-white p-4 text-left text-sm text-zinc-600 transition-colors hover:border-blue-200 hover:bg-blue-50 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-300 dark:hover:border-blue-900/50 dark:hover:bg-blue-900/20"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {isMessagesLoading && activeSessionId && (
            <div className="flex justify-center p-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            </div>
          )}

          <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
            <div className="space-y-8">
              {messages?.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    'group flex items-end gap-2',
                    msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  )}
                >
                  {/* Avatar — only for bot */}
                  {msg.role === 'assistant' && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-sm">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div className={cn('flex max-w-[85%] flex-col', msg.role === 'user' ? 'items-end' : 'items-start')}>
                    {/* Bubble */}
                    <div
                      className={cn(
                        'rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm',
                        msg.role === 'user'
                          ? 'rounded-br-sm bg-blue-600 text-white'
                          : 'rounded-bl-sm bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100'
                      )}
                    >
                      {msg.role === 'assistant' ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-900 prose-pre:text-zinc-100 prose-pre:rounded-lg prose-pre:p-3 prose-code:text-blue-600 dark:prose-code:text-blue-400">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}
                    </div>

                    {/* Hover Actions & Timestamp */}
                    <div className={cn(
                      "mt-1.5 flex items-center gap-3 opacity-0 transition-opacity group-hover:opacity-100",
                      msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                    )}>
                      <span className="text-[11px] text-zinc-400 font-medium">
                        {new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {msg.role === 'assistant' && (
                        <button
                          onClick={() => handleCopy(msg.id, msg.content)}
                          className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-400 transition-colors hover:text-zinc-700 dark:hover:text-zinc-300"
                        >
                          {copiedId === msg.id ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                          {copiedId === msg.id ? 'Copied' : 'Copy'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Optimistic User Message */}
              {sendMutation.isPending && sendMutation.variables && (
                <div className="flex flex-row-reverse items-end gap-2">
                  <div className="flex max-w-[75%] flex-col items-end">
                    <div className="rounded-2xl rounded-br-sm bg-blue-600 px-4 py-2.5 text-sm leading-relaxed text-white opacity-70 shadow-sm">
                      <p className="whitespace-pre-wrap">{sendMutation.variables.message}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Typing Indicator */}
              {sendMutation.isPending && (
                <div className="flex flex-row items-end gap-2">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-sm">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="rounded-2xl rounded-bl-sm bg-zinc-100 px-4 py-3 shadow-sm dark:bg-zinc-800">
                    <div className="flex h-4 items-center gap-1">
                      <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500" style={{ animationDelay: '0ms' }} />
                      <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500" style={{ animationDelay: '150ms' }} />
                      <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} className="h-4" />
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="shrink-0 p-4">
          <div className="mx-auto max-w-3xl relative">
            <div className="overflow-hidden rounded-2xl border border-zinc-300 bg-white shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:focus-within:border-blue-500">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message TradeBot..."
                disabled={sendMutation.isPending}
                className="w-full resize-none bg-transparent py-4 pl-4 pr-12 text-sm text-zinc-900 placeholder:text-zinc-500 focus:outline-none disabled:opacity-50 dark:text-zinc-100 dark:placeholder:text-zinc-400"
                rows={1}
                style={{ minHeight: '56px', maxHeight: '200px' }}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || sendMutation.isPending}
                className="absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:bg-zinc-200 disabled:text-zinc-400 dark:disabled:bg-zinc-700 dark:disabled:text-zinc-500"
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-zinc-500 dark:text-zinc-400">
              TradeBot can make mistakes. Verify important information.
            </p>
          </div>
        </div>

      </main>
    </div>
  )
}
