import {
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import App from '../App'
import {
    getAnalyticsOverview,
    getCurrentUser,
    getModelPerformance,
    getPCBRisks,
    getPCBUnits,
    getStoredToken,
} from '../api'

import { MemoryRouter } from 'react-router-dom'

vi.mock('../api', () => ({
    clearToken: vi.fn(),
    getAnalyticsOverview: vi.fn(),
    getCurrentUser: vi.fn(),
    getModelPerformance: vi.fn(),
    getPCBRisk: vi.fn(),
    getPCBRisks: vi.fn(),
    getPCBUnits: vi.fn(),
    getStoredToken: vi.fn(),
    login: vi.fn(),
    storeToken: vi.fn(),
}))


const user = {
    id: 'user-1',
    email: 'admin@factorypulse.dev',
    full_name: 'Emre Dogan',
    role: 'ADMIN' as const,
    is_active: true,
}

const overview = {
    production_order_count: 10,
    pcb_count: 5000,
    pcb_status_counts: {
        passed: 3991,
        failed: 396,
        rework: 613,
        queued: 0,
    },
    pass_rate: 79.82,
    failure_rate: 7.92,
    rework_rate: 12.26,
    process_event_count: 24185,
    quality_measurement_count: 48370,
    out_of_spec_measurement_count: 1009,
}

const pcbUnits = [
    {
        id: 'pcb-high',
        serial_number: 'ML-TEST-PCB-HIGH',
        production_order_id: 'order-1',
        material_lot_id: null,
        shift: 'DAY' as const,
        status: 'FAILED' as const,
        created_at: '2026-08-28T08:00:00Z',
        updated_at: '2026-08-28T08:00:00Z',
    },
    {
        id: 'pcb-low',
        serial_number: 'ML-TEST-PCB-LOW',
        production_order_id: 'order-1',
        material_lot_id: null,
        shift: 'DAY' as const,
        status: 'PASSED' as const,
        created_at: '2026-08-28T08:01:00Z',
        updated_at: '2026-08-28T08:01:00Z',
    },
]

const riskList = {
    total_analyzed: 2,
    high_risk_count: 1,
    medium_risk_count: 0,
    low_risk_count: 1,
    items: [
        {
            pcb_id: 'pcb-high',
            serial_number: 'ML-TEST-PCB-HIGH',
            actual_status: 'FAILED' as const,
            issue_probability: 0.91,
            decision_threshold: 0.44,
            predicted_issue: true,
            risk_level: 'HIGH' as const,
            model_type: 'random_forest',
        },
        {
            pcb_id: 'pcb-low',
            serial_number: 'ML-TEST-PCB-LOW',
            actual_status: 'PASSED' as const,
            issue_probability: 0.08,
            decision_threshold: 0.44,
            predicted_issue: false,
            risk_level: 'LOW' as const,
            model_type: 'random_forest',
        },
    ],
}

const performance = {
    model_name: 'FactoryPulse PCB Risk Model',
    model_type: 'random_forest',
    evaluated_at: '2026-08-28T08:05:32Z',
    dataset: {
        name: 'ml_test.csv',
        row_count: 2000,
        issue_count: 367,
        issue_rate: 0.1835,
    },
    decision_threshold: 0.44,
    feature_count: 21,
    metrics: {
        accuracy: 0.9105,
        precision: 0.76257,
        recall: 0.743869,
        f1_score: 0.753103,
        roc_auc: 0.913788,
    },
    confusion_matrix: {
        true_negative: 1548,
        false_positive: 85,
        false_negative: 94,
        true_positive: 273,
    },
    feature_importances: [
        {
            feature:
                'numeric__reflow_soldering__param__drift_score',
            importance: 0.113757,
        },
    ],
}


function mockDashboardRequests(): void {
    vi.mocked(getCurrentUser)
        .mockResolvedValue(user)

    vi.mocked(getAnalyticsOverview)
        .mockResolvedValue(overview)

    vi.mocked(getPCBUnits)
        .mockResolvedValue(pcbUnits)

    vi.mocked(getPCBRisks)
        .mockResolvedValue(riskList)

    vi.mocked(getModelPerformance)
        .mockResolvedValue(performance)
}


describe('FactoryPulse App', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('shows the login screen without a token', async () => {
        vi.mocked(getStoredToken)
            .mockReturnValue(null)

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>,
        )

        expect(
            await screen.findByRole(
                'heading',
                {
                    name: 'Welcome back',
                },
            ),
        ).toBeInTheDocument()

        expect(
            screen.getByLabelText('Email'),
        ).toBeInTheDocument()

        expect(
            screen.getByRole(
                'button',
                {
                    name: 'Sign in',
                },
            ),
        ).toBeInTheDocument()
    })

    it('loads the authenticated dashboard', async () => {
        vi.mocked(getStoredToken)
            .mockReturnValue('test-token')

        mockDashboardRequests()

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>,
        )

        expect(
            await screen.findByRole(
                'heading',
                {
                    name: 'Quality dashboard',
                },
            ),
        ).toBeInTheDocument()

        expect(
            screen.getByText(/5[.,]000/),
        ).toBeInTheDocument()

        expect(
            screen.getByText('91.4%'),
        ).toBeInTheDocument()

        expect(
            screen.getByText(
                'ML-TEST-PCB-HIGH',
            ),
        ).toBeInTheDocument()

        expect(
            getModelPerformance,
        ).toHaveBeenCalledOnce()
    })

    it('filters the risk table by risk level', async () => {
        vi.mocked(getStoredToken)
            .mockReturnValue('test-token')

        mockDashboardRequests()

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>,
        )

        await screen.findByRole(
            'heading',
            {
                name: 'Quality dashboard',
            },
        )

        expect(
            screen.getByText(
                'ML-TEST-PCB-HIGH',
            ),
        ).toBeInTheDocument()

        expect(
            screen.getByText(
                'ML-TEST-PCB-LOW',
            ),
        ).toBeInTheDocument()

        fireEvent.click(
            screen.getByRole(
                'button',
                {
                    name: 'HIGH',
                },
            ),
        )

        await waitFor(() => {
            expect(
                screen.getByText(
                    'ML-TEST-PCB-HIGH',
                ),
            ).toBeInTheDocument()

            expect(
                screen.queryByText(
                    'ML-TEST-PCB-LOW',
                ),
            ).not.toBeInTheDocument()
        })
    })
})