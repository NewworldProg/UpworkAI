import React, {useState} from 'react'
import axios from 'axios'

export default function ManualIngest({onIngested, addAppOutput}){
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [skills, setSkills] = useState('')
  const [budget, setBudget] = useState('')
  const [tosSafe, setTosSafe] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const ingest = async ()=>{
    setLoading(true); setError(null)
    addAppOutput && addAppOutput(`📝 Manual Ingest: Creating project "${title}"`)
    try{
      const payload = { payload: { title, description, skills_required: skills, budget, url, tos_safe: tosSafe }, allow_fetch: false }
      addAppOutput && addAppOutput(`📡 API Call: POST /api/projects/ingest/`)
      const res = await axios.post('/api/projects/ingest/', payload)
      onIngested && onIngested(res.data)
      addAppOutput && addAppOutput(`✅ Project created successfully: ${res.data.title}`)
      setTitle(''); setUrl(''); setDescription(''); setSkills(''); setBudget('')
    }catch(e){
      console.error(e)
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || String(e)
      setError(msg)
      addAppOutput && addAppOutput(`❌ Failed to create project: ${msg}`)
    }
    setLoading(false)
  }

  return (
    <div style={{border:'1px solid #eee',padding:8}}>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
        <input placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
        <input placeholder="Budget" value={budget} onChange={e=>setBudget(e.target.value)} />
        <input placeholder="Project URL (optional)" value={url} onChange={e=>setUrl(e.target.value)} />
        <textarea placeholder="Paste full job description here" value={description} onChange={e=>setDescription(e.target.value)} rows={6} style={{gridColumn:'1 / -1'}} />
  <input placeholder="skills (space or comma separated)" value={skills} onChange={e=>setSkills(e.target.value)} style={{gridColumn:'1 / -1'}} />
        <label style={{gridColumn:'1 / -1'}}><input type="checkbox" checked={tosSafe} onChange={e=>setTosSafe(e.target.checked)} /> I confirm I will paste job text manually (TOS-safe)</label>
      </div>
      <div style={{marginTop:8}}>
        <button onClick={ingest} disabled={!description || loading}>Create Project</button>
        {error && <span style={{color:'red',marginLeft:8}}>{String(error)}</span>}
      </div>
    </div>
  )
}
