import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function NotificationPush() {
  const [jobs, setJobs] = useState([])
  const [isBrowserOpen, setIsBrowserOpen] = useState(false)
  const [status, setStatus] = useState('disconnected')
  const [keywords, setKeywords] = useState('javascript,react,node.js')
  const [profileId, setProfileId] = useState('')
  const [logs, setLogs] = useState([])
  const [selectedJobs, setSelectedJobs] = useState(new Set())
  const [savingJobs, setSavingJobs] = useState(false)
  const [existingJobTitles, setExistingJobTitles] = useState(new Set())
  
  // Message scraping state
  const [messages, setMessages] = useState([])
  const [scrapingMessages, setScrapingMessages] = useState(false)

  // Check status on mount
  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const response = await axios.get('/api/notification-push/status/')
      setStatus(response.data.status)
      setIsBrowserOpen(response.data.is_running)
      setKeywords(response.data.keywords || keywords)
      addLog('info', `Status: ${response.data.status} (${response.data.jobs_count} jobs captured)`)
    } catch (error) {
      setStatus('error')
      addLog('error', `Failed to check status: ${error.message}`)
    }
  }

  const openBrowser = async () => {
    try {
      setIsBrowserOpen(true)
      const response = await axios.post('/api/notification-push/start/', {
        keywords: keywords,
        profileId: profileId
      })
      
      if (response.data.success) {
        setStatus('monitoring')
        addLog('success', response.data.message)
      } else {
        setIsBrowserOpen(false)
        addLog('error', response.data.message)
      }
    } catch (error) {
      setIsBrowserOpen(false)
      addLog('error', `Failed to start browser: ${error.message}`)
    }
  }

  const closeBrowser = async () => {
    try {
      const response = await axios.post('/api/notification-push/stop/')
      setIsBrowserOpen(false)
      setStatus('connected')
      addLog('info', response.data.message || 'Browser closed')
    } catch (error) {
      addLog('error', `Failed to close browser: ${error.message}`)
    }
  }

  const manualScrape = async () => {
    try {
      addLog('info', 'Manual scrape (logged-in) triggered')
      const response = await axios.post('/api/notification-push/manual-scrape/')
      addLog('info', response.data.message || 'Manual scrape triggered')
      // Refresh jobs after manual scrape
      setTimeout(fetchJobs, 2000)
    } catch (error) {
      addLog('error', `Manual scrape failed: ${error.message}`)
    }
  }

  const universalScrape = async () => {
    try {
      addLog('info', 'Universal DOM scrape triggered')
      const response = await axios.post('/api/notification-push/universal-scrape/')
      addLog('info', response.data.message || 'Universal scrape triggered')
      // Refresh jobs after universal scrape
      setTimeout(fetchJobs, 2000)
    } catch (error) {
      addLog('error', `Universal scrape failed: ${error.message}`)
    }
  }

  const scrapeMessages = async () => {
    try {
      setScrapingMessages(true)
      addLog('info', 'Extracting Upwork messages/notifications...')
      
      // Start extraction process
      const extractResponse = await axios.post('/api/messages/extract/')
      
      if (extractResponse.data.success) {
        addLog('info', 'Message extraction started in background...')
        
        // Wait a bit for extraction to complete, then fetch messages
        setTimeout(async () => {
          try {
            const messagesResponse = await axios.get('/api/messages/messages/')
            const extractedMessages = messagesResponse.data || []
            setMessages(extractedMessages)
            addLog('success', `✅ Extracted ${extractedMessages.length} messages from Upwork`)
            
            // Log message details
            if (extractedMessages.length > 0) {
              extractedMessages.slice(0, 3).forEach((msg, index) => {
                addLog('info', `Message ${index + 1}: ${msg.sender} - ${msg.preview.substring(0, 50)}...`)
              })
              if (extractedMessages.length > 3) {
                addLog('info', `... and ${extractedMessages.length - 3} more messages`)
              }
            }
          } catch (fetchError) {
            addLog('error', `Failed to fetch extracted messages: ${fetchError.message}`)
          } finally {
            setScrapingMessages(false)
          }
        }, 5000) // Wait 5 seconds for extraction to complete
        
      } else {
        addLog('error', `Message extraction failed: ${extractResponse.data.message}`)
        setScrapingMessages(false)
      }
    } catch (error) {
      addLog('error', `Message extraction failed: ${error.message}`)
      setScrapingMessages(false)
    }
  }

  const refreshChromeStatus = async () => {
    try {
      addLog('info', 'Refreshing Chrome status...')
      const response = await axios.post('/api/notification-push/refresh/')
      addLog('success', response.data.message)
      // Refresh status after refreshing Chrome
      setTimeout(checkStatus, 1000)
    } catch (error) {
      addLog('error', `Failed to refresh Chrome status: ${error.message}`)
    }
  }

  const fetchJobs = async () => {
    try {
      const response = await axios.get('/api/notification-push/jobs/')
      setJobs(response.data.jobs || [])
      addLog('info', `Fetched ${response.data.jobs?.length || 0} jobs`)
      
      // Also check which jobs already exist in database
      checkExistingJobs(response.data.jobs || [])
    } catch (error) {
      addLog('error', `Failed to fetch jobs: ${error.message}`)
    }
  }

  const checkExistingJobs = async (currentJobs) => {
    try {
      const existingProjectsResponse = await axios.get('/api/projects/')
      const existingTitles = new Set(
        existingProjectsResponse.data.map(project => project.title.toLowerCase().trim())
      )
      setExistingJobTitles(existingTitles)
      
      const duplicateCount = currentJobs.filter(job => 
        existingTitles.has((job.title || '').toLowerCase().trim())
      ).length
      
      if (duplicateCount > 0) {
        addLog('info', `Found ${duplicateCount} jobs already in database`)
      }
    } catch (error) {
      addLog('warning', `Could not check for existing jobs: ${error.message}`)
    }
  }

  const addLog = (level, message) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev.slice(-19), { // Keep last 20 logs
      timestamp,
      level,
      message
    }])
  }

  const saveJobsToDatabase = async (jobsToSave = null) => {
    try {
      setSavingJobs(true)
      const jobs_data = jobsToSave || jobs.filter((_, index) => selectedJobs.has(index))
      
      if (jobs_data.length === 0) {
        addLog('warning', 'No jobs selected to save')
        return
      }

      // First, get existing projects to check for duplicates
      addLog('info', 'Checking for duplicate jobs...')
      const existingProjectsResponse = await axios.get('/api/projects/')
      const existingTitles = new Set(
        existingProjectsResponse.data.map(project => project.title.toLowerCase().trim())
      )

      let saved_count = 0
      let skipped_count = 0
      
      for (const job of jobs_data) {
        const jobTitle = (job.title || 'Untitled Job').toLowerCase().trim()
        
        // Check if job already exists in database
        if (existingTitles.has(jobTitle)) {
          skipped_count++
          addLog('info', `Skipped duplicate: ${job.title}`)
          continue
        }
        
        try {
          // Create project from scraped job
          const project_data = {
            title: job.title || 'Untitled Job',
            client: job.client || (job.url?.includes('upwork.com') ? 'Upwork Client' : 'Unknown Client'),
            budget: job.budget || 'Budget not specified',
            description: job.description || 'No description available',
            url: job.url || '',
            skills_required: job.skills_required || '',
            status: 'scraped',
            tos_safe: true,
            fetch_method: 'scrape'
          }
          
          const response = await axios.post('/api/projects/', project_data)
          if (response.status === 201) {
            saved_count++
            // Add to existing titles set to prevent duplicates in this batch
            existingTitles.add(jobTitle)
            addLog('success', `Saved: ${job.title}`)
          }
        } catch (error) {
          if (error.response?.status === 400 && error.response?.data?.title?.[0]?.includes('already exists')) {
            skipped_count++
            addLog('info', `Skipped duplicate: ${job.title}`)
          } else {
            addLog('error', `Failed to save: ${job.title} - ${error.response?.data?.detail || error.message}`)
          }
        }
      }
      
      addLog('success', `Database save completed: ${saved_count} saved, ${skipped_count} skipped`)
      
      // Clear selection after successful save
      setSelectedJobs(new Set())
      
    } catch (error) {
      addLog('error', `Database save failed: ${error.message}`)
    } finally {
      setSavingJobs(false)
    }
  }

  const toggleJobSelection = (index) => {
    setSelectedJobs(prev => {
      const newSelection = new Set(prev)
      if (newSelection.has(index)) {
        newSelection.delete(index)
      } else {
        newSelection.add(index)
      }
      return newSelection
    })
  }

  const selectAllJobs = () => {
    // Only select jobs that are not already in the database
    const newJobIndices = jobs
      .map((job, index) => ({ job, index }))
      .filter(({ job }) => !existingJobTitles.has((job.title || '').toLowerCase().trim()))
      .map(({ index }) => index)
    
    setSelectedJobs(new Set(newJobIndices))
  }

  const clearSelection = () => {
    setSelectedJobs(new Set())
  }

  const getStatusColor = () => {
    switch (status) {
      case 'monitoring': return '#007bff'
      case 'connected': return '#28a745'
      case 'error': return '#dc3545'
      default: return '#6c757d'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'monitoring': return '🔵 Chrome Running'
      case 'connected': return '🟢 Ready'
      case 'error': return '🔴 Error'
      default: return '⚫ Disconnected'
    }
  }

  return (
    <div style={{
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px',
      backgroundColor: '#f8f9fa',
      maxWidth: '800px'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, color: '#333' }}>
          🌐 Upwork Job Scraper
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ 
            color: getStatusColor(), 
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            {getStatusText()}
          </span>
          <button
            onClick={checkStatus}
            style={{
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              padding: '5px 10px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🔄 Refresh Status
          </button>
        </div>
      </div>

      {/* Configuration */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>⚙️ Configuration</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <div>
            <label style={{ fontSize: '13px', color: '#666', display: 'block', marginBottom: '5px' }}>
              Search Keywords (comma separated):
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              style={{ 
                width: '100%', 
                padding: '8px', 
                fontSize: '13px', 
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              disabled={isBrowserOpen}
              placeholder="javascript,react,node.js,python"
            />
          </div>
          <div>
            <label style={{ fontSize: '13px', color: '#666', display: 'block', marginBottom: '5px' }}>
              Profile ID (optional):
            </label>
            <input
              type="text"
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
              style={{ 
                width: '100%', 
                padding: '8px', 
                fontSize: '13px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              disabled={isBrowserOpen}
              placeholder="1"
            />
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>🎮 Controls</h4>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {!isBrowserOpen ? (
            <button 
              onClick={openBrowser}
              style={{
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                padding: '10px 15px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              🚀 Open Chrome Browser
            </button>
          ) : (
            <button 
              onClick={closeBrowser}
              style={{
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                padding: '10px 15px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              ⏹️ Close Browser
            </button>
          )}
          
          <button 
            onClick={refreshChromeStatus}
            style={{
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            🔄 Refresh Chrome Status
          </button>
          
          <button 
            onClick={manualScrape}
            disabled={!isBrowserOpen}
            style={{
              backgroundColor: isBrowserOpen ? '#28a745' : '#6c757d',
              color: 'white',
              border: 'none',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: isBrowserOpen ? 'pointer' : 'not-allowed',
              fontSize: '14px'
            }}
          >
            🔍 Manual Scrape (Logged-in)
          </button>
          
          <button 
            onClick={universalScrape}
            disabled={!isBrowserOpen}
            style={{
              backgroundColor: isBrowserOpen ? '#ff9500' : '#6c757d',
              color: 'white',
              border: 'none',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: isBrowserOpen ? 'pointer' : 'not-allowed',
              fontSize: '14px'
            }}
          >
            🌐 Universal Scrape (Any Page)
          </button>

          <button 
            onClick={scrapeMessages}
            disabled={!isBrowserOpen || scrapingMessages}
            style={{
              backgroundColor: (!isBrowserOpen || scrapingMessages) ? '#6c757d' : '#e83e8c',
              color: 'white',
              border: 'none',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: (!isBrowserOpen || scrapingMessages) ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            {scrapingMessages ? '📬 Extracting...' : '📬 Extract Messages'}
          </button>
          
          <button 
            onClick={fetchJobs}
            style={{
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📋 Load Jobs
          </button>
        </div>
      </div>

      {/* Instructions */}
      {isBrowserOpen && (
        <div style={{ 
          backgroundColor: '#d1ecf1', 
          border: '1px solid #bee5eb', 
          borderRadius: '5px', 
          padding: '10px', 
          marginBottom: '20px',
          fontSize: '13px'
        }}>
          <strong>📋 Instructions:</strong>
          <ol style={{ margin: '5px 0 0 0', paddingLeft: '20px' }}>
            <li>Chrome browser should now be open with Upwork login page</li>
            <li>Manually login to your Upwork account</li>
            <li>Navigate to any page you want to scrape</li>
            <li><strong>Manual Scrape (Logged-in):</strong> For Upwork job pages when logged in</li>
            <li><strong>Universal Scrape (Any Page):</strong> For any page content (works without login)</li>
            <li><strong>Extract Messages:</strong> Extract messages/notifications from your Upwork account (requires login)</li>
            <li>Use "Load Jobs" to refresh the captured jobs list</li>
          </ol>
        </div>
      )}

      {/* Jobs Display */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h4 style={{ margin: 0, fontSize: '16px' }}>💼 Captured Jobs ({jobs.length})</h4>
          
          {jobs.length > 0 && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#666' }}>
                {selectedJobs.size}/{jobs.length - Array.from(existingJobTitles).filter(title => 
                  jobs.some(job => (job.title || '').toLowerCase().trim() === title)
                ).length} selected ({Array.from(existingJobTitles).filter(title => 
                  jobs.some(job => (job.title || '').toLowerCase().trim() === title)
                ).length} already in DB)
              </span>
              
              <button
                onClick={selectAllJobs}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontSize: '11px'
                }}
              >
                Select All New
              </button>
              
              <button
                onClick={clearSelection}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontSize: '11px'
                }}
              >
                Clear
              </button>
              
              <button
                onClick={() => saveJobsToDatabase(jobs)}
                disabled={savingJobs}
                style={{
                  backgroundColor: savingJobs ? '#95a5a6' : '#28a745',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '3px',
                  cursor: savingJobs ? 'not-allowed' : 'pointer',
                  fontSize: '11px',
                  opacity: savingJobs ? 0.7 : 1
                }}
              >
                {savingJobs ? '💾 Saving...' : '💾 Save Selected'}
              </button>
              
              <button
                onClick={() => saveJobsToDatabase()}
                disabled={savingJobs || selectedJobs.size === 0}
                style={{
                  backgroundColor: savingJobs || selectedJobs.size === 0 ? '#95a5a6' : '#007bff',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '3px',
                  cursor: savingJobs || selectedJobs.size === 0 ? 'not-allowed' : 'pointer',
                  fontSize: '11px',
                  opacity: savingJobs || selectedJobs.size === 0 ? 0.7 : 1
                }}
              >
                {savingJobs ? '💾 Saving...' : '💾 Save Selected'}
              </button>
            </div>
          )}
        </div>
        <div style={{
          maxHeight: '250px',
          overflowY: 'auto',
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '5px',
          padding: '10px'
        }}>
          {jobs.length === 0 ? (
            <div style={{ color: '#666', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
              No jobs captured yet. Start the browser and use manual scraping.
            </div>
          ) : (
            jobs.map((job, index) => {
              const isExisting = existingJobTitles.has((job.title || '').toLowerCase().trim())
              return (
                <div key={index} style={{
                  borderBottom: index < jobs.length - 1 ? '1px solid #eee' : 'none',
                  paddingBottom: '10px',
                  marginBottom: '10px',
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  backgroundColor: isExisting ? '#fff8dc' : 'transparent', // Light yellow for existing jobs
                  padding: '10px',
                  borderRadius: '4px',
                  border: isExisting ? '1px solid #f0e68c' : 'none'
                }}>
                  {/* Checkbox for individual selection */}
                  <input
                    type="checkbox"
                    checked={selectedJobs.has(index)}
                    onChange={() => toggleJobSelection(index)}
                    disabled={isExisting}
                    style={{
                      marginTop: '2px',
                      cursor: isExisting ? 'not-allowed' : 'pointer',
                      opacity: isExisting ? 0.5 : 1
                    }}
                  />
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontWeight: 'bold', 
                      color: isExisting ? '#b8860b' : '#007bff', 
                      marginBottom: '5px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      {job.url ? (
                        <a href={job.url} target="_blank" rel="noopener noreferrer" style={{ 
                          textDecoration: 'none', 
                          color: isExisting ? '#b8860b' : '#007bff' 
                        }}>
                          {job.title}
                        </a>
                      ) : (
                        job.title
                      )}
                      {isExisting && (
                        <span style={{
                          fontSize: '10px',
                          backgroundColor: '#ddd',
                          color: '#666',
                          padding: '2px 6px',
                          borderRadius: '10px',
                          fontWeight: 'normal'
                        }}>
                          Already in Database
                        </span>
                      )}
                    </div>
                    <div style={{ color: '#666', marginBottom: '5px', lineHeight: '1.4' }}>
                      {job.description}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#999' }}>
                      <span>💰 {job.budget || 'Budget not specified'}</span>
                      <span>🕒 {job.timestamp ? new Date(job.timestamp).toLocaleString() : 'Unknown time'}</span>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Messages Display */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h4 style={{ margin: 0, fontSize: '16px' }}>📬 Extracted Messages ({messages.length})</h4>
        </div>
        
        <div style={{
          maxHeight: '300px',
          overflowY: 'auto',
          border: '1px solid #ddd',
          borderRadius: '4px',
          padding: '10px'
        }}>
          {messages.length === 0 ? (
            <div style={{ color: '#666', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
              No messages extracted yet. Use "Extract Messages" to scan Upwork notifications.
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={message.id || index} style={{
                borderBottom: index < messages.length - 1 ? '1px solid #eee' : 'none',
                paddingBottom: '10px',
                marginBottom: '10px',
                fontSize: '13px'
              }}>
                <div style={{ 
                  fontWeight: 'bold', 
                  color: '#007bff', 
                  marginBottom: '5px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>👤 {message.sender || 'Unknown Sender'}</span>
                  <span style={{
                    fontSize: '10px',
                    color: '#999',
                    backgroundColor: message.isRead ? '#d4edda' : '#fff3cd',
                    padding: '2px 6px',
                    borderRadius: '10px',
                    border: message.isRead ? '1px solid #c3e6cb' : '1px solid #ffeaa7'
                  }}>
                    {message.isRead ? '✓ Read' : '● Unread'}
                  </span>
                </div>
                
                {message.preview && (
                  <div style={{ 
                    color: '#666', 
                    marginBottom: '5px', 
                    lineHeight: '1.4',
                    fontStyle: 'italic'
                  }}>
                    "{message.preview}"
                  </div>
                )}
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#999' }}>
                  <span>🕒 {message.messageTime || message.timestamp || 'Unknown time'}</span>
                  {message.conversationId && (
                    <span>📋 ID: {message.conversationId}</span>
                  )}
                </div>
                
                {/* Debug info - can be removed later */}
                {message.selector_used && (
                  <div style={{ 
                    fontSize: '10px', 
                    color: '#888', 
                    marginTop: '5px',
                    fontFamily: 'monospace'
                  }}>
                    Extracted via: {message.selector_used}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Logs */}
      <div>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>💻 Activity Logs</h4>
        <div style={{
          maxHeight: '150px',
          overflowY: 'auto',
          backgroundColor: '#1e1e1e',
          color: '#00ff00',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: '11px',
          padding: '10px',
          borderRadius: '5px',
          border: '1px solid #333'
        }}>
          {logs.map((log, index) => (
            <div key={index} style={{ marginBottom: '2px' }}>
              <span style={{ color: '#888' }}>[{log.timestamp}]</span>{' '}
              <span style={{ 
                color: log.level === 'error' ? '#ff4444' : 
                      log.level === 'success' ? '#00ff00' : 
                      log.level === 'info' ? '#00aaff' : '#ffaa00' 
              }}>
                {log.level.toUpperCase()}
              </span>: {log.message}
            </div>
          ))}
          
          {logs.length === 0 && (
            <div style={{ color: '#666' }}>
              Waiting for activity...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}