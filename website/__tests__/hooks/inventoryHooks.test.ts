import { renderHook, waitFor } from '@testing-library/react';
import { useDateList, useInventoryData } from '@/hooks/useInventory';

describe('useDateList', () => {
  const originalFetch = global.fetch;
  afterEach(() => {
    global.fetch = originalFetch;
    jest.resetAllMocks();
  });

  test('fetches and formats date list', async () => {
    const mockResponse = { list: ['2025-05-20'] };
    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockResponse) })
    ) as any;

    const { result } = renderHook(() => useDateList());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledWith('/api/LogList');
    expect(result.current.dates).toEqual([
      { value: '2025-05-20', label: '2025-05-20' },
    ]);
    expect(result.current.error).toBeNull();
  });
});

describe('useInventoryData', () => {
  const originalFetch = global.fetch;
  afterEach(() => {
    global.fetch = originalFetch;
    jest.resetAllMocks();
  });

  test('fetches inventory data for a date', async () => {
    const mockData = { item_count: { 苹果: 2 }, duration: '1h' };
    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockData) })
    ) as any;

    const { result } = renderHook(() => useInventoryData('2025-05-20'));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledWith('/api/analyse?date=2025-05-20');
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });
});
