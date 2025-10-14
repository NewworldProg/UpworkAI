import React, {useEffect, useState} from 'react'
import axios from 'axios'

export default function SkillsetsPanel({onSelect}){
  const [skillsets, setSkillsets] = useState([])
  const [name, setName] = useState('')
  const [skills, setSkills] = useState('')

  const load = async ()=>{
    try{
      const res = await axios.get('/api/skillsets/')
      setSkillsets(res.data)
    }catch(e){console.error(e)}
  }

  useEffect(()=>{ load() },[])

  const create = async ()=>{
    try{
      await axios.post('/api/skillsets/', { name, skills })
      setName(''); setSkills('')
      load()
    }catch(e){console.error(e)}
  }

  const remove = async (id)=>{
    try{
      await axios.delete(`/api/skillsets/${id}/`)
      load()
    }catch(e){console.error(e)}
  }

  return (
    <div style={{border:'1px solid #eee',padding:8}}>
      <h4>Saved skillsets</h4>
      <div style={{display:'flex',gap:8}}>
        <input placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
        <input placeholder="skills (comma)" value={skills} onChange={e=>setSkills(e.target.value)} style={{width:300}} />
        <button onClick={create}>Create</button>
      </div>
      <div style={{marginTop:8}}>
        {skillsets.map(s=> (
          <div key={s.id} style={{display:'flex',justifyContent:'space-between',padding:6,borderBottom:'1px solid #f0f0f0'}}>
            <div>
              <strong>{s.name}</strong>
              <div style={{color:'#666'}}>{s.skills}</div>
            </div>
            <div>
              <button onClick={()=> onSelect && onSelect(s)}>Use</button>
              <button onClick={()=>remove(s.id)} style={{marginLeft:8}}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
