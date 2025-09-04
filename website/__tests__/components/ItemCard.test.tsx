import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ItemCard } from '@/app/page'

test('ItemCard renders and handles click', async () => {
  const user = userEvent.setup()
  const onClick = jest.fn()
  render(<ItemCard name='苹果' count={3} color='#fff' onClick={onClick} />)
  expect(screen.getByText('苹果')).toBeInTheDocument()
  await user.click(screen.getByText('苹果'))
  expect(onClick).toHaveBeenCalled()
})
