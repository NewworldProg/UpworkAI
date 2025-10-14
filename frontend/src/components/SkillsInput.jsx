import React, {useState, useEffect} from 'react'

export default function SkillsInput({value, onChange}){
  // value may be array or string
  const [text, setText] = useState(Array.isArray(value)? value.join(' '): (value||''))

  useEffect(()=>{
    setText(Array.isArray(value)? value.join(' '): (value||''))
  },[value])

  const handleBlur = ()=>{
    // Accept commas, newlines or spaces as separators. Keep multi-word skills when comma is used.
    const raw = text || ''
    const parts = []
    raw.replace(/\r/g,' ').split(',').forEach(chunk=>{
      const p = chunk.trim()
      if(!p) return
      // split by whitespace if user didn't use commas
      const sub = p.split(/\s+/).map(s=>s.trim()).filter(Boolean)
      if(sub.length === 1){
        parts.push(sub[0])
      }else{
        // If chunk contained spaces but no commas, treat the whole chunk as a single multi-word skill
        parts.push(p)
      }
    })
    onChange && onChange(parts)
  }

  return (
    <input value={text} onChange={e=>setText(e.target.value)} onBlur={handleBlur} placeholder="e.g. python django react (commas optional)" style={{width:400}} />
  )
}
