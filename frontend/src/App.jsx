import React, { useState } from 'react'
import ProjectList from './components/ProjectList'
import NotificationPush from './components/NotificationPush'
import MessagePanel from './components/MessagePanel'
import ChatPage from './components/ChatPage'

export default function App(){
  const [currentView, setCurrentView] = useState('dashboard') // 'dashboard' | 'chat'
  const [activeChatId, setActiveChatId] = useState(null)

  const openChat = (chatId) => {
    setActiveChatId(chatId)
    setCurrentView('chat')
  }

  const goBackToDashboard = () => {
    setCurrentView('dashboard')
    setActiveChatId(null)
  }

  if (currentView === 'chat' && activeChatId) {
    return (
      <ChatPage 
        chatId={activeChatId} 
        onBack={goBackToDashboard}
      />
    )
  }

  return (
    <div style={{padding:20}}>
      <h1>UpworkAI Dashboard</h1>
      <ProjectList />
      <MessagePanel onOpenChat={openChat} />
      <NotificationPush />
    </div>
  )
}
