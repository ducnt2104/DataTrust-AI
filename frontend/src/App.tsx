import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import { SurveysListPage } from './pages/SurveysListPage';
import { SurveyBuilderPage } from './pages/SurveyBuilderPage';
import { PublicSurveyPage } from './pages/PublicSurveyPage';
import { SurveyAnalyticsPage } from './pages/SurveyAnalyticsPage';
import { ResponsesListPage } from './pages/ResponsesListPage';
import { ResponseDetailPage } from './pages/ResponseDetailPage';
import { ResponseComparePage } from './pages/ResponseComparePage';
import { ExportImportPage } from './pages/ExportImportPage';
import { PaperSurveyPage } from './pages/PaperSurveyPage';
import { EnumeratorAnalyticsPage } from './pages/EnumeratorAnalyticsPage';
import { PublicCertificateVerifyPage } from './pages/PublicCertificateVerifyPage';

export function App() {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname || '/');

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo(0, 0);
  };

  // Check if current route is a Public Survey Page: /s/:slug or /survey/:id
  const publicSlugMatch = currentPath.match(/^\/s\/([^/]+)/);
  const publicSurveyMatch = currentPath.match(/^\/survey\/([^/]+)/);

  if (publicSlugMatch || publicSurveyMatch) {
    const slug = (publicSlugMatch ? publicSlugMatch[1] : publicSurveyMatch![1]);
    return (
      <ErrorBoundary>
        <PublicSurveyPage slug={slug} onNavigate={navigate} />
      </ErrorBoundary>
    );
  }

  // Check if current route is Public Certificate Verification: /verify or /verify/:certId
  const verifyMatch = currentPath.match(/^\/verify(?:\/([^/]+))?$/);
  if (verifyMatch) {
    const certQuery = verifyMatch[1] ? decodeURIComponent(verifyMatch[1]) : '';
    return (
      <ErrorBoundary>
        <PublicCertificateVerifyPage initialQuery={certQuery} onNavigate={navigate} />
      </ErrorBoundary>
    );
  }

  // Admin Workspace Router
  let content = null;

  if (currentPath === '/' || currentPath === '') {
    content = <DashboardPage onNavigate={navigate} />;
  } else if (currentPath === '/surveys') {
    content = <SurveysListPage onNavigate={navigate} />;
  } else if (currentPath === '/surveys/new') {
    content = <SurveyBuilderPage surveyId="new" onNavigate={navigate} />;
  } else {
    // Parameterized routes
    const editMatch = currentPath.match(/^\/surveys\/([^/]+)\/edit$/);
    const analyticsMatch = currentPath.match(/^\/surveys\/([^/]+)\/analytics$/);
    const responsesMatch = currentPath.match(/^\/surveys\/([^/]+)\/responses$/);
    const responseDetailMatch = currentPath.match(/^\/surveys\/([^/]+)\/responses\/([^/]+)$/);
    const compareMatch = currentPath.match(/^\/surveys\/([^/]+)\/compare/);
    const exportMatch = currentPath.match(/^\/surveys\/([^/]+)\/export$/);
    const paperMatch = currentPath.match(/^\/surveys\/([^/]+)\/paper$/);
    const enumMatch = currentPath.match(/^\/surveys\/([^/]+)\/enumerators$/);

    if (editMatch) {
      content = <SurveyBuilderPage surveyId={editMatch[1]} onNavigate={navigate} />;
    } else if (paperMatch) {
      content = <PaperSurveyPage surveyId={paperMatch[1]} onNavigate={navigate} />;
    } else if (enumMatch) {
      content = <EnumeratorAnalyticsPage surveyId={enumMatch[1]} onNavigate={navigate} />;
    } else if (analyticsMatch) {
      content = <SurveyAnalyticsPage surveyId={analyticsMatch[1]} onNavigate={navigate} />;
    } else if (responsesMatch) {
      content = <ResponsesListPage surveyId={responsesMatch[1]} onNavigate={navigate} />;
    } else if (responseDetailMatch) {
      content = (
        <ResponseDetailPage
          surveyId={responseDetailMatch[1]}
          responseId={responseDetailMatch[2]}
          onNavigate={navigate}
        />
      );
    } else if (compareMatch) {
      const urlParams = new URLSearchParams(window.location.search);
      const resp1 = urlParams.get('resp1') || '';
      const resp2 = urlParams.get('resp2') || '';
      content = (
        <ResponseComparePage
          surveyId={compareMatch[1]}
          resp1Id={resp1}
          resp2Id={resp2}
          onNavigate={navigate}
        />
      );
    } else if (exportMatch) {
      content = <ExportImportPage surveyId={exportMatch[1]} onNavigate={navigate} />;
    } else {
      content = <DashboardPage onNavigate={navigate} />;
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/60 font-sans text-slate-900 antialiased selection:bg-indigo-500 selection:text-white">
      <Navbar currentPath={currentPath} onNavigate={navigate} />
      <main className="flex-1">
        <ErrorBoundary>{content}</ErrorBoundary>
      </main>
      <Footer />
    </div>
  );
}

export default App;
