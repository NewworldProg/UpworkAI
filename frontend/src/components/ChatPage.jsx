import React, { useState, useEffect, useRef } from 'react';
import { openInExternalBrowser } from '../utils/browserUtils';
import './ChatPage.css';

const ChatPage = ({ chatId, onBack }) => {
    const [messages, setMessages] = useState([]);
    const [currentMessage, setCurrentMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [chatInfo, setChatInfo] = useState(null);
    const [aiSuggestions, setAiSuggestions] = useState([]);
    const messagesEndRef = useRef(null);

    // Učitaj poruke za chat
    useEffect(() => {
        if (chatId) {
            loadChatData();
        }
    }, [chatId]);

    // Auto-scroll do dna kad se dodaju nove poruke
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const loadChatData = async () => {
        setIsLoading(true);
        try {
            // Učitaj osnovne informacije o chat-u
            const chatResponse = await fetch(`http://localhost:8000/api/messages/chats/${chatId}/`);
            if (chatResponse.ok) {
                const chatData = await chatResponse.json();
                setChatInfo(chatData.chat || chatData);  // Handle nested response structure
            }

            // Učitaj poruke
            const messagesResponse = await fetch(`http://localhost:8000/api/messages/chats/${chatId}/messages/`);
            if (messagesResponse.ok) {
                const messagesData = await messagesResponse.json();
                setMessages(messagesData.messages || messagesData);  // Handle both response formats
            }

            // Učitaj AI predloge
            const suggestionsResponse = await fetch(`http://localhost:8000/api/messages/chats/${chatId}/ai-suggestions/`);
            if (suggestionsResponse.ok) {
                const suggestionsData = await suggestionsResponse.json();
                setAiSuggestions(suggestionsData.suggestions || []);
            }
        } catch (error) {
            console.error('Greška pri učitavanju chat podataka:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!currentMessage.trim()) return;

        const newMessage = {
            chat_id: chatId,
            content: currentMessage,
            sender: 'Me',
            timestamp: new Date().toISOString(),
            is_outgoing: true
        };

        try {
            setMessages(prev => [...prev, newMessage]);
            setCurrentMessage('');

            // Pošalji poruku na backend
            const response = await fetch(`http://localhost:8000/api/messages/chats/${chatId}/messages/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newMessage)
            });

            if (response.ok) {
                // Osvezi poruke
                loadChatData();
            }
        } catch (error) {
            console.error('Greška pri slanju poruke:', error);
        }
    };

    const useAiSuggestion = (suggestion) => {
        setCurrentMessage(suggestion);
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Tekst kopiran!');
        });
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString('sr-RS', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (isLoading) {
        return (
            <div className="chat-page loading">
                <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Učitavam chat...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="chat-page">
            {/* Header */}
            <div className="chat-header">
                <button className="back-button" onClick={onBack}>
                    ← Nazad
                </button>
                <div className="chat-info">
                    <h2>{chatInfo?.other_participant || 'Chat'}</h2>
                    <p>{chatInfo?.total_messages} poruka | 
                       {chatInfo?.unread_count > 0 && (
                           <span className="unread-badge">{chatInfo.unread_count} nepročitano</span>
                       )}
                    </p>
                </div>
                {chatInfo?.chat_url && (
                    <button 
                        className="open-external-button" 
                        onClick={() => openInExternalBrowser(chatInfo.chat_url)}
                        title="Otvori u Chrome"
                    >
                        🌐 Chrome
                    </button>
                )}
            </div>

            <div className="chat-content">
                {/* AI Suggestions Panel */}
                {aiSuggestions.length > 0 && (
                    <div className="ai-suggestions">
                        <h3>🤖 AI Predlozi</h3>
                        <div className="suggestions-list">
                            {aiSuggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    className="suggestion-btn"
                                    onClick={() => useAiSuggestion(suggestion)}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Messages Area */}
                <div className="messages-container">
                    <div className="messages-list">
                        {messages.map((message, index) => (
                            <div 
                                key={index} 
                                className={`message ${message.is_outgoing ? 'outgoing' : 'incoming'}`}
                            >
                                <div className="message-header">
                                    <span className="sender">{message.sender}</span>
                                    <span className="timestamp">{formatTimestamp(message.timestamp)}</span>
                                    <button 
                                        className="copy-btn"
                                        onClick={() => copyToClipboard(message.content)}
                                        title="Kopiraj poruku"
                                    >
                                        📋
                                    </button>
                                </div>
                                <div className="message-content">
                                    {message.content}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Message Input */}
                <div className="message-input-area">
                    <div className="input-container">
                        <textarea
                            value={currentMessage}
                            onChange={(e) => setCurrentMessage(e.target.value)}
                            placeholder="Ukucaj poruku..."
                            className="message-input"
                            rows="3"
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                        />
                        <div className="input-actions">
                            <button 
                                className="send-btn"
                                onClick={sendMessage}
                                disabled={!currentMessage.trim()}
                            >
                                Pošalji 📤
                            </button>
                            <button 
                                className="ai-help-btn"
                                onClick={loadChatData}
                                title="Osvezi AI predloge"
                            >
                                🤖 AI Pomoć
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatPage;