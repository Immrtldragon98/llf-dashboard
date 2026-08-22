import React,{useEffect,useMemo,useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API=(import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";
type Equipment={id:number;asset_id:string;line:string;name:string};
type Parameter={parameter_id:number;key:string;name:string;type:string;unit?:string;options?:string[]};
type User={sub:string;role:"admin"|"operator"|"viewer"};

function App(){
  const [token,setToken]=useState(localStorage.getItem("token")||"");
  const [user,setUser]=useState<User|null>(null);
  const [username,setUsername]=useState("operator");
  const [password,setPassword]=useState("operator123");
  const [message,setMessage]=useState("");
  const [tab,setTab]=useState<"entry"|"data"|"admin">("entry");
  const [equipment,setEquipment]=useState<Equipment[]>([]);
  const [entryLine,setEntryLine]=useState("CH2-WRM1");
  const [entryEquipment,setEntryEquipment]=useState<Equipment|null>(null);
  const [parameters,setParameters]=useState<Parameter[]>([]);
  const [shift,setShift]=useState("A");
  const [recordDate,setRecordDate]=useState(new Date().toISOString().slice(0,10));
  const [values,setValues]=useState<Record<string,string>>({});
  const [remarks,setRemarks]=useState("");
  const [entryCompletion,setEntryCompletion]=useState<any[]>([]);
  const [viewEquipment,setViewEquipment]=useState("");
  const [viewShift,setViewShift]=useState("");
  const [startDate,setStartDate]=useState("");
  const [endDate,setEndDate]=useState("");
  const [records,setRecords]=useState<any[]>([]);
  const [completion,setCompletion]=useState<any[]>([]);
  const [completionDate,setCompletionDate]=useState(new Date().toISOString().slice(0,10));
  const [newEq,setNewEq]=useState({asset_id:"",line:"CH2-WRM1",name:""});
  const [newParam,setNewParam]=useState({parameter_key:"",parameter_name:"",parameter_type:"status",unit:""});
  const authHeaders=useMemo(()=>({Authorization:`Bearer ${token}`}),[token]);

  async function api(path:string, options:any={}){
    const headers={...(options.headers||{}),...authHeaders};
    const response=await fetch(`${API}${path}`,{...options,headers});
    if(response.status===401){logout();throw new Error("Session expired");}
    return response;
  }
  function logout(){localStorage.removeItem("token");setToken("");setUser(null);}
  async function login(){
    setMessage("");
    const r=await fetch(`${API}/auth/login`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});
    const d=await r.json();
    if(!r.ok){setMessage(d.detail||"Login failed");return;}
    localStorage.setItem("token",d.token);setToken(d.token);
  }
  async function loadEquipment(){
    if(!token)return;
    const r=await api("/equipment");const data=await r.json();setEquipment(data);
    if(data.length&&!viewEquipment)setViewEquipment(String(data[0].id));
  }
  async function loadEntryCompletion(){
    if(!token)return;
    const r=await api(`/completion?record_date=${recordDate}&line=${encodeURIComponent(entryLine)}`);setEntryCompletion(await r.json());
  }
  useEffect(()=>{if(token)api("/auth/me").then(r=>r.json()).then(setUser).catch(()=>{});},[token]);
  useEffect(()=>{loadEquipment().catch(()=>{});},[token]);
  useEffect(()=>{if(user)loadEntryCompletion().catch(()=>{});},[user,recordDate,entryLine]);
  useEffect(()=>{if(entryEquipment)api(`/equipment/${entryEquipment.id}/parameters`).then(r=>r.json()).then(data=>{setParameters(data);setValues({});setRemarks("");setMessage("");});},[entryEquipment]);

  const entryLines=[...new Set(equipment.map(e=>e.line))];
  const entryEq=equipment.filter(e=>e.line===entryLine);
  function completionFor(equipmentId:number){return entryCompletion.find(x=>x.id===equipmentId);}
  function isCurrentShiftComplete(equipmentId:number){const c=completionFor(equipmentId);return !!c?.shifts?.[shift];}
  function isAbnormal(p:Parameter){const v=(values[p.key]||"").toUpperCase();return p.type==="status"&&(v==="NOT OK"||v==="NO");}
  const abnormalCount=parameters.filter(isAbnormal).length;
  const missingCount=parameters.filter(p=>!values[p.key]||!values[p.key].trim()).length;
  const canSubmit=parameters.length>0&&missingCount===0&&(abnormalCount===0||remarks.trim().length>0);

  async function saveShift(){
    if(!entryEquipment)return;
    if(missingCount>0){setMessage(`⚠ Complete all ${parameters.length} parameters before saving. ${missingCount} still missing.`);return;}
    if(abnormalCount>0&&!remarks.trim()){setMessage("⚠ Add remarks because one or more readings are NOT OK / NO.");return;}
    const readings=parameters.map(p=>({parameter_id:p.parameter_id,value:values[p.key]}));
    const r=await api("/shift-records",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({equipment_id:entryEquipment.id,shift,record_date:recordDate,remarks:remarks.trim()||null,readings})});
    const d=await r.json();setMessage(r.ok?"✓ Shift data saved":`⚠ ${d.detail||"Save failed"}`);
    if(r.ok){await loadEntryCompletion();await loadCompletion();}
  }
  function queryString(){const q=new URLSearchParams();if(viewEquipment)q.set("equipment_id",viewEquipment);if(viewShift)q.set("shift",viewShift);if(startDate)q.set("start_date",startDate);if(endDate)q.set("end_date",endDate);return q.toString();}
  async function loadRecords(){const r=await api(`/shift-records?${queryString()}`);setRecords(await r.json());}
  async function loadCompletion(){const r=await api(`/completion?record_date=${completionDate}`);setCompletion(await r.json());}
  useEffect(()=>{if(user)loadCompletion().catch(()=>{});},[user,completionDate]);
  async function downloadExcel(){const r=await api(`/export.xlsx?${queryString()}`);if(!r.ok){const d=await r.json();setMessage(`⚠ ${d.detail||"Export failed"}`);return;}const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="LLF_equipment_data.xlsx";a.click();URL.revokeObjectURL(url);}
  async function addEquipment(){const r=await api("/admin/equipment",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({asset_id:newEq.asset_id,line_code:newEq.line,name:newEq.name})});const d=await r.json();setMessage(r.ok?"✓ Equipment added":`⚠ ${d.detail||"Could not add equipment"}`);if(r.ok){setNewEq({...newEq,asset_id:"",name:""});loadEquipment();}}
  async function addParameter(){const body={...newParam,unit:newParam.unit||null};const r=await api("/admin/parameters",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();setMessage(r.ok?"✓ Parameter added":`⚠ ${d.detail||"Could not add parameter"}`);}

  if(!user)return <div className="login"><div className="login-card"><h1>LLF Dashboard</h1><p>Continuous Properzi 15 Tbh</p><input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Username"/><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="Password"/><button className="primary full" onClick={login}>Sign in</button>{message&&<div className="message">{message}</div>}<small>Prototype: operator/operator123 · admin/admin123 · viewer/viewer123</small></div></div>;

  return <div className="app">
    <header><div><h1>LLF Dashboard</h1><small>Continuous Properzi 15 Tbh · {user.sub} ({user.role})</small></div><button onClick={logout}>Sign out</button></header>
    <nav><button className={tab==="entry"?"active":""} onClick={()=>setTab("entry")}>LLF Entry</button><button className={tab==="data"?"active":""} onClick={()=>{setTab("data");loadRecords();}}>View Data</button>{user.role==="admin"&&<button className={tab==="admin"?"active":""} onClick={()=>setTab("admin")}>Admin</button>}</nav>

    {tab==="entry"&&<main>
      <section className="panel"><div className="section-title"><div><h2>Line</h2><small>Choose line, shift and date before equipment</small></div><div className="entry-controls"><input type="date" value={recordDate} onChange={e=>{setRecordDate(e.target.value);setEntryEquipment(null)}}/><div className="chips">{["A","B","C"].map(s=><button key={s} className={shift===s?"chip selected":"chip"} onClick={()=>{setShift(s);setEntryEquipment(null)}}>Shift {s}</button>)}</div></div></div><div className="chips top-gap">{entryLines.map(l=><button key={l} className={entryLine===l?"chip selected":"chip"} onClick={()=>{setEntryLine(l);setEntryEquipment(null)}}>{l.replace("CH2-","")}</button>)}</div></section>
      <section className="panel"><h2>Equipment</h2><div className="equipment-grid">{entryEq.map(e=>{const c=completionFor(e.id);const done=!!c?.shifts?.[shift];return <button key={e.id} className={`equipment-tile ${done?"equipment-done":""} ${entryEquipment?.id===e.id?"equipment-selected":""}`} onClick={()=>setEntryEquipment(e)}><span>{e.name}</span><small>{e.asset_id}</small><strong>{done?`Shift ${shift} ✓ Completed`:`Shift ${shift} · Pending`}</strong></button>})}</div></section>
      {entryEquipment&&<section className="panel"><div className="section-title"><div><h2>{entryEquipment.name}</h2><small>{entryEquipment.asset_id} · Shift {shift} · {recordDate}</small></div>{isCurrentShiftComplete(entryEquipment.id)?<span className="status-pill completed">Already completed</span>:<span className="status-pill pending-pill">Pending</span>}</div>{isCurrentShiftComplete(entryEquipment.id)?<div className="locked-note">This shift has already been submitted. Use <strong>View Data</strong> to review it.</div>:<><div className="progress-row"><span>{parameters.length-missingCount}/{parameters.length} parameters completed</span>{abnormalCount>0&&<span className="abnormal-count">{abnormalCount} abnormal</span>}</div><div className="params">{parameters.map(p=><label key={p.parameter_id} className={isAbnormal(p)?"parameter abnormal":"parameter"}><span>{p.name}{p.unit&&<em>{p.unit}</em>}</span>{p.type==="status"?<select className={isAbnormal(p)?"abnormal-input":""} value={values[p.key]||""} onChange={e=>setValues({...values,[p.key]:e.target.value})}><option value="">Select</option>{p.options?.map(o=><option key={o} value={o}>{o}</option>)}</select>:<input type="number" value={values[p.key]||""} onChange={e=>setValues({...values,[p.key]:e.target.value})}/>}</label>)}</div><div className={`remarks-box ${abnormalCount>0?"remarks-required":""}`}><label>Remarks {abnormalCount>0&&<strong>Required for abnormal reading</strong>}<textarea placeholder={abnormalCount>0?"Describe the abnormal condition / action taken...":"Optional shift remarks..."} value={remarks} onChange={e=>setRemarks(e.target.value)}/></label></div>{user.role!=="viewer"&&<button className="primary" disabled={!canSubmit} onClick={saveShift}>Save Shift {shift} Data</button>}{!canSubmit&&user.role!=="viewer"&&<small className="submit-hint">{missingCount>0?`${missingCount} parameter(s) still need a value.`:"Remarks required because an abnormal status is selected."}</small>}</>}{message&&<div className="message">{message}</div>}</section>}
    </main>}

    {tab==="data"&&<main><section className="panel"><div className="section-title"><div><h2>Equipment Data</h2><small>Filter and export shift-wise LLF records</small></div><button className="primary no-top" onClick={downloadExcel}>Download Excel</button></div><div className="filters"><label>Equipment<select value={viewEquipment} onChange={e=>setViewEquipment(e.target.value)}><option value="">All Equipment</option>{equipment.map(e=><option key={e.id} value={String(e.id)}>{e.line.replace("CH2-","")} · {e.name}</option>)}</select></label><label>Shift<select value={viewShift} onChange={e=>setViewShift(e.target.value)}><option value="">All shifts</option><option>A</option><option>B</option><option>C</option></select></label><label>From<input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)}/></label><label>To<input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)}/></label><button onClick={loadRecords}>Apply Filters</button></div><div className="table-wrap"><table><thead><tr><th>Date</th><th>Shift</th><th>Line</th><th>Equipment</th><th>Parameter</th><th>Value</th><th>Unit</th><th>Remarks</th><th>Entered by</th></tr></thead><tbody>{records.map((r,i)=>{const abnormal=(String(r.value).toUpperCase()==="NOT OK"||String(r.value).toUpperCase()==="NO");return <tr key={`${r.record_id}-${i}`} className={abnormal?"abnormal-row":""}><td>{r.record_date}</td><td>{r.shift}</td><td>{r.line.replace("CH2-","")}</td><td>{r.equipment_name}</td><td>{r.parameter_name}</td><td>{r.value||"—"}</td><td>{r.unit||"—"}</td><td>{r.remarks||"—"}</td><td>{r.entered_by}</td></tr>})}</tbody></table>{!records.length&&<p className="empty">No records match the selected filters.</p>}</div></section><section className="panel"><div className="section-title"><div><h2>Shift Completion</h2><small>A/B/C submission status by equipment</small></div><input type="date" value={completionDate} onChange={e=>setCompletionDate(e.target.value)}/></div><div className="completion-grid">{completion.map(c=><div key={c.id} className="completion-card"><div><strong>{c.line.replace("CH2-","")} · {c.name}</strong><small>{c.asset_id}</small></div><div className="completion-shifts">{["A","B","C"].map(s=><span key={s} className={c.shifts[s]?"done":"pending"}>{s} {c.shifts[s]?"✓":"—"}</span>)}</div></div>)}</div></section></main>}

    {tab==="admin"&&user.role==="admin"&&<main><section className="panel"><h2>Add Equipment</h2><div className="form-grid"><input placeholder="Asset ID e.g. CH2-WRM1-Coiler" value={newEq.asset_id} onChange={e=>setNewEq({...newEq,asset_id:e.target.value})}/><input placeholder="Line e.g. CH2-WRM1" value={newEq.line} onChange={e=>setNewEq({...newEq,line:e.target.value})}/><input placeholder="Equipment name" value={newEq.name} onChange={e=>setNewEq({...newEq,name:e.target.value})}/><button className="primary no-top" onClick={addEquipment}>Add Equipment</button></div></section><section className="panel"><h2>Add Parameter</h2><div className="form-grid"><input placeholder="Parameter key" value={newParam.parameter_key} onChange={e=>setNewParam({...newParam,parameter_key:e.target.value})}/><input placeholder="Parameter name" value={newParam.parameter_name} onChange={e=>setNewParam({...newParam,parameter_name:e.target.value})}/><select value={newParam.parameter_type} onChange={e=>setNewParam({...newParam,parameter_type:e.target.value})}><option value="status">Status</option><option value="number">Number</option></select><input placeholder="Unit: mm, °C, m/s, Nm" value={newParam.unit} onChange={e=>setNewParam({...newParam,unit:e.target.value})}/><button className="primary no-top" onClick={addParameter}>Add Parameter</button></div>{message&&<div className="message">{message}</div>}</section></main>}
  </div>
}

createRoot(document.getElementById("root")!).render(<App/>);
