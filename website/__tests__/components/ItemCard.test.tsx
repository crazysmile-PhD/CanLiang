import { render, screen, fireEvent } from '@testing-library/react';
import { ItemCard } from '@/components/ItemCard';

test('renders item card and handles click', () => {
  const handleClick = jest.fn();
  render(<ItemCard name="苹果" count={3} color="red" onClick={handleClick} />);
  expect(screen.getByText('苹果')).toBeInTheDocument();
  expect(screen.getByText('3')).toBeInTheDocument();
  fireEvent.click(screen.getByText('苹果'));
  expect(handleClick).toHaveBeenCalled();
});
