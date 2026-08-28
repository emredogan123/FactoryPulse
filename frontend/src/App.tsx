import axios from 'axios'
import {
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { FormEvent } from 'react'

import {
  clearToken,
  getAnalyticsOverview,
  getCurrentUser,
  getPCBRisk,
  getPCBUnits,
  getStoredToken,
  login,
  storeToken,
  getPCBRisks,
} from './api'
import type {
  AnalyticsOverview,
  PCBRiskPrediction,
  PCBUnit,
  User,
  PCBRiskListResponse,
  RiskLevel,
} from './types'
import './App.css'


function getErrorMessage(
  error: unknown,
): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (!error.response) {
      return (
        'Backend connection failed. '
        + 'Make sure the API is running.'
      )
    }
  }

  return 'An unexpected error occurred.'
}


function App() {
  const [user, setUser] =
    useState<User | null>(null)

  const [overview, setOverview] =
    useState<AnalyticsOverview | null>(null)

  const [pcbUnits, setPCBUnits] =
    useState<PCBUnit[]>([])

  const [selectedPCBId, setSelectedPCBId] =
    useState('')

  const [prediction, setPrediction] =
    useState<PCBRiskPrediction | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] =
    useState('')
  const [search, setSearch] =
    useState('ML-TEST')

  const [isBooting, setIsBooting] =
    useState(true)
  const [isLoggingIn, setIsLoggingIn] =
    useState(false)
  const [isLoadingDashboard, setIsLoadingDashboard] =
    useState(false)
  const [isPredicting, setIsPredicting] =
    useState(false)
  const [error, setError] =
    useState<string | null>(null)

  const [riskList, setRiskList] =
    useState<PCBRiskListResponse | null>(
      null,
    )

  const [riskFilter, setRiskFilter] =
    useState<RiskLevel | 'ALL'>('ALL')

  const filteredPCBs = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase()

    const matchingPCBs = normalizedSearch
      ? pcbUnits.filter((pcb) =>
        pcb.serial_number
          .toLowerCase()
          .includes(normalizedSearch),
      )
      : pcbUnits

    return matchingPCBs.slice(0, 100)
  }, [pcbUnits, search])

  const filteredRisks = useMemo(() => {
    if (!riskList) {
      return []
    }

    return riskList.items
      .filter(
        (item) =>
          riskFilter === 'ALL'
          || item.risk_level === riskFilter,
      )
      .sort(
        (first, second) =>
          second.issue_probability
          - first.issue_probability,
      )
  }, [riskList, riskFilter])

  async function loadDashboard(): Promise<void> {
    setIsLoadingDashboard(true)
    setError(null)

    try {
      const [
        overviewData,
        pcbData,
        riskData,
      ] = await Promise.all([
        getAnalyticsOverview(),
        getPCBUnits(),
        getPCBRisks('ML-TEST', 50),
      ])

      setOverview(overviewData)
      setPCBUnits(pcbData)
      setRiskList(riskData)

      const preferredPCB =
        pcbData.find((pcb) =>
          pcb.serial_number.startsWith(
            'ML-TEST-',
          ),
        ) ?? pcbData[0]

      if (preferredPCB) {
        setSelectedPCBId(preferredPCB.id)
      }
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      )
    } finally {
      setIsLoadingDashboard(false)
    }
  }

  useEffect(() => {
    async function restoreSession(): Promise<void> {
      const token = getStoredToken()

      if (!token) {
        setIsBooting(false)
        return
      }

      try {
        const currentUser =
          await getCurrentUser()

        setUser(currentUser)
        await loadDashboard()
      } catch {
        clearToken()
        setUser(null)
      } finally {
        setIsBooting(false)
      }
    }

    void restoreSession()
  }, [])

  async function handleLogin(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    setIsLoggingIn(true)
    setError(null)

    try {
      const tokenResponse =
        await login(email, password)

      storeToken(
        tokenResponse.access_token,
      )

      const currentUser =
        await getCurrentUser()

      setUser(currentUser)
      await loadDashboard()
    } catch (requestError) {
      clearToken()
      setError(
        getErrorMessage(requestError),
      )
    } finally {
      setIsLoggingIn(false)
    }
  }

  function handleLogout(): void {
    clearToken()
    setUser(null)
    setOverview(null)
    setPCBUnits([])
    setPrediction(null)
    setPassword('')
    setError(null)
    setRiskList(null)
  }

  async function handlePrediction(): Promise<void> {
    if (!selectedPCBId) {
      return
    }

    setIsPredicting(true)
    setPrediction(null)
    setError(null)

    try {
      const result =
        await getPCBRisk(selectedPCBId)

      setPrediction(result)
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      )
    } finally {
      setIsPredicting(false)
    }
  }

  if (isBooting) {
    return (
      <main className="loading-screen">
        <div className="pulse-mark">
          FP
        </div>
        <p>Starting FactoryPulse...</p>
      </main>
    )
  }

  if (!user) {
    return (
      <main className="login-page">
        <section className="login-brand">
          <div className="brand-mark">FP</div>
          <p className="eyebrow">
            Manufacturing Intelligence
          </p>
          <h1>
            See quality risks before they
            become production losses.
          </h1>
          <p className="login-description">
            FactoryPulse combines process
            data, quality signals and machine
            learning in one operational
            dashboard.
          </p>
        </section>

        <section className="login-panel">
          <form
            className="login-card"
            onSubmit={handleLogin}
          >
            <div>
              <p className="eyebrow">
                Secure access
              </p>
              <h2>Welcome back</h2>
              <p className="muted">
                Sign in with your FactoryPulse
                account.
              </p>
            </div>

            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@factorypulse.dev"
                autoComplete="username"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </label>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={isLoggingIn}
            >
              {isLoggingIn
                ? 'Signing in...'
                : 'Sign in'}
            </button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">
            FP
          </div>
          <div>
            <strong>FactoryPulse</strong>
            <span>Quality Intelligence</span>
          </div>
        </div>

        <nav>
          <button className="nav-item active">
            <span>⌁</span>
            Overview
          </button>
          <button className="nav-item">
            <span>◇</span>
            PCB Risk
          </button>
          <button className="nav-item">
            <span>▥</span>
            Production
          </button>
          <button className="nav-item">
            <span>◉</span>
            Machines
          </button>
        </nav>

        <div className="sidebar-user">
          <div className="avatar">
            {user.full_name
              .slice(0, 1)
              .toUpperCase()}
          </div>
          <div>
            <strong>{user.full_name}</strong>
            <span>{user.role}</span>
          </div>
          <button
            className="logout-button"
            onClick={handleLogout}
            title="Sign out"
          >
            ↗
          </button>
        </div>
      </aside>

      <main className="dashboard">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">
              Live production overview
            </p>
            <h1>Quality dashboard</h1>
          </div>

          <div className="system-status">
            <span className="status-dot" />
            Systems operational
          </div>
        </header>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isLoadingDashboard && (
          <div className="panel">
            Loading dashboard data...
          </div>
        )}

        {overview && (
          <section className="metrics-grid">
            <article className="metric-card">
              <span>Total PCBs</span>
              <strong>
                {overview.pcb_count.toLocaleString()}
              </strong>
              <small>
                {
                  overview.production_order_count
                } production orders
              </small>
            </article>

            <article className="metric-card success">
              <span>Pass rate</span>
              <strong>
                {overview.pass_rate.toFixed(1)}%
              </strong>
              <small>
                {
                  overview.pcb_status_counts
                    .passed
                } passed units
              </small>
            </article>

            <article className="metric-card danger">
              <span>Failure rate</span>
              <strong>
                {overview.failure_rate.toFixed(1)}%
              </strong>
              <small>
                {
                  overview.pcb_status_counts
                    .failed
                } failed units
              </small>
            </article>

            <article className="metric-card warning">
              <span>Out of spec</span>
              <strong>
                {
                  overview
                    .out_of_spec_measurement_count
                }
              </strong>
              <small>
                {
                  overview
                    .quality_measurement_count
                } measurements
              </small>
            </article>
          </section>
        )}

        <section className="content-grid">
          <article className="panel risk-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  ML risk analysis
                </p>
                <h2>PCB risk prediction</h2>
              </div>
              <span className="model-chip">
                Random Forest
              </span>
            </div>

            <label className="search-field">
              Search serial number
              <input
                value={search}
                onChange={(event) => {
                  setSearch(
                    event.target.value,
                  )
                  setPrediction(null)
                }}
                placeholder="ML-TEST-PCB..."
              />
            </label>

            <label className="search-field">
              Select PCB
              <select
                value={selectedPCBId}
                onChange={(event) => {
                  setSelectedPCBId(
                    event.target.value,
                  )
                  setPrediction(null)
                }}
              >
                <option value="">
                  Select a PCB
                </option>
                {filteredPCBs.map((pcb) => (
                  <option
                    key={pcb.id}
                    value={pcb.id}
                  >
                    {pcb.serial_number}
                    {' · '}
                    {pcb.status}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="primary-button"
              onClick={handlePrediction}
              disabled={
                !selectedPCBId
                || isPredicting
              }
            >
              {isPredicting
                ? 'Analyzing...'
                : 'Analyze risk'}
            </button>
          </article>

          <article className="panel prediction-panel">
            {!prediction ? (
              <div className="empty-state">
                <div className="empty-icon">◎</div>
                <h2>No prediction yet</h2>
                <p>
                  Select a PCB to calculate its
                  quality risk.
                </p>
              </div>
            ) : (
              <>
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">
                      Prediction result
                    </p>
                    <h2>
                      {prediction.serial_number}
                    </h2>
                  </div>

                  <span
                    className={
                      `risk-badge ${prediction.risk_level
                        .toLowerCase()
                      }`
                    }
                  >
                    {prediction.risk_level}
                  </span>
                </div>

                <div className="probability">
                  <strong>
                    {(
                      prediction
                        .issue_probability * 100
                    ).toFixed(1)}
                    %
                  </strong>
                  <span>
                    Issue probability
                  </span>
                </div>

                <div className="progress-track">
                  <div
                    className={
                      `progress-fill ${prediction.risk_level
                        .toLowerCase()
                      }`
                    }
                    style={{
                      width: `${prediction
                        .issue_probability * 100
                        }%`,
                    }}
                  />
                  <span
                    className="threshold-marker"
                    style={{
                      left: `${prediction
                        .decision_threshold * 100
                        }%`,
                    }}
                  />
                </div>

                <div className="prediction-meta">
                  <div>
                    <span>Threshold</span>
                    <strong>
                      {(
                        prediction
                          .decision_threshold * 100
                      ).toFixed(0)}
                      %
                    </strong>
                  </div>
                  <div>
                    <span>Decision</span>
                    <strong>
                      {prediction.predicted_issue
                        ? 'Inspection required'
                        : 'Normal flow'}
                    </strong>
                  </div>
                  <div>
                    <span>Model</span>
                    <strong>
                      {prediction.model_type}
                    </strong>
                  </div>
                </div>
              </>
            )}
          </article>
        </section>
        <section className="panel risk-table-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                Prioritized inspection queue
              </p>
              <h2>Recent PCB risk analysis</h2>
            </div>

            <div className="risk-summary">
              <span className="summary-high">
                {riskList?.high_risk_count ?? 0}
                {' '}high
              </span>
              <span className="summary-medium">
                {riskList?.medium_risk_count ?? 0}
                {' '}medium
              </span>
              <span className="summary-low">
                {riskList?.low_risk_count ?? 0}
                {' '}low
              </span>
            </div>
          </div>

          <div className="risk-toolbar">
            {(
              [
                'ALL',
                'HIGH',
                'MEDIUM',
                'LOW',
              ] as const
            ).map((level) => (
              <button
                key={level}
                className={
                  riskFilter === level
                    ? 'filter-button active'
                    : 'filter-button'
                }
                onClick={() =>
                  setRiskFilter(level)
                }
              >
                {level}
              </button>
            ))}
          </div>

          <div className="table-wrapper">
            <table className="risk-table">
              <thead>
                <tr>
                  <th>PCB serial</th>
                  <th>Actual status</th>
                  <th>Risk probability</th>
                  <th>Risk level</th>
                  <th>Prediction</th>
                </tr>
              </thead>

              <tbody>
                {filteredRisks.map((item) => {
                  const actualIssue =
                    item.actual_status === 'FAILED'
                    || item.actual_status === 'REWORK'

                  const isCorrect =
                    actualIssue
                    === item.predicted_issue

                  return (
                    <tr
                      key={item.pcb_id}
                      onClick={() => {
                        setSelectedPCBId(
                          item.pcb_id,
                        )
                        setPrediction(item)
                      }}
                    >
                      <td>
                        <strong>
                          {item.serial_number}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={
                            `status-label ${item.actual_status
                              .toLowerCase()
                            }`
                          }
                        >
                          {item.actual_status}
                        </span>
                      </td>

                      <td>
                        <div className="table-risk-value">
                          <strong>
                            {(
                              item.issue_probability
                              * 100
                            ).toFixed(1)}
                            %
                          </strong>
                          <div>
                            <span
                              style={{
                                width: `${item.issue_probability
                                  * 100
                                  }%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>

                      <td>
                        <span
                          className={
                            `risk-badge ${item.risk_level
                              .toLowerCase()
                            }`
                          }
                        >
                          {item.risk_level}
                        </span>
                      </td>

                      <td>
                        <span
                          className={
                            isCorrect
                              ? 'prediction-correct'
                              : 'prediction-incorrect'
                          }
                        >
                          {isCorrect
                            ? 'Correct'
                            : 'Mismatch'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App