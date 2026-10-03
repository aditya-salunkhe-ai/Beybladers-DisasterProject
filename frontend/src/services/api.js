const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function request(path, options={}){const r=await fetch(`${BASE}${path}`,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options});if(!r.ok){let msg=`${r.status} ${r.statusText}`;try{const body=await r.json();msg=body.detail||msg}catch{}throw new Error(msg)}return r.json();}
export const api={
 dashboard:()=>request('/api/dashboard'), requests:()=>request('/api/requests'),
 createRequest:(data)=>request('/api/requests',{method:'POST',body:JSON.stringify(data)}),
 resources:()=>request('/api/resources'), facilities:()=>request('/api/facilities'), events:()=>request('/api/events'),
 allocationPreview:(id)=>request(`/api/allocate/${id}`),
 createAllocation:(id)=>request(`/api/allocate/${id}`,{method:'POST'}),
 dispatch:(id)=>request(`/api/dispatch/${id}`,{method:'POST'}),
 allocations:()=>request('/api/allocations'),
 missions:()=>request('/api/operations/missions'),
 markEnRoute:(id)=>request(`/api/operations/${id}/en-route`,{method:'POST'}),
 simulateFacilityFull:(id)=>request(`/api/simulate/facility-full/${id}`,{method:'POST'}),
 simulateRoadBlock:(id)=>request(`/api/simulate/road-block/${id}`,{method:'POST'}),
 deliver:(id)=>request(`/api/operations/${id}/deliver`,{method:'POST'}),
 requestAudit:(id)=>request(`/api/audit/requests/${id}`),
 resetDemo:()=>request('/api/demo/reset',{method:'POST'})
};
