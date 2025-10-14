import React, {useState, useEffect} from 'react'
import axios from 'axios'

export default function ProjectModal({project, onClose, onSaved}){
  const [cover, setCover] = useState(project.cover_letter || '')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('zephyr') // general | local | openai | deepseak | ollama | zephyr
  const [loadingText, setLoadingText] = useState('Generating...')

  // Load scraped jobs when modal opens
  useEffect(() => {
    // Remove scraped jobs loading since we don't need browse functionality anymore
  }, [])

  // Remove scraped jobs functions since we don't need browse functionality
  // Jobs are now saved directly from NotificationPush component

  const generate = async ()=>{
    setLoading(true)
    const modelNames = {
      general: 'General AI',
      local: 'Local Gemma 2B',
      openai: 'OpenAI GPT',
      deepseak: 'DeepSeek',
      ollama: 'Ollama Mistral 7B',
      zephyr: 'T5 Cover Genie (Specialized)'
    }
    setLoadingText(`Generating with ${modelNames[mode] || 'AI'} model...`)
    
    if (mode === 'zephyr') {
      // Use new Django AI endpoint instead of old Zephyr API proxy
      try {
        const res = await axios.post('/api/ai/generate-cover-letter/', {
          job_title: project.title,
          company_name: project.client || '',
          job_description: project.description || '',
          skills: project.skills_required || 'Python, React, JavaScript'
        })
        
        if (res.data && res.data.success) {
          setCover(res.data.cover_letter)
          onSaved({...project, cover_letter: res.data.cover_letter, status: 'proposal_ready'})
        } else {
          // Show error in textarea instead of just loading text
          const errorMessage = res.data?.error || 'AI Cover Letter generation failed. Please try again.'
          setCover(`Error: ${errorMessage}`)
          setLoadingText('T5 Cover Genie generation failed. Please try again.')
          setTimeout(() => setLoadingText('Generating...'), 3000)
        }
      } catch (error) {
        setLoadingText('Django AI endpoint connection failed. Please ensure backend is running on port 8000.')
        setTimeout(() => setLoadingText('Generating...'), 3000)
      }
    } else {
      // Use existing Django backend
      const res = await axios.post(`/api/projects/${project.id}/generate_cover/`, {skills: project.skills_required, mode}).catch(()=>null)
      if(res && res.data){
        setCover(res.data.cover_letter)
        onSaved({...project, cover_letter: res.data.cover_letter, status: 'proposal_ready'})
      } else {
        setLoadingText('Generation failed. Please try again.')
        setTimeout(() => setLoadingText('Generating...'), 3000)
      }
    }
    setLoading(false)
  }

  const sendToMonday = async ()=>{
    setLoading(true)
    const res = await axios.post(`/api/projects/${project.id}/send_to_monday/`, {assignee: 'writer'}).catch(()=>null)
    setLoading(false)
    if(res && res.data){
      onSaved({...project, status: 'accepted'})
      onClose()
    }
  }

  return (
    <div style={{position:'fixed',left:20,right:20,top:20,bottom:20,background:'#fff',padding:20,overflow:'auto',border:'1px solid #ccc'}}>
      <div style={{position: 'relative', height: '100%'}}>
        <button onClick={onClose} style={{float: 'right'}}>✕ Close</button>
        
        {/* Remove browse controls since jobs are saved directly from NotificationPush */}

        {/* Standard Project View - no more dual mode needed */}
        <div>
          <h2>{project.title}</h2>
            <p><strong>Client:</strong> {project.client}</p>
            {project.url && <p><strong>URL:</strong> <a href={project.url} target="_blank" rel="noopener noreferrer">{project.url}</a></p>}
            <p><strong>Budget:</strong> {project.budget}</p>
            <p><strong>Description:</strong></p>
            <div style={{whiteSpace:'pre-wrap',border:'1px solid #eee',padding:10}}>{project.description}</div>

            <h3>Cover Letter</h3>
            <div style={{marginBottom:8}}>
              <label style={{marginRight:8}}>Generation mode:</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="general" checked={mode==='general'} onChange={(e)=>setMode(e.target.value)} /> General</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="local" checked={mode==='local'} onChange={(e)=>setMode(e.target.value)} /> Local AI</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="openai" checked={mode==='openai'} onChange={(e)=>setMode(e.target.value)} /> OpenAI</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="deepseak" checked={mode==='deepseak'} onChange={(e)=>setMode(e.target.value)} /> DeepSeak</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="ollama" checked={mode==='ollama'} onChange={(e)=>setMode(e.target.value)} /> Ollama</label>
              <label style={{marginRight:8}}><input type="radio" name="mode" value="zephyr" checked={mode==='zephyr'} onChange={(e)=>setMode(e.target.value)} /> 🤖 T5 Cover Genie</label>
            </div>
            
            {/* Loading UI */}
            {loading && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(255,255,255,0.9)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000
              }}>
                <div style={{
                  width: 40,
                  height: 40,
                  border: '4px solid #f3f3f3',
                  borderTop: '4px solid #3498db',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  marginBottom: 20
                }}></div>
                <h3 style={{margin: 0, color: '#333'}}>{loadingText}</h3>
                <p style={{color: '#666', fontSize: '14px', marginTop: 10}}>
                  AI models may take 10-30 seconds to respond...
                </p>
              </div>
            )}
            
            {/* CSS for spinner animation */}
            <style>
              {`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}
            </style>

            <textarea value={cover} onChange={(e)=>setCover(e.target.value)} rows={8} style={{width:'100%'}} />
            <div style={{marginTop:10}}>
              <button onClick={generate} disabled={loading}>
                {loading ? 'Generating...' : 'Generate cover letter'}
              </button>
              <button onClick={()=>{onSaved({...project, cover_letter:cover}); alert('Saved locally')}} style={{marginLeft:8}}>Save</button>
              <button onClick={sendToMonday} style={{marginLeft:8}}>Send to Monday</button>
            </div>
          </div>
        </div>
      </div>
  )
}