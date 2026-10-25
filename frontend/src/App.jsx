import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { WorkflowProvider } from './context/WorkflowContext';
import AppShell from './components/layout/AppShell';
import WelcomePage from './pages/WelcomePage';
import InterviewPlaceholder from './pages/InterviewPlaceholder';
import ProfileReviewPlaceholder from './pages/ProfileReviewPlaceholder';
import AssessmentPlaceholder from './pages/AssessmentPlaceholder';
import MatchesPlaceholder from './pages/MatchesPlaceholder';

export function App() {
  return (
    <WorkflowProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/interview" element={<InterviewPlaceholder />} />
            <Route path="/profile/review" element={<ProfileReviewPlaceholder />} />
            <Route path="/assessment" element={<AssessmentPlaceholder />} />
            <Route path="/matches" element={<MatchesPlaceholder />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </WorkflowProvider>
  );
}

export default App;
