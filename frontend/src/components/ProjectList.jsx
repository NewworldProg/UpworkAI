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
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [hasPrevious, setHasPrevious] = useState(false)
  const [loading, setLoading] = useState(false)
  
  const jobsPerPage = 20

  // Load jobs from notification-push database
  const loadJobs = async (page = 1) => {
    setLoading(true)
    try {
      const offset = (page - 1) * jobsPerPage
      const res = await axios.get(`/api/notification-push/jobs/all/?limit=${jobsPerPage}&offset=${offset}`)
      
      if (res.data.success) {
        // Convert notification-push jobs to project format
        const convertedJobs = res.data.jobs.map(job => ({
          id: job.id,
          title: job.title,
          client: job.client_name,
          budget: job.budget || 'Not specified',
          description: job.description,
          job_url: job.job_url,
          scraped_at: job.scraped_at,
          match_score: null // This will be calculated later if needed
        }))
        
        setProjects(convertedJobs)
        setTotalCount(res.data.total_count)
        setHasNext(res.data.has_next)
        setHasPrevious(res.data.has_previous)
        setCurrentPage(page)
      }
    } catch(e) {
      console.error('Failed to load jobs from database:', e.message)
      // Fallback to original projects API
      try {
        const res = await axios.get('/api/projects/')
        setProjects(res.data)
      } catch(fallbackError) {
        console.error('Failed to load projects fallback:', fallbackError.message)
      }
    }
    setLoading(false)
  }

  useEffect(() => {
    loadJobs(1)
  }, [])

  const doSearch = async (skillsStr)=>{
    try{
      const res = await axios.post('/api/projects/search/', { skills: skillsStr })
      setProjects(res.data)
      // Reset pagination when searching
      setCurrentPage(1)
      setTotalCount(res.data.length)
      setHasNext(false)
      setHasPrevious(false)
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

  const handlePreviousPage = () => {
    if (hasPrevious && currentPage > 1) {
      loadJobs(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (hasNext) {
      loadJobs(currentPage + 1)
    }
  }

  const totalPages = Math.ceil(totalCount / jobsPerPage)

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
            <button onClick={() => loadJobs(1)} style={{marginLeft: 10}}>
              Load All Jobs
            </button>
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

      {/* Pagination Info */}
      <div style={{marginBottom: 10, padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4}}>
        <span>
          Showing {projects.length} of {totalCount} total jobs 
          {totalPages > 1 && ` (Page ${currentPage} of ${totalPages})`}
          {loading && ' - Loading...'}
        </span>
      </div>

      <table width="100%" border="1" cellPadding="8">
        <thead>
          <tr>
            <th>Title</th>
            <th>Client</th>
            <th>Budget</th>
            <th>Score</th>
            <th>Scraped At</th>
          </tr>
        </thead>
        <tbody>
          {projects.map(p=> (
            <tr key={p.id} onClick={()=>setSelected(p)} style={{cursor:'pointer'}}>
              <td>{p.title}</td>
              <td>{p.client}</td>
              <td>{p.budget}</td>
              <td>{p.match_score ?? '-'}</td>
              <td>{p.scraped_at ? new Date(p.scraped_at).toLocaleDateString() : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{marginTop: 15, textAlign: 'center'}}>
          <button 
            onClick={handlePreviousPage} 
            disabled={!hasPrevious || loading}
            style={{marginRight: 10, padding: '8px 16px'}}
          >
            ← Previous
          </button>
          
          <span style={{margin: '0 15px', fontWeight: 'bold'}}>
            Page {currentPage} of {totalPages}
          </span>
          
          <button 
            onClick={handleNextPage} 
            disabled={!hasNext || loading}
            style={{marginLeft: 10, padding: '8px 16px'}}
          >
            Next →
          </button>
        </div>
      )}

      {selected && <ProjectModal project={selected} onClose={()=>setSelected(null)} onSaved={(updated)=>{
        setProjects(ps=>ps.map(p=> p.id===updated.id? updated: p));
        setSelected(updated);
      }} />}
    </div>
  )
}
