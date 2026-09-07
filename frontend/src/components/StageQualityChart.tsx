import { useEffect, useState } from 'react'
import axios from 'axios'

import { getStageQuality } from '../api'
import type {
  StageQualityResponse,
  StageType,
} from '../types'

const STAGE_LABELS: Record<StageType, string> = {
  SOLDER_PASTE_PRINTING: 'Solder Paste Printing',
  COMPONENT_PLACEMENT: 'Component Placement',
  REFLOW_SOLDERING: 'Reflow Soldering',
  AOI_INSPECTION: 'AOI Inspection',
  FUNCTIONAL_TESTING: 'Functional Testing',
}

export function StageQualityChart({
  prefix,
}: {
  prefix: string
}) {
  const [data, setData] =
    useState<StageQualityResponse | null>(null)

  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function load(): Promise<void> {
      try {
        const result = await getStageQuality(
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
              ? 'You do not have permission to view stage quality.'
              : 'Stage quality could not be loaded. Use Refresh quality to try again.',
        )
      }
    }

    void load()

    return () => {
      active = false
      controller.abort()
    }
  }, [prefix])

  return (
    <article
      className="pq-stage-chart pq-chart"
      aria-labelledby="pq-stage-title"
    >
      <h3 id="pq-stage-title">
        Issues by production stage
      </h3>

      <p className="pq-note">
        Process event rates, not unique PCB rates.
        Issues = WARNING + FAILED.
        PENDING records are excluded.
      </p>

      {error ? (
        <p role="alert" className="pq-error">
          {error}
        </p>
      ) : !data ? (
        <p role="status">
          Loading stage quality...
        </p>
      ) : !data.stages.some(stage => stage.total_count > 0) ? (
        <p role="status">
          No process events found for this selection.
        </p>
      ) : (
        <>
          <div className="pq-stage-legend">
            <span>
              <i className="pq-warning-color" />
              WARNING
            </span>
            <span>
              <i className="pq-failed-color" />
              FAILED
            </span>
          </div>

          <div className="pq-scale" aria-hidden="true">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>

          <ul>
            {data.stages.map(stage => {
              const evaluated = stage.evaluated_count

              const warningWidth = evaluated
                ? 100 * stage.warning_count / evaluated
                : 0

              const failedWidth = evaluated
                ? 100 * stage.failed_count / evaluated
                : 0

              return (
                <li
                  key={stage.stage_type}
                  className="pq-row"
                >
                  <div className="pq-row-title">
                    <strong>
                      {STAGE_LABELS[stage.stage_type]}
                    </strong>

                    <span>
                      {stage.issue_rate === null
                        ? 'No data'
                        : `${stage.issue_rate.toFixed(2)}%`}
                    </span>
                  </div>

                  {stage.issue_rate !== null && (
                    <div
                      className="pq-track pq-stage-track"
                      aria-hidden="true"
                    >
                      <span
                        className="pq-warning-color"
                        style={{
                          width: `${warningWidth}%`,
                        }}
                      />
                      <span
                        className="pq-failed-color"
                        style={{
                          width: `${failedWidth}%`,
                        }}
                      />
                    </div>
                  )}

                  <small>
                    {stage.warning_count.toLocaleString('en-US')} warning
                    {' · '}
                    {stage.failed_count.toLocaleString('en-US')} failed
                    {' · '}
                    {evaluated.toLocaleString('en-US')} evaluated
                    {' · '}
                    {stage.pending_count.toLocaleString('en-US')} pending
                  </small>
                </li>
              )
            })}
          </ul>
        </>
      )}
    </article>
  )
}