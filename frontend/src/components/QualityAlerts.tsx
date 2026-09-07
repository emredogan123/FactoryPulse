import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

import {
  acknowledgeQualityAlert,
  getQualityAlerts,
} from '../api'
import type { QualityAlert } from '../types'

import './QualityAlerts.css'

type ReviewFilter = 'pending' | 'reviewed' | 'all'

const PAGE_SIZE = 20

function getErrorMessage(cause: unknown): string {
  const status = axios.isAxiosError(cause)
    ? cause.response?.status
    : undefined

  if (status === 401) {
    return 'Your session has expired. Sign out and sign in again.'
  }

  if (status === 403) {
    return 'You do not have permission to perform this action.'
  }

  return 'The request could not be completed. Please refresh and try again.'
}

function AlertResults({
  dataset,
  reviewFilter,
  offset,
  canReview,
  onPrevious,
  onNext,
  onReload,
}: {
  dataset: string
  reviewFilter: ReviewFilter
  offset: number
  canReview: boolean
  onPrevious: () => void
  onNext: () => void
  onReload: () => void
}) {
  const [items, setItems] = useState<QualityAlert[] | null>(null)
  const [loadError, setLoadError] = useState('')
  const [actionError, setActionError] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const active = useRef(false)
  const saving = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false
    active.current = true

    async function load() {
      try {
        const result = await getQualityAlerts(
          {
            prefix: dataset === '*' ? undefined : dataset,
            acknowledged:
              reviewFilter === 'all'
                ? undefined
                : reviewFilter === 'reviewed',
            limit: PAGE_SIZE,
            offset,
          },
          controller.signal,
        )

        if (!cancelled) {
          setItems(result.items)
        }
      } catch (cause) {
        if (!cancelled) {
          setLoadError(getErrorMessage(cause))
        }
      }
    }

    void load()

    return () => {
      cancelled = true
      active.current = false
      controller.abort()
    }
  }, [dataset, reviewFilter, offset])

  async function handleReview(id: string) {
    if (saving.current || !canReview) {
      return
    }

    saving.current = true
    setBusyId(id)
    setActionError('')

    try {
      await acknowledgeQualityAlert(id)

      if (active.current) {
        onReload()
      }
    } catch (cause) {
      if (active.current) {
        setActionError(getErrorMessage(cause))
      }
    } finally {
      saving.current = false

      if (active.current) {
        setBusyId(null)
      }
    }
  }

  if (loadError) {
    return <p role="alert">{loadError}</p>
  }

  if (!items) {
    return <p role="status">Loading quality alerts...</p>
  }

  return (
    <>
      {actionError && <p role="alert">{actionError}</p>}

      {items.length === 0 ? (
        <p role="status">No alerts found on this page.</p>
      ) : (
        <div className="qa-table-scroll">
          <table className="data-table qa-table">
            <thead>
              <tr>
                <th scope="col">Date (UTC)</th>
                <th scope="col">Dataset</th>
                <th scope="col">Issues / Evaluated</th>
                <th scope="col">Issue rate</th>
                <th scope="col">Threshold</th>
                <th scope="col">Minimum events</th>
                <th scope="col">Status</th>
                <th scope="col">Action / Reviewed at</th>
              </tr>
            </thead>

            <tbody>
              {items.map(alert => {
                const reviewed = alert.acknowledged_at !== null

                return (
                  <tr key={alert.id}>
                    <td>{alert.quality_date}</td>

                    <td>
                      {alert.dataset_prefix || 'All records'}
                    </td>

                    <td>
                      {alert.issue_count.toLocaleString('en-US')}
                      {' / '}
                      {alert.evaluated_count.toLocaleString('en-US')}
                    </td>

                    <td className="qa-rate">
                      {alert.issue_rate.toFixed(2)}%
                    </td>

                    <td>
                      {alert.threshold_percent.toFixed(2)}%
                    </td>

                    <td>
                      {alert.minimum_count.toLocaleString('en-US')}
                    </td>

                    <td>
                      <span
                        className={`qa-badge ${
                          reviewed ? 'qa-reviewed' : 'qa-pending'
                        }`}
                      >
                        {reviewed ? 'Reviewed' : 'Needs review'}
                      </span>
                    </td>

                    <td>
                      {alert.acknowledged_at ? (
                        <time dateTime={alert.acknowledged_at}>
                          {new Date(alert.acknowledged_at)
                            .toISOString()
                            .replace('T', ' ')
                            .slice(0, 19)}
                          {' UTC'}
                        </time>
                      ) : canReview ? (
                        <button
                          type="button"
                          disabled={busyId !== null}
                          aria-label={
                            `Mark ${alert.quality_date} ` +
                            `${alert.dataset_prefix || 'all records'} as reviewed`
                          }
                          onClick={() => void handleReview(alert.id)}
                        >
                          {busyId === alert.id
                            ? 'Saving...'
                            : 'Mark as reviewed'}
                        </button>
                      ) : (
                        <span>Read only</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <nav className="qa-controls" aria-label="Quality alert pages">
        <button
          type="button"
          disabled={offset === 0 || busyId !== null}
          onClick={onPrevious}
        >
          Previous
        </button>

        <span>Page {Math.floor(offset / PAGE_SIZE) + 1}</span>

        <button
          type="button"
          disabled={items.length < PAGE_SIZE || busyId !== null}
          onClick={onNext}
        >
          Next
        </button>
      </nav>
    </>
  )
}

export function QualityAlerts({
  canReview,
}: {
  canReview: boolean
}) {
  const [dataset, setDataset] = useState('ML-TRAIN')
  const [reviewFilter, setReviewFilter] =
    useState<ReviewFilter>('pending')
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)

  function reload() {
    setOffset(0)
    setRevision(previous => previous + 1)
  }

  return (
    <section
      className="panel qa-panel"
      aria-labelledby="qa-title"
    >
      <h2 id="qa-title">Quality alerts</h2>

      <p className="qa-note">
        Alerts record days when the process issue rate exceeded
        the threshold with enough evaluated events.
        Issues = WARNING + FAILED.
        Reviewed means the alert has been inspected.
      </p>

      <div className="qa-controls">
        <label htmlFor="qa-dataset">Dataset</label>
        <select
          id="qa-dataset"
          value={dataset}
          onChange={event => {
            setDataset(event.target.value)
            setOffset(0)
          }}
        >
          <option value="ML-TRAIN">ML-TRAIN</option>
          <option value="ML-TEST">ML-TEST</option>
          <option value="">All-records analysis</option>
          <option value="*">All alert groups</option>
        </select>

        <label htmlFor="qa-status">Status</label>
        <select
          id="qa-status"
          value={reviewFilter}
          onChange={event => {
            setReviewFilter(event.target.value as ReviewFilter)
            setOffset(0)
          }}
        >
          <option value="pending">Needs review</option>
          <option value="reviewed">Reviewed</option>
          <option value="all">All statuses</option>
        </select>

        <button type="button" onClick={reload}>
          Refresh alerts
        </button>
      </div>

      <p className="qa-note">
        These filters apply only to the alert list.
        All-records analysis shows alerts generated for the
        combined dataset.
      </p>

      <AlertResults
        key={`${dataset}:${reviewFilter}:${offset}:${revision}`}
        dataset={dataset}
        reviewFilter={reviewFilter}
        offset={offset}
        canReview={canReview}
        onPrevious={() =>
          setOffset(previous => Math.max(0, previous - PAGE_SIZE))
        }
        onNext={() =>
          setOffset(previous => previous + PAGE_SIZE)
        }
        onReload={reload}
      />
    </section>
  )
}