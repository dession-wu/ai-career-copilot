import { fireEvent, render, screen, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RevisionReview } from '@/components/career/RevisionReview';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
describe('Fact review decisions', () => {
    it('requires a decision and can reject an unsupported claim without losing surrounding content', () => {
        vi.spyOn(window, 'confirm').mockReturnValue(true);
        const apply = vi.fn();
        render(<RevisionReview before={'姓名\n参与项目\n教育'} after={'姓名\n主导项目\n教育'} onApply={apply}/>);
        const submit = screen.getByRole('button', { name: '将核对结果写入编辑区' });
        expect(submit).toBeDisabled();
        fireEvent.click(screen.getByText(/变化 1/));
        fireEvent.click(screen.getByRole('button', { name: '保留参考原文' }));
        fireEvent.click(submit);
        expect(apply).toHaveBeenCalledWith('姓名\n参与项目\n教育');
    });
    it('can accept a wording change explicitly', () => {
        vi.spyOn(window, 'confirm').mockReturnValue(true);
        const apply = vi.fn();
        render(<RevisionReview before="开发接口" after="参与接口开发" onApply={apply}/>);
        fireEvent.click(screen.getByText(/变化 1/));
        fireEvent.click(screen.getByRole('button', { name: '使用建议表达' }));
        fireEvent.click(screen.getByRole('button', { name: '将核对结果写入编辑区' }));
        expect(apply).toHaveBeenCalledWith('参与接口开发');
    });
});
