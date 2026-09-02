import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getMachines } from '../api'
import type {
  Machine,
  MachineStatus,
} from '../types'

const STATUS_LABELS: Record<
  MachineStatus,
  string
> = {
  ACTIVE: 'Active',
  MAINTENANCE: 'Maintenance',
  OFFLINE: 'Offline',
}

function formatStage(stage: string): string {
  return stage
    .toLowerCase()
    .split('_')
    .map(
      (word) =>
        word.charAt(0).toUpperCase()
        + word.slice(1),
    )
    .join(' ')
}

export function MachinesPage() {
  const [machines, setMachines] =
    useState<Machine[]>([])
  const [isLoading, setIsLoading] =
    useState(true)
  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    async function loadMachines(): Promise<void> {
      try {
        setIsLoading(true)
        setError(null)

        const data = await getMachines()
        setMachines(data)
      } catch {
        setError(
          'Machine data could not be loaded.',
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadMachines()
  }, [])

  const statusCounts = useMemo(
    () => ({
      active: machines.filter(
        (machine) =>
          machine.status === 'ACTIVE',
      ).length,
      maintenance: machines.filter(
        (machine) =>
          machine.status === 'MAINTENANCE',
      ).length,
      offline: machines.filter(
        (machine) =>
          machine.status === 'OFFLINE',
      ).length,
    }),
    [machines],
  )

  return (
    <>
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">
            Production infrastructure
          </p>
          <h1>Machines</h1>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          Live machine inventory
        </div>
      </header>

      <section className="metrics-grid">
        <article className="metric-card">
          <span>Total machines</span>
          <strong>{machines.length}</strong>
          <small>Registered equipment</small>
        </article>

        <article className="metric-card success">
          <span>Active</span>
          <strong>{statusCounts.active}</strong>
          <small>Available for production</small>
        </article>

        <article className="metric-card warning">
          <span>Maintenance</span>
          <strong>
            {statusCounts.maintenance}
          </strong>
          <small>Under maintenance</small>
        </article>

        <article className="metric-card danger">
          <span>Offline</span>
          <strong>{statusCounts.offline}</strong>
          <small>Currently unavailable</small>
        </article>
      </section>

      <section className="panel machine-table-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">
              Equipment status
            </p>
            <h2>Production machines</h2>
          </div>
        </div>

        {isLoading && (
          <p className="muted">
            Loading machines...
          </p>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {!isLoading
          && !error
          && machines.length === 0 && (
            <p className="muted">
              No machines found.
            </p>
          )}

        {!isLoading && machines.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Machine code</th>
                  <th>Name</th>
                  <th>Production stage</th>
                  <th>Status</th>
                  <th>Commissioned</th>
                </tr>
              </thead>

              <tbody>
                {machines.map((machine) => (
                  <tr key={machine.id}>
                    <td>
                      <strong>
                        {machine.machine_code}
                      </strong>
                    </td>
                    <td>{machine.name}</td>
                    <td>
                      {formatStage(
                        machine.stage_type,
                      )}
                    </td>
                    <td>
                      <span
                        className={
                          `machine-status ${machine.status
                            .toLowerCase()}`
                        }
                      >
                        {
                          STATUS_LABELS[
                            machine.status
                          ]
                        }
                      </span>
                    </td>
                    <td>
                      {machine.commissioned_at
                        ? new Date(
                          machine.commissioned_at,
                        ).toLocaleDateString()
                        : 'Not specified'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}