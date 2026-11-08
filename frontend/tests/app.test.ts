import { describe, it, expect } from 'vitest';

describe('App Configuration', () => {
  it('should have correct API base URL', () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    expect(apiUrl).toBeDefined();
    expect(apiUrl).toContain('localhost');
  });

  it('should have shared types available', async () => {
    const types = await import('@shared/types');
    expect(types).toBeDefined();
  });

  it('should have shared constants available', async () => {
    const constants = await import('@shared/constants');
    expect(constants.API_PATHS).toBeDefined();
    expect(constants.JOB_STATUS).toBeDefined();
  });
});
