import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import axios from 'axios'

import { getDailyQuality } from '../api'
import type {
  DailyQualityItem,
  DailyQualityResponse,
} from '../types'

function TrendPlot({ days }: { days: DailyQualityItem[] }) {
  const width = 900
  const height = 280
  const left = 55
  const right = 25
  const top = 25
  const bottom = 45

  const plotWidth = width - left - right
  const plotHeight = height - top - bottom

  const maximum = Math.max(
    0,
    ...days.map(day => day.issue_rate ?? 0),
  )

  // Tüm noktalar aynı, açıkça etiketlenmiş ölçeği kullanır.
  const upperBound = Math.min(
    100,
    Math.max(10, Math.ceil(maximum / 10) * 10),
  )

  const x = (index: number) =>
    days.length === 1
      ? left + plotWidth / 2
      : left + index * plotWidth / (days.length - 1)

  const y = (value: number) =>
    top + plotHeight * (1 - value / upperBound)

  let path = ''
  let connected = false

  days.forEach((day, index) => {
    if (day.issue_rate === null) {
      connected = false
      return
    }

    path += `${connected ? 'L' : 'M'} ${x(index)} ${y(day.issue_rate)} `
    connected = true
  })

  const labelIndexes = [...new Set([
    0,
    Math.floor((days.length - 1) / 2),
    days.length - 1,
  ])]

  return (
    <div className="pq-trend-scroll">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="pq-trend-svg"
        role="img"
        aria-label="Daily process issue rate. Missing days have no data points. Exact values are available in the daily details table."
      >
        {[0, 1, 2, 3, 4].map(index => {
          const value = upperBound * index / 4

          return (
            <g key={index}>
              <line
                x1={left}
                x2={width - right}
                y1={y(value)}
                y2={y(value)}
                stroke="var(--border)"
              />
              <text
                x={left - 10}
                y={y(value) + 4}
                textAnchor="end"
              >
                {value}%
              </text>
            </g>
          )
        })}

        <path
          d={path}
          fill="none"
          stroke="var(--teal-dark)"
          strokeWidth={2.5}
          strokeLinejoin="round"
        />

        {days.map((day, index) =>
          day.issue_rate === null ? null : (
            <circle
              key={day.date}
              cx={x(index)}
              cy={y(day.issue_rate)}
              r={3.5}
              fill="var(--teal-dark)"
            >
              <title>
                {day.date}: {day.issue_rate.toFixed(2)}%
                {' · '}
                {day.issue_count} issues /
                {' '}{day.evaluated_count} evaluated
              </title>
            </circle>
          ),
        )}

        {labelIndexes.map(index => (
          <text
            key={index}
            x={x(index)}
            y={height - 12}
            textAnchor={
              days.length === 1
                ? 'middle'
                : index === 0
                  ? 'start'
                  : index === days.length - 1
                    ? 'end'
                    : 'middle'
            }
          >
            {days[index].date}
          </text>
        ))}
      </svg>
    </div>
  )
}

function DailyResults({
  prefix,
  startDate,
  endDate,
}: {
  prefix: string
  startDate: string
  endDate: string
}) {
  const [data, setData] =
    useState<DailyQualityResponse | null>(null)

  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function load(): Promise<void> {
      try {
        const result = await getDailyQuality(
          startDate,
          endDate,
          prefix || undefined,
          controller.signal,
        )

        if (active) {
          setData(result)
        }
      } catch (cause) {
        if (!active) {
          return
        }

        const status = axios.isAxiosError(cause)
          ? cause.response?.status
          : undefined

        setError(
          status === 401
            ? 'Your session has expired. Sign out and sign in again.'
            : status === 403
              ? 'You do not have permission to view daily quality.'
              : 'Daily quality could not be loaded. Check the backend and press Apply dates to retry.',
        )
      }
    }

    void load()

    return () => {
      active = false
      controller.abort()
    }
  }, [prefix, startDate, endDate])

  if (error) {
    return <p role="alert" className="pq-error">{error}</p>
  }

  if (!data) {
    return <p role="status">Loading daily quality...</p>
  }

  const evaluated = data.days.reduce(
    (sum, day) => sum + day.evaluated_count,
    0,
  )

  const issues = data.days.reduce(
    (sum, day) => sum + day.issue_count,
    0,
  )

  if (evaluated === 0) {
    return (
      <p role="status">
        No evaluated process events found in this date range.
      </p>
    )
  }

  // Günlük yüzdelerin ortalaması değil, toplam kayıtlardan hesaplanır.
  const periodRate = 100 * issues / evaluated

  return (
    <>
      <p className="pq-note">
        {evaluated.toLocaleString('en-US')} evaluated events
        {' · '}
        {issues.toLocaleString('en-US')} issues
        {' · '}
        Period issue rate: {periodRate.toFixed(2)}%
        {' · '}
        Timezone: {data.timezone}
      </p>

      <TrendPlot days={data.days} />

      <details className="pq-daily-details">
        <summary>Daily details</summary>

        <div className="pq-daily-table">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Date (UTC)</th>
                <th scope="col">Evaluated</th>
                <th scope="col">Warning</th>
                <th scope="col">Failed</th>
                <th scope="col">Issue rate</th>
              </tr>
            </thead>

            <tbody>
              {data.days.map(day => (
                <tr key={day.date}>
                  <td>{day.date}</td>
                  <td>{day.evaluated_count.toLocaleString('en-US')}</td>
                  <td>{day.warning_count.toLocaleString('en-US')}</td>
                  <td>{day.failed_count.toLocaleString('en-US')}</td>
                  <td>
                    {day.issue_rate === null
                      ? 'No data'
                      : `${day.issue_rate.toFixed(2)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  )
}

export function DailyQualityChart({
  prefix,
}: {
  prefix: string
}) {
  const [startDate, setStartDate] = useState('2026-08-01')
  const [endDate, setEndDate] = useState('2026-08-31')
  const [validationError, setValidationError] = useState('')

  const [selection, setSelection] = useState({
    startDate: '2026-08-01',
    endDate: '2026-08-31',
    revision: 0,
  })

  function handleApply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const first = Date.parse(`${startDate}T00:00:00Z`)
    const last = Date.parse(`${endDate}T00:00:00Z`)
    const days = (last - first) / 86_400_000 + 1

    if (!Number.isFinite(days) || days < 1 || days > 366) {
      setValidationError(
        'Choose a valid date range containing 1 to 366 days.',
      )
      return
    }

    setValidationError('')
    setSelection(previous => ({
      startDate,
      endDate,
      revision: previous.revision + 1,
    }))
  }

  return (
    <article
      className="pq-stage-chart"
      aria-labelledby="pq-daily-title"
    >
      <h3 id="pq-daily-title">Daily quality trend</h3>

      <p className="pq-note">
        Events are grouped by completion date in UTC.
        Issues = WARNING + FAILED.
        PENDING events and events without a completion date
        are excluded. Missing days are shown as gaps.
      </p>

      <form className="pq-controls" onSubmit={handleApply}>
        <label htmlFor="pq-start-date">Start date</label>
        <input
          id="pq-start-date"
          type="date"
          required
          value={startDate}
          onChange={event => setStartDate(event.target.value)}
        />

        <label htmlFor="pq-end-date">End date</label>
        <input
          id="pq-end-date"
          type="date"
          required
          value={endDate}
          onChange={event => setEndDate(event.target.value)}
        />

        <button type="submit">Apply dates</button>
      </form>

      {validationError && (
        <p role="alert" className="pq-error">
          {validationError}
        </p>
      )}

      <p className="pq-note">
        Displayed range: {selection.startDate}
        {' — '}{selection.endDate} (UTC)
      </p>

      <DailyResults
        key={`${prefix}:${selection.startDate}:${selection.endDate}:${selection.revision}`}
        prefix={prefix}
        startDate={selection.startDate}
        endDate={selection.endDate}
      />
    </article>
  )
}