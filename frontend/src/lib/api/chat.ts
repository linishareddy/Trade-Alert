import request from './client'

// ── Types ────────────────────────────────────────────────────────────────────

export interface ChatSession {
  id: string
  title: string | null
  created_at: string
  last_message_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  tool_used: string | null
  created_at: string
}

export interface SendMessageResponse {
  session_id: string
  reply: string
  tool_used: string | null
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const chatApi = {
  /** Send a message. If session_id is omitted, a new session is started. */
  send: (message: string, session_id?: string) =>
    request<SendMessageResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id }),
    }),

  /** List all sessions for the logged-in user, sorted by recent activity. */
  listSessions: () => request<ChatSession[]>('/chat/sessions'),

  /** Fetch the full message history for a session. */
  getMessages: (session_id: string) =>
    request<ChatMessage[]>(`/chat/sessions/${session_id}/messages`),

  /** Rename a chat session */
  renameSession: (session_id: string, title: string) =>
    request<ChatSession>(`/chat/sessions/${session_id}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    }),

  /** Delete a chat session */
  deleteSession: (session_id: string) =>
    request<{ status: string }>(`/chat/sessions/${session_id}`, {
      method: 'DELETE',
    }),
}
