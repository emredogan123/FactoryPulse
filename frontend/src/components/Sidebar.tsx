import { NavLink } from 'react-router-dom'

import type { User } from '../types'

interface SidebarProps {
    user: User
    onLogout: () => void
}

const navigationItems = [
    {
        path: '/',
        icon: '⌁',
        label: 'Overview',
    },
    {
        path: '/pcb-risk',
        icon: '◇',
        label: 'PCB Risk',
    },
    {
        path: '/production',
        icon: '▥',
        label: 'Production',
    },
    {
        path: '/machines',
        icon: '◉',
        label: 'Machines',
    },
]

export function Sidebar({
    user,
    onLogout,
}: SidebarProps) {
    return (
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
                {navigationItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) =>
                            isActive
                                ? 'nav-item active'
                                : 'nav-item'
                        }
                    >
                        <span>{item.icon}</span>
                        {item.label}
                    </NavLink>
                ))}
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
                    onClick={onLogout}
                    title="Sign out"
                    type="button"
                >
                    ↗
                </button>
            </div>
        </aside>
    )
}