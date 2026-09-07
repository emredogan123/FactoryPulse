import { useEffect, useState } from 'react'
import axios from 'axios'
import { StageQualityChart } from './StageQualityChart'
import { getProductionQuality } from '../api'
import type {
    ProductionQualityResponse,
    QualityCounts,
} from '../types'

import './ProductionQualityCharts.css'
import { DailyQualityChart } from './DailyQualityChart'

function formatCount(value: number): string {
    return value.toLocaleString('en-US')
}

function formatRate(value: number | null): string {
    return value === null
        ? 'No data'
        : `${value.toFixed(2)}%`
}

function QualityRow({
    label,
    values,
}: {
    label: string
    values: QualityCounts
}) {
    return (
        <li className="pq-row">
            <div className="pq-row-title">
                <strong>{label}</strong>
                <span>{formatRate(values.issue_rate)}</span>
            </div>

            {values.issue_rate !== null && (
                <div className="pq-track" aria-hidden="true">
                    <span
                        style={{
                            width: `${Math.max(0, Math.min(100, values.issue_rate))
                                }%`,
                        }}
                    />
                </div>
            )}

            <small>
                {formatCount(values.issue_count)} issues
                {' / '}
                {formatCount(values.evaluated_count)} evaluated
                {' · '}
                {formatCount(values.pending_count)} pending
            </small>
        </li>
    )
}

function QualityResults({ prefix }: { prefix: string }) {
    const [result, setResult] =
        useState<ProductionQualityResponse | null>(null)

    const [error, setError] = useState('')

    useEffect(() => {
        const controller = new AbortController()
        let active = true

        async function load(): Promise<void> {
            try {
                const data = await getProductionQuality(
                    prefix || undefined,
                    controller.signal,
                )

                if (active) {
                    setResult(data)
                }
            } catch (cause) {
                if (!active) {
                    return
                }

                const status = axios.isAxiosError(cause)
                    ? cause.response?.status
                    : undefined

                if (status === 401) {
                    setError(
                        'Your session has expired. Sign out and sign in again.',
                    )
                } else if (status === 403) {
                    setError(
                        'You do not have permission to view production quality.',
                    )
                } else {
                    setError(
                        'Production quality could not be loaded. '
                        + 'Check the backend and try again.',
                    )
                }
            }
        }

        void load()

        return () => {
            active = false
            controller.abort()
        }
    }, [prefix])

    if (error) {
        return (
            <p role="alert" className="pq-error">
                {error}
            </p>
        )
    }

    if (!result) {
        return (
            <p role="status">
                Loading production quality...
            </p>
        )
    }

    if (result.summary.total_count === 0) {
        return (
            <p role="status">
                No PCB records found for this selection.
            </p>
        )
    }

    return (
        <>
            <div className="pq-summary">
                <div>
                    <span>Selected PCBs</span>
                    <strong>
                        {formatCount(result.summary.total_count)}
                    </strong>
                </div>

                <div>
                    <span>Evaluated</span>
                    <strong>
                        {formatCount(result.summary.evaluated_count)}
                    </strong>
                </div>

                <div>
                    <span>Pending</span>
                    <strong>
                        {formatCount(result.summary.pending_count)}
                    </strong>
                </div>

                <div>
                    <span>Issue rate</span>
                    <strong>
                        {formatRate(result.summary.issue_rate)}
                    </strong>
                </div>
            </div>

            <div className="pq-grid">
                <article
                    className="pq-chart"
                    aria-labelledby="pq-shifts-title"
                >
                    <h3 id="pq-shifts-title">
                        Issues by shift
                    </h3>

                    <div className="pq-scale" aria-hidden="true">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                    </div>

                    <ul>
                        {result.shifts.map(item => (
                            <QualityRow
                                key={item.shift}
                                label={item.shift}
                                values={item}
                            />
                        ))}
                    </ul>
                </article>

                <article
                    className="pq-chart"
                    aria-labelledby="pq-lots-title"
                >
                    <h3 id="pq-lots-title">
                        Issues by material lot
                    </h3>

                    <div className="pq-scale" aria-hidden="true">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                    </div>

                    <ul
                        className="pq-lots"
                        tabIndex={0}
                        aria-label="Material lot quality results"
                    >
                        {result.material_lots.map(item => (
                            <QualityRow
                                key={item.material_lot_id ?? 'no-lot'}
                                label={item.lot_code ?? 'No material lot'}
                                values={item}
                            />
                        ))}
                    </ul>
                </article>
            </div>
        </>
    )
}

export function ProductionQualityCharts() {
    const [prefix, setPrefix] = useState('ML-TRAIN')
    const [revision, setRevision] = useState(0)

    return (
        <section
            className="panel pq-section"
            aria-labelledby="pq-title"
        >
            <div className="pq-heading">
                <div>
                    <p className="eyebrow">
                        Production quality analysis
                    </p>

                    <h2 id="pq-title">
                        Shift and material quality
                    </h2>
                </div>

                <div className="pq-controls">
                    <label htmlFor="pq-prefix">
                        Quality dataset
                    </label>

                    <select
                        id="pq-prefix"
                        value={prefix}
                        onChange={event => setPrefix(event.target.value)}
                    >
                        <option value="ML-TRAIN">ML-TRAIN</option>
                        <option value="ML-TEST">ML-TEST</option>
                        <option value="">All records</option>
                    </select>

                    <button
                        type="button"
                        onClick={() => setRevision(value => value + 1)}
                    >
                        Refresh quality
                    </button>
                </div>
            </div>

            <p className="pq-note">
                Observed issues = FAILED + REWORK.
                Rates use PASSED, FAILED and REWORK records only.
                Pending records are excluded.
                This filter applies only to this section.
            </p>

            <QualityResults
  key={`quality:${prefix}:${revision}`}
  prefix={prefix}
/>

<StageQualityChart
  key={`stages:${prefix}:${revision}`}
  prefix={prefix}
/>

<DailyQualityChart
  key={`daily:${prefix}:${revision}`}
  prefix={prefix}
/>
        </section>
    )
}