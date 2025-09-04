import { render, screen, waitFor } from '@testing-library/react';
import InventoryPage from '@/app/page';

test('renders inventory page with fetched data', async () => {
  const originalFetch = global.fetch;
  const mockDateList = { list: ['2025-05-20'] };
  const mockInventory = { item_count: { 苹果: 3 }, duration: '10m' };

  global.fetch = jest.fn((url: string) => {
    if (url === '/api/LogList') {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDateList) });
    }
    if (url.startsWith('/api/analyse')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockInventory) });
    }
    return Promise.reject(new Error('unknown url'));
  }) as any;

  render(<InventoryPage />);

  await waitFor(() => expect(screen.getByText('苹果')).toBeInTheDocument());

  global.fetch = originalFetch;
});
