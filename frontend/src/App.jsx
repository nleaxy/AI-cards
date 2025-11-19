import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import Decks from './pages/Decks';
import Upload from './pages/Upload';
import Learn from './pages/Learn';
import Review from './pages/Review';
import ManageCards from './pages/ManageCards';

function App() {
  return (
    <Router>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/decks" element={<Decks />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/learn/:deckId" element={<Learn />} />
            <Route path="/manage/:deckId" element={<ManageCards />} />
            <Route path="/review" element={<Review />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;