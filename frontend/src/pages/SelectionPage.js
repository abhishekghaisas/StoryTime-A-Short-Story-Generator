iimport React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const SelectionPage = ({ themes, genres, setStoryData }) => {
  const [selectedTheme, setSelectedTheme] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [maxLength, setMaxLength] = useState(500);
  const [temperature, setTemperature] = useState(0.7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedTheme || !selectedGenre) {
      setError('Please select both a theme and a genre');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme: selectedTheme,
          genre: selectedGenre,
          max_length: maxLength,
          temperature: temperature
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate story');
      }
      
      const data = await response.json();
      setStoryData(data);
      navigate('/story');
    } catch (error) {
      setError(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Capitalize first letter of string
  const capitalize = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  return (
    <div className="container">
      <Link to="/" className="btn btn-back">
        Back
      </Link>
      
      <div className="selection-container">
        <h1>Create Your Story</h1>
        <p>Choose a theme and genre for your personalized bedtime story</p>
        
        {error && (
          <div style={{ color: 'red', marginBottom: '1rem' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="card">
          <div className="form-group">
            <label htmlFor="theme">Theme</label>
            <select 
              id="theme" 
              className="form-control"
              value={selectedTheme}
              onChange={(e) => setSelectedTheme(e.target.value)}
            >
              <option value="">Select a theme</option>
              {themes.map((theme) => (
                <option key={theme} value={theme}>
                  {capitalize(theme)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="genre">Genre</label>
            <select 
              id="genre" 
              className="form-control"
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
            >
              <option value="">Select a genre</option>
              {genres.map((genre) => (
                <option key={genre} value={genre}>
                  {capitalize(genre)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="length">
              Story Length: {maxLength} words
            </label>
            <input 
              type="range" 
              id="length" 
              min="200" 
              max="1000" 
              step="50"
              value={maxLength}
              onChange={(e) => setMaxLength(Number(e.target.value))}
              className="form-control"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="creativity">
              Creativity Level: {Math.round(temperature * 100)}%
            </label>
            <input 
              type="range" 
              id="creativity" 
              min="0.1" 
              max="1.0" 
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="form-control"
            />
            <small>Higher creativity means more varied and unique stories, but they might be less coherent.</small>
          </div>
          
          <button 
            type="submit" 
            className="btn" 
            disabled={isLoading}
          >
            {isLoading ? 'Generating...' : 'Generate Story'}
          </button>
          
          {isLoading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Creating your magical story...</p>
              <p><small>This may take a moment as our AI crafts the perfect tale</small></p>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default SelectionPage;
