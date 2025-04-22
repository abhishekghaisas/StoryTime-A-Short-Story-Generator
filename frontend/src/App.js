// App.js - Main Component with Story Quality Features
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import WelcomePage from './pages/WelcomePage';
import SelectionPage from './pages/SelectionPage';
import StoryPage from './pages/StoryPage';
import './App.css';

function App() {
  const [storyData, setStoryData] = useState(null);
  const [themes, setThemes] = useState([]);
  const [genres, setGenres] = useState([]);
  
  // Fetch available themes and genres when the app loads
  useEffect(() => {
    fetchThemesAndGenres();
  }, []);

  const fetchThemesAndGenres = async () => {
    try {
      const response = await fetch('http://localhost:8000/themes-genres');
      if (response.ok) {
        const data = await response.json();
        setThemes(data.themes);
        setGenres(data.genres);
      } else {
        console.error('Failed to fetch themes and genres');
      }
    } catch (error) {
      console.error('Error fetching themes and genres:', error);
    }
  };

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route 
            path="/select" 
            element={<SelectionPage 
              themes={themes} 
              genres={genres} 
              setStoryData={setStoryData} 
            />} 
          />
          <Route 
            path="/story" 
            element={
              storyData ? 
                <StoryPage storyData={storyData} /> : 
                <Navigate to="/select" replace />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;