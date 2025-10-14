import React, { useState } from 'react'
import ProjectList from './components/ProjectList'
import NotificationPush from './components/NotificationPush'
import MessagePanel from './components/MessagePanel'
import ChatPage from './components/ChatPage'
import ActiveChatAnalysisPage from './components/ActiveChatAnalysisPage'

export default function App(){
  const [currentView, setCurrentView] = useState('dashboard') // 'dashboard' | 'chat' | 'chat-analysis'
  const [activeChatId, setActiveChatId] = useState(null)
  const [chatAnalysisData, setChatAnalysisData] = useState(null)

  const openChat = (chatId) => {
    setActiveChatId(chatId)
    setCurrentView('chat')
  }

  const openChatAnalysis = (analysisData) => {
    setChatAnalysisData(analysisData)
    setCurrentView('chat-analysis')
  }

  const goBackToDashboard = () => {
    setCurrentView('dashboard')
    setActiveChatId(null)
    setChatAnalysisData(null)
  }

  if (currentView === 'chat' && activeChatId) {
    return (
      <ChatPage 
        chatId={activeChatId} 
        onBack={goBackToDashboard}
      />
    )
  }

  if (currentView === 'chat-analysis') {
    return (
      <ActiveChatAnalysisPage 
        chatData={chatAnalysisData?.chatData}
        suggestions={chatAnalysisData?.suggestions}
        onBack={goBackToDashboard}
      />
    )
  }

  return (
    <div style={{padding:20}}>
      <h1>UpworkAI Dashboard</h1>
      <ProjectList />
      <MessagePanel onOpenChat={openChat} onOpenChatAnalysis={openChatAnalysis} />
      <NotificationPush />
    </div>
  )
}
