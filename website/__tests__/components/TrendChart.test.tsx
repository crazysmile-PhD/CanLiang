import { render, screen } from '@testing-library/react'
import { TrendChart } from '@/app/page'

const colors = {
  primary: '#000',
  secondary: '#111',
  accent1: '#222',
  accent2: '#333',
  light: '#eee',
  lightBorder: '#ccc',
  lightGray: '#ddd',
  mediumGray: '#bbb',
  darkText: '#000',
}

test('TrendChart renders with data', () => {
  const data = { '2025-05-20': 1, '2025-05-21': 3 }
  render(<TrendChart data={data} title='Test' colors={colors} type='item' />)
  expect(screen.getByText('数量变化趋势')).toBeInTheDocument()
})
