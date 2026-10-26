import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { WorkflowProvider } from './context/WorkflowContext';
import AppShell from './components/layout/AppShell';
import WelcomePage from './pages/WelcomePage';
import InterviewPage from './pages/InterviewPage';
import ProfileReviewPage from './pages/ProfileReviewPlaceholder';
import AssessmentPage from './pages/AssessmentPage';
import MatchesPage from './pages/MatchesPage';

export function App() {
  return (
    <WorkflowProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/profile/review" element={<ProfileReviewPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/matches" element={<MatchesPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </WorkflowProvider>
  );
}

export default App;
