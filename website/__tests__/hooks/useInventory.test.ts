import { renderHook, waitFor } from '@testing-library/react'
import { useInventory } from '@/hooks/useInventory'

describe('useInventory', () => {
  afterEach(() => {
    ;(global.fetch as jest.Mock) && (global.fetch as jest.Mock).mockReset()
  })

  test('fetches inventory data', async () => {
    const mockData = { item_count: { 苹果: 2 }, duration: '10m' }
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    })

    const { result } = renderHook(() => useInventory('2025-05-20'))

    await waitFor(() => expect(result.current.data).toEqual(mockData))
    expect(global.fetch).toHaveBeenCalledWith('/api/analyse?date=2025-05-20')
  })

  test('handles fetch error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('network'))
    const { result } = renderHook(() => useInventory('2025-05-20'))
    await waitFor(() => expect(result.current.error).toBe('network'))
  })
})
