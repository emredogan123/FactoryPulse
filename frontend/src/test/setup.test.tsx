import {
  render,
  screen,
} from '@testing-library/react'
import {
  describe,
  expect,
  it,
} from 'vitest'


describe('frontend test environment', () => {
  it('renders React content', () => {
    render(
      <div>
        FactoryPulse test environment
      </div>,
    )

    expect(
      screen.getByText(
        'FactoryPulse test environment',
      ),
    ).toBeInTheDocument()
  })
})