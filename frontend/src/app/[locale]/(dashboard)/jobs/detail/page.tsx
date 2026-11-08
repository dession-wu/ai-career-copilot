import { Suspense } from 'react';
import JobWorkspace from '@/components/career/JobWorkspace';
export default function JobDetailPage() { return <Suspense fallback={<div className="loading-state">正在打开岗位工作区…</div>}><JobWorkspace /></Suspense>; }
