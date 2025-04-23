import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const SavedStoriesPage = ({ setSelectedSavedStory }) => {
  const [savedStories, setSavedStories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load saved stories from localStorage
    const loadSavedStories = () => {
      setIsLoading(true);
      try {
        const storiesJSON = localStorage.getItem('savedStories');
        const stories = storiesJSON ? JSON.parse(storiesJSON) : [];
        setSavedStories(stories);
        setError(null);
      } catch (err) {
        setError('Failed to load saved stories');
        console.error('Error loading saved stories:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadSavedStories();
  }, []);

  const handleViewStory = (story) => {
    setSelectedSavedStory(story);
  };

  const handleDeleteStory = (index) => {
    const updatedStories = [...savedStories];
    updatedStories.splice(index, 1);
    setSavedStories(updatedStories);
    localStorage.setItem('savedStories', JSON.stringify(updatedStories));
  };

  // Generate a title based on theme and genre if not provided
  const getStoryTitle = (story) => {
    return story.title || 
      `The ${story.theme.charAt(0).toUpperCase() + story.theme.slice(1)} ${story.genre.charAt(0).toUpperCase() + story.genre.slice(1)}`;
  };

  // Format the saved date
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown date';
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
  };

  return (
    <div className="container">
      <Link to="/" className="btn btn-back">
        Back
      </Link>
      
      <div className="saved-stories-container">
        <h1>Your Saved Stories</h1>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading your stories...</p>
          </div>
        ) : savedStories.length === 0 ? (
          <div className="card">
            <p>You don't have any saved stories yet.</p>
            <Link to="/select" className="btn">
              Create Your First Story
            </Link>
          </div>
        ) : (
          <div className="stories-list">
            {savedStories.map((story, index) => (
              <div key={index} className="story-list-item card">
                <h2>{getStoryTitle(story)}</h2>
                <div className="story-meta">
                  <span>Theme: {story.theme.charAt(0).toUpperCase() + story.theme.slice(1)}</span>
                  •
                  <span>Genre: {story.genre.charAt(0).toUpperCase() + story.genre.slice(1)}</span>
                  •
                  <span>Saved: {formatDate(story.savedAt)}</span>
                </div>
                <div className="story-preview">
                  {story.content.substring(0, 150)}...
                </div>
                <div className="btn-container">
                  <Link 
                    to="/view-story" 
                    className="btn"
                    onClick={() => handleViewStory(story)}
                  >
                    View Story
                  </Link>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => handleDeleteStory(index)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SavedStoriesPage;