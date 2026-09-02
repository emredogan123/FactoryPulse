import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getProductionOrders } from '../api'
import type {
  ProductionOrder,
  ProductionOrderStatus,
} from '../types'

const STATUS_LABELS: Record<
  ProductionOrderStatus,
  string
> = {
  PLANNED: 'Planned',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return 'Not specified'
  }

  return new Date(value).toLocaleDateString()
}

export function ProductionPage() {
  const [orders, setOrders] =
    useState<ProductionOrder[]>([])
  const [isLoading, setIsLoading] =
    useState(true)
  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    async function loadOrders(): Promise<void> {
      try {
        setIsLoading(true)
        setError(null)

        const data =
          await getProductionOrders()

        setOrders(data)
      } catch {
        setError(
          'Production orders could not be loaded.',
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadOrders()
  }, [])

  const summary = useMemo(
    () => ({
      total: orders.length,
      inProgress: orders.filter(
        (order) =>
          order.status === 'IN_PROGRESS',
      ).length,
      completed: orders.filter(
        (order) =>
          order.status === 'COMPLETED',
      ).length,
      targetQuantity: orders.reduce(
        (total, order) =>
          total + order.target_quantity,
        0,
      ),
    }),
    [orders],
  )

  return (
    <>
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">
            Manufacturing operations
          </p>
          <h1>Production</h1>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          Production data available
        </div>
      </header>

      <section className="metrics-grid">
        <article className="metric-card">
          <span>Total orders</span>
          <strong>{summary.total}</strong>
          <small>Registered production orders</small>
        </article>

        <article className="metric-card warning">
          <span>In progress</span>
          <strong>{summary.inProgress}</strong>
          <small>Currently being produced</small>
        </article>

        <article className="metric-card success">
          <span>Completed</span>
          <strong>{summary.completed}</strong>
          <small>Finished production orders</small>
        </article>

        <article className="metric-card">
          <span>Target quantity</span>
          <strong>
            {summary.targetQuantity.toLocaleString()}
          </strong>
          <small>Total planned PCB quantity</small>
        </article>
      </section>

      <section className="panel production-table-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">
              Order tracking
            </p>
            <h2>Production orders</h2>
          </div>
        </div>

        {isLoading && (
          <p className="muted">
            Loading production orders...
          </p>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {!isLoading
          && !error
          && orders.length === 0 && (
            <p className="muted">
              No production orders found.
            </p>
          )}

        {!isLoading && orders.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order code</th>
                  <th>Product</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Planned start</th>
                  <th>Planned end</th>
                </tr>
              </thead>

              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <strong>
                        {order.order_code}
                      </strong>
                    </td>
                    <td>{order.product_code}</td>
                    <td>
                      {order.target_quantity
                        .toLocaleString()}
                    </td>
                    <td>
                      <span
                        className={
                          `order-status ${order.status
                            .toLowerCase()}`
                        }
                      >
                        {
                          STATUS_LABELS[
                            order.status
                          ]
                        }
                      </span>
                    </td>
                    <td>
                      {formatDate(
                        order.planned_start_at,
                      )}
                    </td>
                    <td>
                      {formatDate(
                        order.planned_end_at,
                      )}
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