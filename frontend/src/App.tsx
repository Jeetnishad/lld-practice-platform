import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { DashboardPage } from './pages/DashboardPage'
import { ProblemsPage } from './pages/ProblemsPage'
import { ProblemDetailPage } from './pages/ProblemDetailPage'
import { WorkspacePage } from './pages/WorkspacePage'
import { FeedbackPage } from './pages/FeedbackPage'
import { HistoryPage } from './pages/HistoryPage'

function NotFound() {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', height: '100vh', gap: 12, textAlign: 'center',
    }}>
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: 48, fontWeight: 700,
        color: '#0EA5A0', letterSpacing: '-0.04em',
      }}>404</span>
      <p style={{ fontSize: 13, color: '#8B97A4' }}>Page not found</p>
      <a href="/" style={{ fontSize: 12, color: '#0EA5A0', textDecoration: 'none' }}>
        Return home
      </a>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/problems" element={<ProblemsPage />} />
        <Route path="/problems/:id" element={<ProblemDetailPage />} />
        <Route path="/attempt/:id" element={<WorkspacePage />} />
        <Route path="/attempt/:id/feedback" element={<FeedbackPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
