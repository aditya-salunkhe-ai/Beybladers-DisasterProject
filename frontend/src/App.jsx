import {useEffect,useState} from 'react';
import Sidebar from './components/Sidebar';
import CommandCenter from './pages/CommandCenter';
import EmergencyRequests from './pages/EmergencyRequests';
import Allocation from './pages/Allocation';
import LiveOperations from './pages/LiveOperations';
import AuditTracking from './pages/AuditTracking';
import './styles.css';

const validPages=['command','requests','allocation','operations','audit'];
const pageFromHash=()=>{const p=(window.location.hash||'#command').slice(1).split('?')[0];return validPages.includes(p)?p:'command'};
export default function App(){
 const [page,setPage]=useState(pageFromHash),[selectedRequest,setSelectedRequest]=useState('');
 useEffect(()=>{const sync=()=>setPage(pageFromHash());window.addEventListener('hashchange',sync);if(!window.location.hash)window.location.hash='command';return()=>window.removeEventListener('hashchange',sync)},[]);
 const nav=(p,id)=>{if(id)setSelectedRequest(id);window.location.hash=p;setPage(p)};
 let view=page==='command'?<CommandCenter onNavigate={nav}/>:page==='requests'?<EmergencyRequests onAllocate={(id)=>nav('allocation',id)}/>:page==='allocation'?<Allocation initialRequestId={selectedRequest} onNavigate={nav}/>:page==='operations'?<LiveOperations/>:<AuditTracking/>;
 return <div className="app"><Sidebar page={page} onNavigate={nav}/>{view}</div>
}
