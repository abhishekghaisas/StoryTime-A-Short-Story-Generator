import React from 'react';
import { Link, Navigate } from 'react-router-dom';

const SavedStoryViewPage = ({ selectedSavedStory }) => {
  // If no story is selected, redirect to saved stories page
  if (!selectedSavedStory) {
    return <Navigate to="/saved-stories" replace />;
  }

  // Generate a title based on theme and genre if not provided in the API response
  const storyTitle = selectedSavedStory.title || 
    `The ${selectedSavedStory.theme.charAt(0).toUpperCase() + selectedSavedStory.theme.slice(1)} ${selectedSavedStory.genre.charAt(0).toUpperCase() + selectedSavedStory.genre.slice(1)}`;
  
  // Function to handle downloading the story
  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob(
      [
        `${storyTitle}\n\n` +
        `Theme: ${selectedSavedStory.theme.charAt(0).toUpperCase() + selectedSavedStory.theme.slice(1)}\n` +
        `Genre: ${selectedSavedStory.genre.charAt(0).toUpperCase() + selectedSavedStory.genre.slice(1)}\n\n` +
        selectedSavedStory.content
      ], 
      { type: 'text/plain' }
    );
    
    element.href = URL.createObjectURL(file);
    element.download = `${storyTitle.replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="container">
      <Link to="/saved-stories" className="btn btn-back">
        Back to Saved Stories
      </Link>
      
      <div className="story-container">
        <h1>Your Saved Story</h1>
        
        <div className="story-meta">
          <span>Theme: {selectedSavedStory.theme.charAt(0).toUpperCase() + selectedSavedStory.theme.slice(1)}</span>
          •
          <span>Genre: {selectedSavedStory.genre.charAt(0).toUpperCase() + selectedSavedStory.genre.slice(1)}</span>
        </div>
        
        <div className="story-card">
          <h2 className="story-title">{storyTitle}</h2>
          <div className="story-content">
            {selectedSavedStory.content}
          </div>
        </div>
        
        <div className="btn-container">
          <Link to="/saved-stories" className="btn btn-secondary">
            Back to Saved Stories
          </Link>
          <button onClick={handleDownload} className="btn">
            Download Story
          </button>
        </div>
      </div>
    </div>
  );
};

export default SavedStoryViewPage;