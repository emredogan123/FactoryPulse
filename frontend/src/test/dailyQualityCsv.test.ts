import { describe, expect, it } from 'vitest'

import { createDailyQualityCsv } from '../utils/dailyQualityCsv'
import type { DailyQualityResponse } from '../types'

function makeReport(): DailyQualityResponse {
  return {
    prefix: 'ML-TRAIN',
    start_date: '2026-08-01',
    end_date: '2026-08-02',
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
    ],
  }
}

describe('Daily quality CSV', () => {
  it('exports report filters and daily values', () => {
    const csv = createDailyQualityCsv(makeReport())
    const lines = csv.slice(1).split('\r\n')

    expect(csv.startsWith('\uFEFF')).toBe(true)
    expect(lines).toHaveLength(3)

    expect(lines[1]).toBe(
      '"ML-TRAIN","2026-08-01","2026-08-02","UTC",' +
      '"2026-08-01","10","8","1","1","2","20.00"',
    )
  })

  it('keeps missing rates empty instead of reporting zero', () => {
    const csv = createDailyQualityCsv(makeReport())
    const lines = csv.slice(1).split('\r\n')

    expect(lines[2]).toBe(
      '"ML-TRAIN","2026-08-01","2026-08-02","UTC",' +
      '"2026-08-02","0","0","0","0","0",""',
    )
  })

  it('preserves a measured zero issue rate', () => {
    const report = makeReport()

    report.days[0] = {
      ...report.days[0],
      passed_count: 10,
      warning_count: 0,
      failed_count: 0,
      issue_count: 0,
      issue_rate: 0,
    }

    const row = createDailyQualityCsv(report)
      .split('\r\n')[1]

    expect(row.endsWith(',"0.00"')).toBe(true)
  })

  it('labels an unfiltered report as All records', () => {
    const report = makeReport()
    report.prefix = null

    const row = createDailyQualityCsv(report)
      .split('\r\n')[1]

    expect(row.startsWith('"All records",')).toBe(true)
  })

  it('escapes quotation marks and commas in text', () => {
    const report = makeReport()
    report.prefix = 'LOT,"A"'

    const row = createDailyQualityCsv(report)
      .split('\r\n')[1]

    expect(row.startsWith('"LOT,""A""",')).toBe(true)
  })

  it('neutralizes text that could be interpreted as a formula', () => {
    const report = makeReport()
    report.prefix = '=1+1'

    const row = createDailyQualityCsv(report)
      .split('\r\n')[1]

    expect(row.startsWith(`"'=1+1",`)).toBe(true)
  })
})