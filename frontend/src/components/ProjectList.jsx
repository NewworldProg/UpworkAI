import React, {useEffect, useState} from 'react'
import axios from 'axios'
import ProjectModal from './ProjectModal'
import SkillsInput from './SkillsInput'
import SkillsetsPanel from './SkillsetsPanel'
import ManualIngest from './ManualIngest'

export default function ProjectList(){
  const [projects, setProjects] = useState([])
  const [selected, setSelected] = useState(null)
  const [mode, setMode] = useState('manual') // 'manual' or 'saved'
  const [skills, setSkills] = useState([])

  useEffect(()=>{
    axios.get('/api/projects/').then(r=>{
      setProjects(r.data)
    }).catch((e)=>{
      console.error('Failed to load projects:', e.message)
    })
  },[])

  const doSearch = async (skillsStr)=>{
    try{
      const res = await axios.post('/api/projects/search/', { skills: skillsStr })
      setProjects(res.data)
    }catch(e){
      console.error('Error searching projects:', e.message)
    }
  }

  const onUseSkillset = (skillset)=>{
    doSearch(skillset.skills)
  }

  const onManualSearch = ()=>{
    doSearch(skills.join(','))
  }

  return (
    <div>
      <div style={{marginBottom:12}}>
        <label style={{marginRight:8}}>Mode:</label>
        <select value={mode} onChange={e=>setMode(e.target.value)}>
          <option value="manual">Manual Search / Ingest</option>
          <option value="saved">Search by Saved Skillset</option>
        </select>
      </div>

      {mode==='manual' ? (
        <div style={{marginBottom:12}}>
          <div style={{display:'flex',alignItems:'center',gap:8}}>
            <SkillsInput value={skills} onChange={setSkills} />
            <button onClick={onManualSearch}>Search</button>
          </div>
          <div style={{marginTop:12}}>
            <ManualIngest onIngested={(p)=> {
              setProjects(ps=>[p,...ps]);
            }} />
          </div>
        </div>
      ) : (
        <div style={{marginBottom:12}}>
          <SkillsetsPanel onSelect={onUseSkillset} />
        </div>
      )}
      <table width="100%" border="1" cellPadding="8">
        <thead>
          <tr><th>Title</th><th>Client</th><th>Budget</th><th>Score</th></tr>
        </thead>
        <tbody>
          {projects.map(p=> (
            <tr key={p.id} onClick={()=>setSelected(p)} style={{cursor:'pointer'}}>
              <td>{p.title}</td>
              <td>{p.client}</td>
              <td>{p.budget}</td>
              <td>{p.match_score ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected && <ProjectModal project={selected} onClose={()=>setSelected(null)} onSaved={(updated)=>{
        setProjects(ps=>ps.map(p=> p.id===updated.id? updated: p));
        setSelected(updated);
      }} />}
    </div>
  )
}
