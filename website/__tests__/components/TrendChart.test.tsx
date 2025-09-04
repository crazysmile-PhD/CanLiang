import { render, screen } from '@testing-library/react';
import { TrendChart } from '@/components/TrendChart';

const colors = {
  primary: '#000',
  secondary: '#111',
  light: '#eee',
  darkText: '#000',
};

test('renders trend chart with stats', () => {
  const data = { '2025-05-20': 10, '2025-05-21': 20 };
  render(<TrendChart data={data} title="测试" colors={colors} type="item" />);
  expect(screen.getByText('最大值')).toBeInTheDocument();
  expect(screen.getByText('最小值')).toBeInTheDocument();
  expect(screen.getByText('平均值')).toBeInTheDocument();
});
