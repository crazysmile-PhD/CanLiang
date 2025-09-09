import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StatsPage from '@/app/stats/page'
import { vi } from 'vitest'

describe('StatsPage', () => {
  const mockData = {
    data: [
      {
        group: 'A',
        lastDuration: 5,
        avgDuration: 3,
        success: 2,
        failure: 1,
        outputs: { x: 1 },
        date: '2024-01-01',
      },
    ],
  }

  beforeEach(() => {
    vi.resetAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
      blob: () => Promise.resolve(new Blob()),
    }) as any
  })

  it('fetches data and switches time window', async () => {
    render(<StatsPage />)
    expect(fetch).toHaveBeenCalledWith('/api/stats?window=1')
    await waitFor(() => screen.getByText('A'))
    await userEvent.selectOptions(screen.getByLabelText('Time Window'), '7')
    await waitFor(() => expect(fetch).toHaveBeenLastCalledWith('/api/stats?window=7'))
  })

  it('calls export endpoints', async () => {
    render(<StatsPage />)
    await waitFor(() => screen.getByText('A'))
    await userEvent.click(screen.getByText('Export CSV'))
    expect(fetch).toHaveBeenCalledWith('/api/stats/export?window=1&format=csv')
    await userEvent.click(screen.getByText('Export JSON'))
    expect(fetch).toHaveBeenCalledWith('/api/stats/export?window=1&format=json')
  })

  it('toggles chart type and dimension', async () => {
    render(<StatsPage />)
    await waitFor(() => screen.getByText('A'))
    await userEvent.click(screen.getByText('Line'))
    expect(screen.getByText('Bar')).toBeInTheDocument()
    await userEvent.click(screen.getByText('By Date'))
    expect(screen.getByText('By Group')).toBeInTheDocument()
  })
})
