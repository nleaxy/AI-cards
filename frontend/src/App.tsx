import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';

// lazy loading — страницы загружаются только при переходе на них
// уменьшает начальный bundle и ускоряет первый экран
const Home = lazy(() => import('./pages/Home'));
const Decks = lazy(() => import('./pages/Decks'));
const Upload = lazy(() => import('./pages/Upload'));
const Learn = lazy(() => import('./pages/Learn'));
const Review = lazy(() => import('./pages/Review'));
const ManageCards = lazy(() => import('./pages/ManageCards'));
const Profile = lazy(() => import('./pages/Profile'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));

// Fallback показывается пока чанк страницы ещё загружается
const PageLoader: React.FC = () => (
  <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
    <div className="loading">Загрузка...</div>
  </div>
);

const App: React.FC = () => {
  return (
    <HelmetProvider>
      <AuthProvider>
        <Router>
          <div className="app">
            <Header />
            <main className="main-content">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/decks" element={<Decks />} />
                  <Route path="/upload" element={<Upload />} />
                  <Route path="/learn/:deckId" element={<Learn />} />
                  <Route path="/manage/:deckId" element={<ManageCards />} />
                  <Route path="/review" element={<Review />} />
                  <Route path="/profile" element={<Profile />} />

                  {/* Admin Routes */}
                  <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
                    <Route path="/admin" element={<AdminPanel />} />
                  </Route>
                </Routes>
              </Suspense>
            </main>
          </div>
        </Router>
      </AuthProvider>
    </HelmetProvider>
  );
}

export default App;