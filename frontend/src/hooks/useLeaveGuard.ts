'use client';
import { useEffect } from 'react';
export function useLeaveGuard(dirty: boolean) {
    useEffect(() => {
        if (!dirty)
            return;
        const unload = (e: BeforeUnloadEvent) => { e.preventDefault(); };
        const click = (e: MouseEvent) => { const a = (e.target as HTMLElement).closest('a'); if (a?.href && !a.href.startsWith(`${location.href.split('#')[0]}#`) && !window.confirm('有尚未保存的修改，确定离开吗？')) {
            e.preventDefault();
            e.stopPropagation();
        } };
        window.addEventListener('beforeunload', unload);
        document.addEventListener('click', click, true);
        return () => { window.removeEventListener('beforeunload', unload); document.removeEventListener('click', click, true); };
    }, [dirty]);
}
