import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { DailyQualityChart } from '../components/DailyQualityChart'
import { getDailyQuality } from '../api'
import type { DailyQualityResponse } from '../types'

vi.mock('../api', () => ({
  getDailyQuality: vi.fn(),
}))

function createResponse(): DailyQualityResponse {
  return {
    prefix: 'ML-TRAIN',
    start_date: '2026-08-01',
    end_date: '2026-08-03',
    timezone: 'UTC',
    days: [
      {
        date: '2026-08-01',
        evaluated_count: 10,
        passed_count: 8,
        warning_count: 1,
        failed_count: 1,
        issue_count: 2,
        issue_rate: 20,
      },
      {
        date: '2026-08-02',
        evaluated_count: 0,
        passed_count: 0,
        warning_count: 0,
        failed_count: 0,
        issue_count: 0,
        issue_rate: null,
      },
      {
        date: '2026-08-03',
        evaluated_count: 90,
        passed_count: 81,
        warning_count: 5,
        failed_count: 4,
        issue_count: 9,
        issue_rate: 10,
      },
    ],
  }
}

describe('Daily quality chart', () => {
  beforeEach(() => {
    vi.mocked(getDailyQuality).mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it('calculates the period rate from event totals', async () => {
    vi.mocked(getDailyQuality)
      .mockResolvedValue(createResponse())

    render(<DailyQualityChart prefix="ML-TRAIN" />)

    // 11 / 100 = %11; günlük yüzdelerin ortalaması %15 değildir.
    expect(
      await screen.findByText(/Period issue rate: 11.00%/),
    ).toBeInTheDocument()

    expect(
      screen.queryByText(/Period issue rate: 15.00%/),
    ).not.toBeInTheDocument()

    expect(
      screen.getByRole('img', {
        name: /Daily process issue rate/,
      }),
    ).toBeInTheDocument()
  })

  it('leaves a gap for a day without data', async () => {
    vi.mocked(getDailyQuality)
      .mockResolvedValue(createResponse())

    render(<DailyQualityChart prefix="ML-TRAIN" />)

    const chart = await screen.findByRole('img', {
      name: /Daily process issue rate/,
    })

    // Üç gün var ama yalnızca iki günün veri noktası var.
    expect(
      chart.querySelectorAll('circle'),
    ).toHaveLength(2)

    // Boş günün iki tarafı ayrı çizgi parçaları olmalı.
    const path = chart.querySelector('path')
      ?.getAttribute('d') ?? ''

    expect(path.match(/M/g)).toHaveLength(2)
    expect(path).not.toContain('L')

    fireEvent.click(
      screen.getByText('Daily details'),
    )

    expect(
      screen.getByText('No data'),
    ).toBeInTheDocument()
  })

  it('requests the applied date range', async () => {
    vi.mocked(getDailyQuality)
      .mockResolvedValue(createResponse())

    render(<DailyQualityChart prefix="ML-TEST" />)

    await screen.findByRole('img', {
      name: /Daily process issue rate/,
    })

    fireEvent.change(
      screen.getByLabelText('Start date'),
      {
        target: { value: '2026-08-05' },
      },
    )

    fireEvent.change(
      screen.getByLabelText('End date'),
      {
        target: { value: '2026-08-10' },
      },
    )

    // Tarih alanını değiştirmek tek başına istek göndermemeli.
    expect(getDailyQuality).toHaveBeenCalledTimes(1)

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Apply dates',
      }),
    )

    await waitFor(() => {
      expect(getDailyQuality).toHaveBeenLastCalledWith(
        '2026-08-05',
        '2026-08-10',
        'ML-TEST',
        expect.any(AbortSignal),
      )
    })

    await screen.findByRole('img', {
      name: /Daily process issue rate/,
    })
  })

  it('rejects a reversed date range without another request', async () => {
    vi.mocked(getDailyQuality)
      .mockResolvedValue(createResponse())

    render(<DailyQualityChart prefix="ML-TRAIN" />)

    await screen.findByRole('img', {
      name: /Daily process issue rate/,
    })

    fireEvent.change(
      screen.getByLabelText('Start date'),
      {
        target: { value: '2026-09-01' },
      },
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Apply dates',
      }),
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      'Choose a valid date range containing 1 to 366 days.',
    )

    expect(getDailyQuality).toHaveBeenCalledTimes(1)
  })

  it('shows an empty state when no events were evaluated', async () => {
    const response = createResponse()
    response.days = [response.days[1]]

    vi.mocked(getDailyQuality)
      .mockResolvedValue(response)

    render(<DailyQualityChart prefix="" />)

    expect(
      await screen.findByText(
        'No evaluated process events found in this date range.',
      ),
    ).toBeInTheDocument()

    expect(screen.queryByRole('img')).not.toBeInTheDocument()

    expect(getDailyQuality).toHaveBeenCalledWith(
      '2026-08-01',
      '2026-08-31',
      undefined,
      expect.any(AbortSignal),
    )
  })

  it('retries after an API error', async () => {
    vi.mocked(getDailyQuality)
      .mockRejectedValueOnce(new Error('Connection failed'))
      .mockResolvedValueOnce(createResponse())

    render(<DailyQualityChart prefix="ML-TRAIN" />)

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent('Daily quality could not be loaded.')

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Apply dates',
      }),
    )

    expect(
      await screen.findByRole('img', {
        name: /Daily process issue rate/,
      }),
    ).toBeInTheDocument()

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})