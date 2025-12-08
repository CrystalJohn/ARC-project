/**
 * Chat Service - API integration for RAG chat
 * Task #36: Build chat interface UI
 */

import { authService } from './authService'

const API_URL = import.meta.env.VITE_API_URL

/**
 * Send a chat message to the RAG API
 * @param {Object} params - Chat parameters
 * @param {string} params.query - User question
 * @param {string} [params.conversationId] - Conversation ID for history
 * @param {string} [params.userId] - User ID
 * @param {string[]} [params.docIds] - Filter by specific documents
 * @param {string} [params.template] - Prompt template (default, academic, concise, detailed)
 * @param {number} [params.topK] - Number of context chunks (1-20)
 * @param {boolean} [params.includeHistory] - Include conversation history
 * @returns {Promise<Object>} Chat response with answer, citations, usage
 */
export async function sendChatMessage({
  query,
  conversationId = null,
  userId = 'anonymous',
  docIds = null,
  template = 'default',
  topK = 3,  // Only top 3 most relevant citations
  includeHistory = true
}) {
  const token = await authService.getAccessToken()
  
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query,
      conversation_id: conversationId,
      user_id: userId,
      doc_ids: docIds,
      template,
      top_k: topK,
      include_history: includeHistory
    })
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `API error: ${response.status}`)
  }

  return await response.json()
}

/**
 * Get conversation history
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<Object>} Conversation history
 */
export async function getConversationHistory(conversationId, limit = 100) {
  const token = await authService.getAccessToken()
  
  const response = await fetch(`${API_URL}/api/chat/history/${conversationId}?limit=${limit}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.status}`)
  }

  return await response.json()
}

/**
 * List all conversations for current user
 * @param {number} [page] - Page number
 * @param {number} [pageSize] - Page size
 * @returns {Promise<Object>} List of conversations
 */
export async function listConversations(limit = 50) {
  const token = await authService.getAccessToken()
  const user = await authService.getCurrentUser()
  
  const response = await fetch(
    `${API_URL}/api/chat/history?user_id=${user?.userId || user?.username || 'anonymous'}&limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to list conversations: ${response.status}`)
  }

  return await response.json()
}

/**
 * Delete a conversation
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<Object>} Deletion result
 */
export async function deleteConversation(conversationId) {
  const token = await authService.getAccessToken()
  
  const response = await fetch(`${API_URL}/api/chat/history/${conversationId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.status}`)
  }

  return await response.json()
}

/**
 * Check rate limit status
 * @returns {Promise<Object>} Rate limit status
 */
export async function checkRateLimit() {
  const token = await authService.getAccessToken()
  const user = await authService.getCurrentUser()
  
  const response = await fetch(
    `${API_URL}/api/chat/rate-limit?user_id=${user?.username || 'anonymous'}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to check rate limit: ${response.status}`)
  }

  return await response.json()
}

/**
 * Check budget status
 * @returns {Promise<Object>} Budget status and model recommendation
 */
export async function checkBudget() {
  const token = await authService.getAccessToken()
  const user = await authService.getCurrentUser()
  
  const response = await fetch(
    `${API_URL}/api/chat/budget?user_id=${user?.username || 'anonymous'}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to check budget: ${response.status}`)
  }

  return await response.json()
}

export const chatService = {
  sendChatMessage,
  getConversationHistory,
  listConversations,
  deleteConversation,
  checkRateLimit,
  checkBudget
}
