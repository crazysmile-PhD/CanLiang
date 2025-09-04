import { render, screen, waitFor } from '@testing-library/react'
import InventoryPage from '@/app/page'

test('InventoryPage renders data from API', async () => {
  global.fetch = jest.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ list: ['2025-05-20'] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ item_count: { 苹果: 2 }, duration: '10m' }) })

  render(<InventoryPage />)

  await waitFor(() => expect(screen.getByText('苹果')).toBeInTheDocument())
})
