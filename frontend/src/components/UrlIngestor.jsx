import React, {useState} from 'react'
import axios from 'axios'

export default function UrlIngestor({onIngested}){
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [allowFetch, setAllowFetch] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const extract = async ()=>{
    setLoading(true)
    try{
      const res = await axios.post('/api/projects/extract_text/', { payload: { url }, allow_fetch: allowFetch })
      setText(res.data.text)
      setError(null)
    }catch(e){
      console.error(e)
      const msg = e?.response?.data?.detail || e?.message || String(e)
      setError(msg)
    }
    setLoading(false)
  }

  const ingest = async ()=>{
    setLoading(true)
    try{
      const payload = { payload: { url }, allow_fetch: allowFetch }
      const res = await axios.post('/api/projects/ingest/', payload)
      onIngested && onIngested(res.data)
      setUrl(''); setText('')
    }catch(e){ console.error(e); alert('Ingest failed') }
    setLoading(false)
  }

  return (
    <div style={{border:'1px solid #eee',padding:8}}>
      <div style={{display:'flex',gap:8,alignItems:'center'}}>
        <input placeholder="https://..." value={url} onChange={e=>setUrl(e.target.value)} style={{width:400}} />
        <label><input type="checkbox" checked={allowFetch} onChange={e=>setAllowFetch(e.target.checked)} /> allow fetch</label>
        <button onClick={extract} disabled={!url || loading}>Extract</button>
        <button onClick={ingest} disabled={!url || loading}>Ingest</button>
      </div>
      <div style={{marginTop:8}}>
        <textarea value={text} readOnly rows={8} style={{width:'100%'}} />
        {error && <div style={{color:'red',marginTop:8}}>Error: {String(error)}</div>}
      </div>
    </div>
  )
}
