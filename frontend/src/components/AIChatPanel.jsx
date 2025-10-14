import React, { useState } from 'react'
import './AIChatPanel.css'

export default function AIChatPanel({ isOpen, onClose, chatData, suggestions, onRegenerateSuggestions, loading = false }) {
  const [selectedSuggestion, setSelectedSuggestion] = useState(null)
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    return new Date(timestamp).toLocaleString('sr-RS', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!isOpen) return null

  return (
    <div className="ai-chat-panel-overlay">
      <div className="ai-chat-panel">
        {/* Header */}
        <div className="ai-panel-header">
          <div className="ai-panel-title">
            <span className="ai-icon">🤖</span>
            <h3>AI Chat Analysis</h3>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Content */}
        <div className="ai-panel-content">
          {/* Chat Info */}
          {chatData && (
            <div className="chat-info-section">
              <div className="info-item">
                <strong>Chat:</strong> {chatData.chatTitle}
              </div>
              {chatData.projectTitle && (
                <div className="info-item">
                  <strong>Project:</strong> {chatData.projectTitle}
                </div>
              )}
              <div className="info-item">
                <strong>Participants:</strong> {chatData.participants?.join(', ')}
              </div>
              <div className="info-item">
                <strong>Messages:</strong> {chatData.messageCount}
              </div>
            </div>
          )}

          {/* Messages Section */}
          {chatData?.messages && (
            <div className="messages-section">
              <h4>Chat Messages</h4>
              <div className="messages-container">
                {chatData.messages.map((message, index) => (
                  <div 
                    key={message.id || index} 
                    className={`message-item ${message.type === 'system' ? 'system-message' : 'user-message'}`}
                  >
                    <div className="message-header">
                      <span className="message-author">{message.author}</span>
                      <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                    </div>
                    <div className="message-content">{message.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Suggestions Section */}
          {suggestions && suggestions.length > 0 && (
            <div className="suggestions-section">
              <div className="suggestions-header">
                <h4>AI Suggestions</h4>
                <button 
                  className="regenerate-btn"
                  onClick={onRegenerateSuggestions}
                  disabled={loading}
                  title="Regenerate suggestions"
                  style={{ opacity: loading ? 0.6 : 1 }}
                >
                  {loading ? '⏳' : '🔄'}
                </button>
              </div>
              <div className="suggestions-container">
                {suggestions.map((suggestion, index) => (
                  <div 
                    key={index} 
                    className={`suggestion-item ${selectedSuggestion === index ? 'selected' : ''}`}
                    onClick={() => setSelectedSuggestion(index)}
                  >
                    <div className="suggestion-header">
                      <span className="suggestion-number">#{index + 1}</span>
                      <button 
                        className="copy-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          copyToClipboard(suggestion)
                        }}
                        title="Copy suggestion"
                      >
                        {copied ? '✅' : '📋'}
                      </button>
                    </div>
                    <div className="suggestion-text">{suggestion}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="ai-panel-footer">
          <button className="secondary-btn" onClick={onClose}>
            Close
          </button>
          {selectedSuggestion !== null && (
            <button 
              className="primary-btn"
              onClick={() => copyToClipboard(suggestions[selectedSuggestion])}
            >
              Copy Selected
            </button>
          )}
        </div>
      </div>
    </div>
  )
}