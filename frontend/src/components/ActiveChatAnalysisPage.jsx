import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ActiveChatAnalysisPage.css';

const ActiveChatAnalysisPage = ({ chatData: passedChatData, suggestions: passedSuggestions, onBack }) => {
  const [chatData, setChatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    if (passedChatData) {
      // Use passed data if available
      setChatData(passedChatData);
      setSuggestions(passedSuggestions || []);
      setLoading(false);
    } else {
      // Otherwise fetch fresh data
      analyzeActiveChat();
    }
  }, [passedChatData, passedSuggestions]);

  const analyzeActiveChat = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/messages/ai/analyze-active-chat/');
      
      if (response.data.success) {
        setChatData(response.data.data.chatData);
        setSuggestions(response.data.data.suggestions || []);
      } else {
        setError(response.data.error || 'Failed to analyze chat');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Network error occurred');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'No timestamp';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const goBack = () => {
    if (onBack) {
      onBack();
    }
  };

  if (loading) {
    return (
      <div className="analysis-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <h2>🤖 Analyzing Active Chat...</h2>
          <p>Extracting messages and generating AI insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-page">
        <div className="error-container">
          <h2>❌ Analysis Failed</h2>
          <p>{error}</p>
          <div className="action-buttons">
            <button onClick={analyzeActiveChat} className="retry-btn">
              🔄 Retry Analysis
            </button>
            <button onClick={goBack} className="back-btn">
              ← Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-page">
      {/* Header */}
      <div className="analysis-header">
        <div className="header-left">
          <button onClick={goBack} className="back-button">
            ← Back
          </button>
          <h1>🤖 AI Chat Analysis</h1>
        </div>
        <div className="header-right">
          <button onClick={analyzeActiveChat} className="refresh-btn">
            🔄 Refresh Analysis
          </button>
        </div>
      </div>

      {/* Chat Overview */}
      {chatData && (
        <div className="chat-overview">
          <div className="overview-card">
            <h3>📊 Chat Overview</h3>
            <div className="overview-grid">
              <div className="overview-item">
                <span className="label">Participants:</span>
                <span className="value">{chatData.participants?.join(', ') || 'Unknown'}</span>
              </div>
              <div className="overview-item">
                <span className="label">Project:</span>
                <span className="value">{chatData.projectTitle || chatData.chatTitle || 'No project specified'}</span>
              </div>
              <div className="overview-item">
                <span className="label">Total Messages:</span>
                <span className="value">{chatData.messageCount || chatData.messages?.length || 0}</span>
              </div>
              <div className="overview-item">
                <span className="label">Analysis Time:</span>
                <span className="value">{formatTimestamp(chatData.extractedAt)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="analysis-content">
        {/* Messages Section */}
        {chatData?.messages && (
          <div className="messages-section">
            <h3>💬 Chat Messages ({chatData.messages.length})</h3>
            <div className="messages-container">
              {chatData.messages.map((message, index) => (
                <div 
                  key={message.id || index} 
                  className={`message-card ${message.type === 'system' ? 'system-message' : 'user-message'}`}
                >
                  <div className="message-header">
                    <div className="message-author">
                      <span className="author-name">{message.author}</span>
                      {message.type === 'system' && <span className="system-badge">System</span>}
                    </div>
                    <div className="message-meta">
                      <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                      <span className="message-number">#{index + 1}</span>
                    </div>
                  </div>
                  <div className="message-content">
                    {message.content}
                  </div>
                  <div className="message-actions">
                    <button 
                      className="copy-message-btn"
                      onClick={() => copyToClipboard(message.content)}
                      title="Copy message"
                    >
                      📋 Copy
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Suggestions - Now below messages */}
        {suggestions && suggestions.length > 0 && (
          <div className="suggestions-section">
            <h3>💡 AI Suggestions</h3>
            <div className="suggestions-container">
              {suggestions.map((suggestion, index) => (
                <div key={index} className="suggestion-card">
                  <div className="suggestion-header">
                    <span className="suggestion-number">{index + 1}</span>
                    <button 
                      className="copy-btn"
                      onClick={() => copyToClipboard(suggestion)}
                      title="Copy to clipboard"
                    >
                      📋
                    </button>
                  </div>
                  <div className="suggestion-content">
                    {suggestion}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="analysis-footer">
        <p>Analysis completed • {chatData?.messages?.length || 0} messages processed</p>
      </div>
    </div>
  );
};

export default ActiveChatAnalysisPage;