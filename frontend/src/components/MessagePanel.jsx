import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { openInExternalBrowser, copyToClipboard } from '../utils/browserUtils'
import AIChatPanel from './AIChatPanel'

export default function MessagePanel({ onOpenChat }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastExtracted, setLastExtracted] = useState(null)
  const [groupedChats, setGroupedChats] = useState({})
  const [chats, setChats] = useState([])
  
  // AI Chat Panel state
  const [showAIPanel, setShowAIPanel] = useState(false)
  const [aiChatData, setAiChatData] = useState(null)
  const [aiSuggestions, setAiSuggestions] = useState([])
  const [aiLoading, setAiLoading] = useState(false)

  // Open message in Chrome debugger instead of regular browser
  const openMessageInChrome = async (chatUrl, conversationId = null) => {
    try {
      // Extract conversation ID from URL if not provided
      if (!conversationId && chatUrl) {
        const urlMatch = chatUrl.match(/room_([a-f0-9]+)/) || 
                        chatUrl.match(/messages\/([^\/\?]+)/)
        conversationId = urlMatch ? urlMatch[1] : null
      }

      if (conversationId) {
        // Use our Chrome control API - ispravka URL-a
        const response = await axios.post('/api/messages/chrome/open-message/', {
          conversation_id: conversationId
        })
        
        if (response.data.success) {
          console.log('✅ Opened message in Chrome debugger:', response.data.action)
        } else {
          console.error('❌ Failed to open in Chrome:', response.data.error)
          // Fallback to regular browser
          openInExternalBrowser(chatUrl)
        }
      } else {
        // Fallback to regular browser if no conversation ID
        openInExternalBrowser(chatUrl)
      }
    } catch (error) {
      console.error('❌ Error opening message in Chrome:', error)
      // Fallback to regular browser
      openInExternalBrowser(chatUrl)
    }
  }

  // Load messages when component mounts
  useEffect(() => {
    loadStoredMessages()
    loadChatsFromDatabase()
  }, [])

  // Scrape active chat in Chrome debugger for AI analysis
  const scrapeActiveChat = async () => {
    try {
      setAiLoading(true)
      console.log('🤖 Analyzing active chat in Chrome debugger...')
      
      // Call endpoint to scrape active chat
      const response = await axios.post('/api/messages/ai/analyze-active-chat/')
      
      if (response.data.success) {
        const responseData = response.data.data
        console.log('✅ Active chat analyzed:', responseData)
        
        // Set data for AI panel
        setAiChatData(responseData.chatData)
        setAiSuggestions(responseData.suggestions || [])
        setShowAIPanel(true)
      } else {
        alert(`❌ Failed to analyze chat: ${response.data.error}`)
      }
    } catch (error) {
      console.error('❌ Error analyzing active chat:', error)
      alert('❌ Error analyzing chat. Make sure Chrome debugger is open with an active chat.')
    } finally {
      setAiLoading(false)
    }
  }

  // Regenerate AI suggestions
  const regenerateAISuggestions = async () => {
    if (!aiChatData) return
    
    try {
      setAiLoading(true)
      const response = await axios.post('/api/messages/ai/analyze-active-chat/')
      
      if (response.data.success) {
        const responseData = response.data.data
        setAiSuggestions(responseData.suggestions || [])
      } else {
        alert(`❌ Failed to regenerate suggestions: ${response.data.error}`)
      }
    } catch (error) {
      console.error('❌ Error regenerating suggestions:', error)
      alert('❌ Error regenerating suggestions.')
    } finally {
      setAiLoading(false)
    }
  }

  // Load chats from database
  const loadChatsFromDatabase = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/messages/chats/')
      if (response.ok) {
        const chatsData = await response.json()
        setChats(chatsData)
        console.log('📊 Učitano', chatsData.length, 'chatova iz baze')
      }
    } catch (error) {
      console.error('Greška pri učitavanju chatova:', error)
    }
  }

  // Load stored messages from backend (kombinacija baze i file sistema)
  const loadStoredMessages = async () => {
    try {
      // Prvo pokušaj da učitaš iz baze
      const dbResponse = await fetch('http://localhost:8000/api/messages/messages/')
      if (dbResponse.ok) {
        const dbData = await dbResponse.json()
        if (dbData.length > 0) {
          setMessages(dbData)
          groupMessagesByChat(dbData)
          setLastExtracted('Učitano iz baze podataka')
          return
        }
      }

      // Ako nema podataka u bazi, pokušaj file sistem
      const response = await fetch('/static/extracted_messages.json')
      if (response.ok) {
        const data = await response.json()
        if (data.messages) {
          setMessages(data.messages)
          groupMessagesByChat(data.messages)
          setLastExtracted(data.extractedAt || 'Previously extracted')
        }
      }
    } catch (error) {
      console.log('No stored messages found, will need to extract new ones')
    }
  }

  // Group messages by conversation/chat
  const groupMessagesByChat = (messagesData) => {
    const grouped = {}
    messagesData.forEach(message => {
      const chatId = message.conversationId || message.conversation_id || message.sender || 'Unknown'
      if (!grouped[chatId]) {
        grouped[chatId] = {
          chatId,
          sender: message.sender,
          messages: [],
          lastMessage: null,
          unreadCount: 0,
          chatUrl: message.chatUrl || message.chat_url || `https://www.upwork.com/messages/${chatId}`
        }
      }
      grouped[chatId].messages.push(message)
      
      // Update last message
      if (!grouped[chatId].lastMessage || new Date(message.timestamp) > new Date(grouped[chatId].lastMessage.timestamp)) {
        grouped[chatId].lastMessage = message
      }
      
      // Count unread messages
      if (!message.isRead) {
        grouped[chatId].unreadCount++
      }
    })
    
    setGroupedChats(grouped)
  }

  // Extract messages from Upwork - koristi novi endpoint
  const extractMessages = async () => {
    setLoading(true)
    try {
      // Koristi novi upwork_messages endpoint
      const response = await axios.post('http://localhost:8000/api/messages/extract/')
      
      if (response.data.success) {
        const extractedMessages = response.data.messages || []
        setMessages(extractedMessages)
        groupMessagesByChat(extractedMessages)
        setLastExtracted(new Date().toLocaleString())
        
        // Refresh chats from database
        await loadChatsFromDatabase()
        
        console.log('✅ Uspešno ekstraktovano', extractedMessages.length, 'poruka')
      } else {
        alert(`Message extraction failed: ${response.data.message}`)
      }
    } catch (error) {
      console.error('Failed to extract messages:', error)
      
      let errorMessage = 'Failed to extract messages.';
      if (error.response && error.response.data && error.response.data.message) {
        errorMessage = error.response.data.message;
      } else if (error.response && error.response.status === 408) {
        errorMessage = 'Message extraction timed out. Make sure Chrome is open and logged into Upwork.';
      }
      
      // Fallback to old endpoint if new one fails
      try {
        console.log('🔄 Pokušavam sa starim endpoint-om...')
        const fallbackResponse = await axios.post('/api/notification-push/scrape-messages/')
        
        if (fallbackResponse.data.success) {
          const extractedMessages = fallbackResponse.data.data.messages || []
          setMessages(extractedMessages)
          groupMessagesByChat(extractedMessages)
          setLastExtracted(new Date().toLocaleString())
        } else {
          alert(errorMessage)
        }
      } catch (fallbackError) {
        alert(errorMessage)
      }
    }
    setLoading(false)
  }

  // Open chat in new tab or in app
  const openChat = (chatUrl, chatId = null) => {
    if (onOpenChat && chatId) {
      // Otvori chat u aplikaciji
      onOpenChat(chatId)
    } else if (chatUrl) {
      // Otvori u Chrome debugger-u umesto external browser-a
      openMessageInChrome(chatUrl, chatId)
    }
  }

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown time'
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now - date
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffHours / 24)
      
      if (diffDays > 0) return `${diffDays}d ago`
      if (diffHours > 0) return `${diffHours}h ago`
      return 'Recent'
    } catch (e) {
      return 'Unknown time'
    }
  }

  const chatList = Object.values(groupedChats).sort((a, b) => {
    // Sort by unread first, then by last message time
    if (a.unreadCount > 0 && b.unreadCount === 0) return -1
    if (a.unreadCount === 0 && b.unreadCount > 0) return 1
    
    const timeA = a.lastMessage ? new Date(a.lastMessage.timestamp) : new Date(0)
    const timeB = b.lastMessage ? new Date(b.lastMessage.timestamp) : new Date(0)
    return timeB - timeA
  })

  return (
    <div style={{ 
      border: '1px solid #ddd', 
      borderRadius: 8, 
      padding: 20, 
      marginTop: 20,
      backgroundColor: '#f9f9f9'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 15 
      }}>
        <h2 style={{ margin: 0, color: '#2c3e50' }}>
          💬 Upwork Messages & Chats
        </h2>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {lastExtracted && (
            <span style={{ fontSize: '12px', color: '#666' }}>
              Last updated: {lastExtracted}
            </span>
          )}
          <button 
            onClick={extractMessages}
            disabled={loading}
            style={{
              backgroundColor: loading ? '#95a5a6' : '#3498db',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: 4,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '🔄 Extracting...' : '📬 Refresh Messages'}
          </button>
        </div>
      </div>

      {/* AI Chat Section */}
      <div style={{ marginBottom: 30 }}>
        <h3 style={{ 
          color: '#2c3e50', 
          marginBottom: 15,
          paddingLeft: 5,
          borderLeft: '4px solid #e74c3c'
        }}>
          🤖 AI Chat Assistant
        </h3>
        <div style={{ 
          background: '#fff5f5',
          padding: 20,
          borderRadius: 8,
          border: '1px solid #f8d7da'
        }}>
          <p style={{ margin: '0 0 15px 0', color: '#721c24' }}>
            Open a conversation in Chrome debugger, then use AI to analyze and suggest replies.
          </p>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button 
              onClick={scrapeActiveChat}
              disabled={aiLoading}
              style={{
                backgroundColor: aiLoading ? '#95a5a6' : '#e74c3c',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: 4,
                cursor: aiLoading ? 'not-allowed' : 'pointer',
                fontWeight: 'bold'
              }}
            >
              {aiLoading ? '🔄 Analyzing...' : '🤖 Analyze Active Chat'}
            </button>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Make sure you have a chat open in Chrome debugger
            </span>
          </div>
        </div>
      </div>

      {/* Database Chats Section */}
      {chats.length > 0 && (
        <div style={{ marginBottom: 30 }}>
          <h3 style={{ 
            color: '#2c3e50', 
            marginBottom: 15,
            paddingLeft: 5,
            borderLeft: '4px solid #3498db'
          }}>
            📊 Saved Chats ({chats.length})
          </h3>
          <div style={{ 
            display: 'grid', 
            gap: 10, 
            maxHeight: '300px', 
            overflowY: 'auto',
            background: '#f8f9fa',
            padding: 15,
            borderRadius: 8,
            border: '1px solid #e9ecef'
          }}>
            {chats.map((chat) => (
              <div
                key={chat.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 12,
                  backgroundColor: 'white',
                  border: `1px solid ${chat.unread_count > 0 ? '#f39c12' : '#dee2e6'}`,
                  borderRadius: 6,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 8, 
                    marginBottom: 4 
                  }}>
                    <h4 style={{ 
                      margin: 0, 
                      color: '#2c3e50',
                      fontSize: '14px',
                      fontWeight: chat.unread_count > 0 ? 'bold' : 'normal'
                    }}>
                      {chat.other_participant || 'Unknown Contact'}
                    </h4>
                    {chat.unread_count > 0 && (
                      <span style={{
                        backgroundColor: '#e74c3c',
                        color: 'white',
                        fontSize: '11px',
                        padding: '2px 6px',
                        borderRadius: '10px',
                        minWidth: '16px',
                        textAlign: 'center'
                      }}>
                        {chat.unread_count}
                      </span>
                    )}
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#6c757d' 
                  }}>
                    {chat.total_messages} poruka | {formatTime(chat.last_message_at)}
                  </div>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  gap: 5 
                }}>
                  {onOpenChat && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onOpenChat(chat.id)
                      }}
                      style={{
                        background: '#3498db',
                        color: 'white',
                        border: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        cursor: 'pointer'
                      }}
                      title="Otvori u aplikaciji"
                    >
                      💬 Open
                    </button>
                  )}
                  {/* Uklonjen Link dugme - korisnik ručno otvara chat u Chrome */}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Messages Section */}
      <div>
        <h3 style={{ 
          color: '#2c3e50', 
          marginBottom: 15,
          paddingLeft: 5,
          borderLeft: '4px solid #27ae60'
        }}>
          📥 Extracted Messages ({chatList.length})
        </h3>

      {chatList.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: 40, 
          color: '#7f8c8d',
          backgroundColor: 'white',
          borderRadius: 4,
          border: '1px solid #ecf0f1'
        }}>
          <h3>No messages found</h3>
          <p>Click "Refresh Messages" to extract conversations from your Upwork account.</p>
          <p style={{ fontSize: '14px' }}>
            Make sure Chrome is open and you're logged into Upwork.
          </p>
        </div>
      ) : (
        <div style={{ 
          display: 'grid', 
          gap: 12, 
          maxHeight: '500px', 
          overflowY: 'auto' 
        }}>
          {chatList.map((chat, index) => (
            <div
              key={chat.chatId}
              onClick={() => openChat(chat.chatUrl)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 15,
                backgroundColor: 'white',
                border: `1px solid ${chat.unreadCount > 0 ? '#f39c12' : '#ecf0f1'}`,
                borderRadius: 6,
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: chat.unreadCount > 0 ? '0 2px 4px rgba(243, 156, 18, 0.1)' : 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f8f9fa'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              {/* Chat info */}
              <div style={{ flex: 1 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 8, 
                  marginBottom: 4 
                }}>
                  <h4 style={{ 
                    margin: 0, 
                    color: '#2c3e50',
                    fontWeight: chat.unreadCount > 0 ? 'bold' : 'normal'
                  }}>
                    {chat.sender || 'Unknown Contact'}
                  </h4>
                  {chat.unreadCount > 0 && (
                    <span style={{
                      backgroundColor: '#e74c3c',
                      color: 'white',
                      fontSize: '12px',
                      padding: '2px 6px',
                      borderRadius: '50%',
                      minWidth: '18px',
                      textAlign: 'center'
                    }}>
                      {chat.unreadCount}
                    </span>
                  )}
                </div>
                
                {chat.lastMessage && (
                  <p style={{ 
                    margin: 0, 
                    color: '#7f8c8d', 
                    fontSize: '14px',
                    lineHeight: '1.4',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    maxWidth: '300px'
                  }}>
                    {chat.lastMessage.preview || 'No preview available'}
                  </p>
                )}
              </div>

              {/* Timestamp, status and action buttons */}
              <div style={{ 
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: 8,
                minWidth: '120px'
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#95a5a6',
                  marginBottom: 4
                }}>
                  {chat.lastMessage ? formatTime(chat.lastMessage.timestamp) : 'No messages'}
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#3498db'
                }}>
                  {chat.messages.length} message{chat.messages.length !== 1 ? 's' : ''}
                </div>
                
                {/* Action buttons */}
                <div style={{ 
                  display: 'flex', 
                  gap: 5 
                }}>
                  {onOpenChat && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        openChat(null, chat.chatId)
                      }}
                      style={{
                        background: '#3498db',
                        color: 'white',
                        border: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        cursor: 'pointer'
                      }}
                      title="Otvori u aplikaciji"
                    >
                      💬 Chat
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      openChat(chat.chatUrl)
                    }}
                    style={{
                      background: '#27ae60',
                      color: 'white',
                      border: 'none',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      cursor: 'pointer'
                    }}
                    title="Otvori na Upwork"
                  >
                    🔗 Link
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary stats */}
      {chatList.length > 0 && (
        <div style={{ 
          marginTop: 15, 
          padding: 10, 
          backgroundColor: 'white', 
          borderRadius: 4,
          border: '1px solid #ecf0f1',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '14px',
          color: '#7f8c8d'
        }}>
          <span>
            📊 Total: {chatList.length} conversation{chatList.length !== 1 ? 's' : ''}
          </span>
          <span>
            🔔 Unread: {chatList.reduce((sum, chat) => sum + chat.unreadCount, 0)} message{chatList.reduce((sum, chat) => sum + chat.unreadCount, 0) !== 1 ? 's' : ''}
          </span>
          <span>
            💬 Total messages: {Object.values(groupedChats).reduce((sum, chat) => sum + chat.unreadCount, 0)}
          </span>
        </div>
      )}

      {/* AI Chat Analysis Panel */}
      <AIChatPanel
        isOpen={showAIPanel}
        onClose={() => setShowAIPanel(false)}
        chatData={aiChatData}
        suggestions={aiSuggestions}
        onRegenerateSuggestions={regenerateAISuggestions}
        loading={aiLoading}
      />
      </div>
    </div>
  )
}