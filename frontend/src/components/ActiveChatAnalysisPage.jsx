import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ActiveChatAnalysisPage.css';

const ActiveChatAnalysisPage = ({ chatData: passedChatData, suggestions: passedSuggestions, onBack }) => {
  const [chatData, setChatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  
  // AI Interview state
  const [aiInterviewData, setAiInterviewData] = useState(null);
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [interviewError, setInterviewError] = useState(null);
  const [interviewSessionCreated, setInterviewSessionCreated] = useState(false);
  
  // Answer suggestion state
  const [questionInput, setQuestionInput] = useState('');
  const [answerSuggestion, setAnswerSuggestion] = useState(null);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [suggestionError, setSuggestionError] = useState(null);
  const [showAnswerSuggestion, setShowAnswerSuggestion] = useState(false);
  
  // Auto smart responses state
  const [smartResponses, setSmartResponses] = useState([]);
  const [smartResponsesLoading, setSmartResponsesLoading] = useState(false);
  const [smartResponsesError, setSmartResponsesError] = useState(null);
  const [showSmartResponses, setShowSmartResponses] = useState(false);

  useEffect(() => {
    console.log('ActiveChatAnalysisPage useEffect triggered');
    console.log('passedChatData:', passedChatData);
    console.log('passedSuggestions:', passedSuggestions);
    
    if (passedChatData) {
      // Use passed data if available
      setChatData(passedChatData);
      setSuggestions(passedSuggestions || []);
      setLoading(false);
    } else {
      // Otherwise fetch fresh data
      console.log('No passed data, calling analyzeActiveChat...');
      analyzeActiveChat();
    }
  }, [passedChatData, passedSuggestions]);

  useEffect(() => {
    console.log('aiInterviewData changed:', aiInterviewData);
  }, [aiInterviewData]);

  const analyzeActiveChat = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/messages/ai/analyze-active-chat/', {}, {
        timeout: 180000 // 3 minute timeout
      });
      
      if (response.data.success) {
        setChatData(response.data.data.chatData);
        setSuggestions(response.data.data.suggestions || []);
        
        // Check for AI Interview data
        if (response.data.data.aiInterview) {
          setAiInterviewData(response.data.data.aiInterview);
          // Don't automatically set session as created from analysis
          setInterviewSessionCreated(false);
        }
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

  const createAiInterview = async () => {
    try {
      setInterviewLoading(true);
      setInterviewError(null);
      
      // Get context_id from already ingested AI Interview data
      const contextId = aiInterviewData?.contextId;
      
      const response = await axios.post('/api/messages/ai/create-interview-from-chat/', {
        context_id: contextId
      });

      if (response.data.session_id) {
        setAiInterviewData(prev => ({
          ...prev,
          ...response.data
        }));
        setInterviewSessionCreated(true);
      } else {
        setInterviewError(response.data.error || 'Failed to create AI interview');
      }
      
    } catch (err) {
      console.error('Error creating AI interview:', err);
      setInterviewError(err.response?.data?.error || 'Failed to create AI interview');
    } finally {
      setInterviewLoading(false);
    }
  };

  const suggestAnswerFromChat = async () => {
    if (!questionInput.trim()) {
      setSuggestionError('Please enter a question first');
      return;
    }

    try {
      setSuggestionLoading(true);
      setSuggestionError(null);
      
      const sessionId = aiInterviewData?.session_id;
      if (!sessionId) {
        setSuggestionError('No interview session found. Please create an interview first.');
        return;
      }

      const response = await axios.post(`/api/interview/sessions/${sessionId}/suggest-answer/`, {
        question: questionInput.trim()
      });

      if (response.data.success) {
        setAnswerSuggestion(response.data.suggestion);
        setShowAnswerSuggestion(true);
      } else {
        setSuggestionError(response.data.error || 'Failed to generate answer suggestion');
      }
      
    } catch (err) {
      console.error('Error suggesting answer:', err);
      setSuggestionError(err.response?.data?.error || 'Failed to suggest answer');
    } finally {
      setSuggestionLoading(false);
    }
  };

  // Function to generate smart responses from chat
  const generateSmartResponses = async () => {
    if (!chatData?.messages || chatData.messages.length === 0) {
      setSmartResponsesError('No chat data available for smart response generation');
      return;
    }

    setSmartResponsesLoading(true);
    setSmartResponsesError(null);

    try {
      const response = await axios.post('/api/interview/generate-smart-responses/', {
        chat_data: chatData,
        context: {
          projectTitle: chatData.projectTitle || 'Project Discussion',
          messageCount: chatData.messages.length,
          participants: [...new Set(chatData.messages.map(m => m.author))]
        }
      });

      if (response.data.smart_responses) {
        setSmartResponses(response.data.smart_responses);
        setShowSmartResponses(true);
      }
    } catch (error) {
      console.error('Error generating smart responses:', error);
      setSmartResponsesError(
        error.response?.data?.error || 
        'Failed to generate smart responses. Please try again.'
      );
    } finally {
      setSmartResponsesLoading(false);
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
      {/* Debug info */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{background: '#f0f0f0', padding: '10px', margin: '10px', fontSize: '12px'}}>
          <strong>Debug Info:</strong><br/>
          Loading: {loading.toString()}<br/>
          Error: {error || 'None'}<br/>
          ChatData exists: {!!chatData}<br/>
          Messages count: {chatData?.messages?.length || 0}<br/>
          InterviewSessionCreated: {interviewSessionCreated.toString()}<br/>
          AIInterviewData exists: {!!aiInterviewData}
        </div>
      )}
      
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

      {/* Chat Overview - Always show if we have any data */}
      {(chatData || loading || error) && (
        <div className="chat-overview">
          <div className="overview-card">
            <h3>📊 Chat Overview</h3>
            {chatData ? (
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
            ) : (
              <div className="no-data-message">
                <p>⏳ Waiting for chat analysis...</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="analysis-content">
        {/* Show message if no chat data */}
        {!chatData && !loading && (
          <div className="no-chat-data">
            <h3>ℹ️ No Chat Data Available</h3>
            <p>Please analyze active chat first to see smart response suggestions.</p>
            <button onClick={analyzeActiveChat} className="analyze-btn">
              🔍 Analyze Active Chat
            </button>
          </div>
        )}

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

        {/* AI Interview Section */}
        <div className="ai-interview-section">
          <div className="interview-header">
            <h3>🎯 AI Interview Assistant</h3>
            <div className="interview-controls">
              {!aiInterviewData && !loading && (
                <button 
                  onClick={analyzeActiveChat}
                  className="create-interview-btn"
                  style={{backgroundColor: '#FF9800'}}
                >
                  🔍 Run Chat Analysis First
                </button>
              )}
              
              {!interviewSessionCreated && aiInterviewData?.contextId && (
                <button 
                  onClick={createAiInterview}
                  disabled={interviewLoading}
                  className="create-interview-btn"
                >
                  {interviewLoading ? '🔄 Creating...' : '🚀 Create AI Interview'}
                </button>
              )}
              {!aiInterviewData?.contextId && aiInterviewData && (
                <span className="interview-status-warning">
                  {aiInterviewData?.error ? 
                    `❌ AI Interview Error: ${aiInterviewData.error}` : 
                    '⚠️ Chat analysis required for AI Interview'}
                </span>
              )}
              {interviewSessionCreated && aiInterviewData && (
                <span className="interview-status">
                  ✅ Interview Ready • Session ID: {aiInterviewData.session_id}
                </span>
              )}
            </div>
          </div>

          {interviewError && (
            <div className="interview-error">
              <p>❌ {interviewError}</p>
              <button onClick={createAiInterview} className="retry-btn">
                🔄 Retry
              </button>
            </div>
          )}

          {interviewSessionCreated && aiInterviewData && (
            <div className="interview-content">
              <div className="interview-info">
                <h4>📋 Interview Information</h4>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="label">Session ID:</span>
                    <span className="value">{aiInterviewData.session_id || aiInterviewData.contextId}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">API Endpoint:</span>
                    <span className="value">/api/interview/</span>
                  </div>
                  <div className="info-item">
                    <span className="label">Status:</span>
                    <span className="value">Ready for AI Processing</span>
                  </div>
                </div>
              </div>

              <div className="interview-actions">
                <h4>🛠️ Available Actions</h4>
                <div className="action-buttons">
                  <button 
                    onClick={() => copyToClipboard(`/api/interview/sessions/${aiInterviewData.session_id || aiInterviewData.contextId}/questions/`)}
                    className="api-btn"
                  >
                    📋 Copy Questions API
                  </button>
                  <button 
                    onClick={() => copyToClipboard(`/api/interview/sessions/${aiInterviewData.session_id || aiInterviewData.contextId}/`)}
                    className="api-btn"
                  >
                    📋 Copy Session API
                  </button>
                  <button 
                    onClick={() => window.open(`/api/interview/sessions/${aiInterviewData.session_id || aiInterviewData.contextId}/`, '_blank')}
                    className="view-btn"
                  >
                    👁️ View Session Data
                  </button>
                </div>
              </div>

              <div className="interview-description">
                <h4>ℹ️ About AI Interview</h4>
                <p>
                  The AI Interview system has processed your chat context and is ready to generate intelligent interview questions 
                  based on the conversation content. Use the API endpoints above to interact with the AI interview engine.
                </p>
                <ul>
                  <li><strong>Generate Questions:</strong> AI will create relevant interview questions based on chat context</li>
                  <li><strong>Analyze Responses:</strong> AI can evaluate and provide feedback on interview responses</li>
                  <li><strong>Follow-up Questions:</strong> Dynamic question generation based on previous answers</li>
                </ul>
              </div>

              {/* Smart Responses Feature */}
              <div className="smart-responses-section">
                <h4>🤖 Smart Response Suggestions</h4>
                <p>AI automatically analyzes your chat and suggests intelligent responses based on the conversation context.</p>
                
                <div className="smart-responses-actions">
                  <button 
                    onClick={generateSmartResponses}
                    disabled={smartResponsesLoading || !chatData?.messages?.length}
                    className="generate-responses-btn"
                  >
                    {smartResponsesLoading ? '🔄 Analyzing Chat...' : '🎯 Generate Smart Responses'}
                  </button>
                  
                  {showSmartResponses && smartResponses.length > 0 && (
                    <button 
                      onClick={() => {
                        setSmartResponses([]);
                        setShowSmartResponses(false);
                        setSmartResponsesError(null);
                      }}
                      className="clear-responses-btn"
                    >
                      🗑️ Clear Responses
                    </button>
                  )}
                </div>

                {smartResponsesError && (
                  <div className="suggestion-error">
                    <p>❌ {smartResponsesError}</p>
                  </div>
                )}

                {showSmartResponses && smartResponses.length > 0 && (
                  <div className="smart-responses-results">
                    <h5>💡 Suggested Responses:</h5>
                    {smartResponses.map((response, index) => (
                      <div key={index} className="smart-response-item">
                        <div className="response-header">
                          <h6>📝 Response {index + 1}</h6>
                          <div className="response-actions">
                            <button 
                              onClick={() => copyToClipboard(response.response)}
                              className="copy-response-btn"
                              title="Copy response to clipboard"
                            >
                              📋 Copy
                            </button>
                          </div>
                        </div>
                        
                        <div className="response-content">
                          <div className="response-text">
                            <strong>Response:</strong>
                            <p>{response.response}</p>
                          </div>
                          
                          {response.context && (
                            <div className="response-context">
                              <strong>Based on:</strong>
                              <p className="context-text">{response.context}</p>
                            </div>
                          )}
                          
                          {response.confidence && (
                            <div className="confidence-score">
                              <strong>Confidence:</strong>
                              <span className={`confidence-value ${response.confidence > 0.7 ? 'high' : response.confidence > 0.4 ? 'medium' : 'low'}`}>
                                {Math.round(response.confidence * 100)}%
                              </span>
                            </div>
                          )}
                          
                          {response.topics && response.topics.length > 0 && (
                            <div className="response-topics">
                              <strong>Related Topics:</strong>
                              <div className="topics-list">
                                {response.topics.map((topic, idx) => (
                                  <span key={idx} className="topic-tag">{topic}</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Answer Suggestion Feature */}
              <div className="answer-suggestion-section">
                <h4>💬 Custom Question Answer Suggestions</h4>
                <p>Get AI-powered answer suggestions for specific questions based on your chat conversation history.</p>
                
                <div className="question-input-section">
                  <div className="input-group">
                    <label htmlFor="question-input">Interview Question:</label>
                    <textarea
                      id="question-input"
                      value={questionInput}
                      onChange={(e) => setQuestionInput(e.target.value)}
                      placeholder="Enter an interview question (e.g., 'Tell me about your Python experience')"
                      className="question-textarea"
                      rows="3"
                    />
                  </div>
                  
                  <div className="suggestion-actions">
                    <button 
                      onClick={suggestAnswerFromChat}
                      disabled={suggestionLoading || !questionInput.trim()}
                      className="suggest-answer-btn"
                    >
                      {suggestionLoading ? '🔄 Generating...' : '🎯 Suggest Answer from Chat'}
                    </button>
                    
                    {questionInput && (
                      <button 
                        onClick={() => {
                          setQuestionInput('');
                          setAnswerSuggestion(null);
                          setSuggestionError(null);
                          setShowAnswerSuggestion(false);
                        }}
                        className="clear-btn"
                      >
                        🗑️ Clear
                      </button>
                    )}
                  </div>
                </div>

                {suggestionError && (
                  <div className="suggestion-error">
                    <p>❌ {suggestionError}</p>
                  </div>
                )}

                {showAnswerSuggestion && answerSuggestion && (
                  <div className="answer-suggestion-result">
                    <h5>🎯 Suggested Answer</h5>
                    <div className="suggested-answer">
                      <div className="answer-text">
                        <p>{answerSuggestion.suggested_answer}</p>
                      </div>
                      
                      <div className="suggestion-meta">
                        <div className="confidence-score">
                          <span className="label">Confidence:</span>
                          <span className={`confidence-value ${answerSuggestion.confidence > 0.7 ? 'high' : answerSuggestion.confidence > 0.4 ? 'medium' : 'low'}`}>
                            {Math.round(answerSuggestion.confidence * 100)}%
                          </span>
                        </div>
                        <div className="source-info">
                          <span className="label">Based on:</span>
                          <span className="value">{answerSuggestion.source_messages} chat messages</span>
                        </div>
                      </div>

                      {answerSuggestion.key_points && answerSuggestion.key_points.length > 0 && (
                        <div className="key-points">
                          <h6>🔑 Key Points from Chat:</h6>
                          <ul>
                            {answerSuggestion.key_points.map((point, index) => (
                              <li key={index}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {answerSuggestion.evidence_from_chat && answerSuggestion.evidence_from_chat.length > 0 && (
                        <div className="evidence-section">
                          <h6>📝 Supporting Evidence from Chat:</h6>
                          {answerSuggestion.evidence_from_chat.map((evidence, index) => (
                            <div key={index} className="evidence-item">
                              <div className="evidence-author">{evidence.author}:</div>
                              <div className="evidence-message">"{evidence.message}"</div>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="suggestion-actions-bottom">
                        <button 
                          onClick={() => copyToClipboard(answerSuggestion.suggested_answer)}
                          className="copy-answer-btn"
                        >
                          📋 Copy Answer
                        </button>
                        <button 
                          onClick={() => copyToClipboard(`Question: ${questionInput}\n\nSuggested Answer: ${answerSuggestion.suggested_answer}\n\nConfidence: ${Math.round(answerSuggestion.confidence * 100)}%`)}
                          className="copy-full-btn"
                        >
                          📄 Copy Full Response
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="analysis-footer">
        <p>Analysis completed • {chatData?.messages?.length || 0} messages processed</p>
      </div>
    </div>
  );
};

export default ActiveChatAnalysisPage;