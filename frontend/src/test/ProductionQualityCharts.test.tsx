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

import { ProductionQualityCharts } from '../components/ProductionQualityCharts'
import { getProductionQuality } from '../api'

import type {
  ProductionQualityResponse,
  QualityCounts,
} from '../types'

vi.mock('../api', () => ({
  getProductionQuality: vi.fn(),

  getStageQuality: vi.fn().mockResolvedValue({
    prefix: null,
    stages: [],
  }),

  getDailyQuality: vi.fn().mockResolvedValue({
    prefix: null,
    start_date: '2026-08-01',
    end_date: '2026-08-31',
    timezone: 'UTC',
    days: [],
  }),
}))

const counts: QualityCounts = {
  total_count: 4,
  evaluated_count: 3,
  pending_count: 1,
  passed_count: 1,
  failed_count: 1,
  rework_count: 1,
  issue_count: 2,
  issue_rate: 66.67,
}

const emptyCounts: QualityCounts = {
  total_count: 0,
  evaluated_count: 0,
  pending_count: 0,
  passed_count: 0,
  failed_count: 0,
  rework_count: 0,
  issue_count: 0,
  issue_rate: null,
}

function createResponse(): ProductionQualityResponse {
  return {
    prefix: 'ML-TRAIN',
    summary: counts,
    shifts: [
      {
        ...counts,
        shift: 'DAY',
      },
      {
        ...emptyCounts,
        shift: 'NIGHT',
      },
    ],
    material_lots: [
      {
        ...counts,
        material_lot_id: null,
        lot_code: null,
      },
    ],
  }
}

describe('Production quality charts', () => {
  beforeEach(() => {
    vi.mocked(getProductionQuality).mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows counts and records without a material lot', async () => {
    vi.mocked(getProductionQuality)
      .mockResolvedValue(createResponse())

    render(<ProductionQualityCharts />)

    expect(
      await screen.findByText('No material lot'),
    ).toBeInTheDocument()

    expect(
      screen.getAllByText(
        '2 issues / 3 evaluated · 1 pending',
      ),
    ).toHaveLength(2)

    expect(
      screen.getAllByText('66.67%'),
    ).toHaveLength(3)

    expect(
      screen.getByText('No data'),
    ).toBeInTheDocument()
  })

  it('requests the selected dataset', async () => {
    vi.mocked(getProductionQuality)
      .mockResolvedValue(createResponse())

    render(<ProductionQualityCharts />)

    await screen.findByText('No material lot')

    expect(
      getProductionQuality,
    ).toHaveBeenLastCalledWith(
      'ML-TRAIN',
      expect.any(AbortSignal),
    )

    fireEvent.change(
      screen.getByLabelText('Quality dataset'),
      {
        target: {
          value: 'ML-TEST',
        },
      },
    )

    await waitFor(() => {
      expect(
        getProductionQuality,
      ).toHaveBeenLastCalledWith(
        'ML-TEST',
        expect.any(AbortSignal),
      )
    })

    await screen.findByText('No material lot')
  })

  it('requests all records without a prefix', async () => {
    vi.mocked(getProductionQuality)
      .mockResolvedValue(createResponse())

    render(<ProductionQualityCharts />)

    await screen.findByText('No material lot')

    fireEvent.change(
      screen.getByLabelText('Quality dataset'),
      {
        target: {
          value: '',
        },
      },
    )

    await waitFor(() => {
      expect(
        getProductionQuality,
      ).toHaveBeenLastCalledWith(
        undefined,
        expect.any(AbortSignal),
      )
    })

    await screen.findByText('No material lot')
  })

  it('shows an empty result without a zero issue rate', async () => {
    vi.mocked(getProductionQuality)
      .mockResolvedValue({
        prefix: 'ML-TRAIN',
        summary: emptyCounts,
        shifts: [],
        material_lots: [],
      })

    render(<ProductionQualityCharts />)

    expect(
      await screen.findByText(
        'No PCB records found for this selection.',
      ),
    ).toBeInTheDocument()

    expect(
      screen.queryByText('0.00%'),
    ).not.toBeInTheDocument()
  })

  it('retries successfully after a connection error', async () => {
    vi.mocked(getProductionQuality)
      .mockRejectedValueOnce(
        new Error('Connection failed'),
      )
      .mockResolvedValueOnce(createResponse())

    render(<ProductionQualityCharts />)

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      'Production quality could not be loaded.',
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Refresh quality',
      }),
    )

    expect(
      await screen.findByText('No material lot'),
    ).toBeInTheDocument()

    expect(
      screen.queryByRole('alert'),
    ).not.toBeInTheDocument()
  })
})