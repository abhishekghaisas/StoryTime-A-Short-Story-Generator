import React from 'react';
import { Link } from 'react-router-dom';

const StoryPage = ({ storyData }) => {
  // Generate a title based on theme and genre if not provided in the API response
  const storyTitle = storyData.title || 
    `The ${storyData.theme.charAt(0).toUpperCase() + storyData.theme.slice(1)} ${storyData.genre.charAt(0).toUpperCase() + storyData.genre.slice(1)}`;
  
  // Function to handle downloading the story
  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob(
      [
        `${storyTitle}\n\n` +
        `Theme: ${storyData.theme.charAt(0).toUpperCase() + storyData.theme.slice(1)}\n` +
        `Genre: ${storyData.genre.charAt(0).toUpperCase() + storyData.genre.slice(1)}\n\n` +
        storyData.content
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
      <Link to="/select" className="btn btn-back">
        Back
      </Link>
      
      <div className="story-container">
        <h1>Your Story is Ready!</h1>
        
        <div className="story-meta">
          <span>Theme: {storyData.theme.charAt(0).toUpperCase() + storyData.theme.slice(1)}</span>
          •
          <span>Genre: {storyData.genre.charAt(0).toUpperCase() + storyData.genre.slice(1)}</span>
        </div>
        
        <div className="story-card">
          <h2 className="story-title">{storyTitle}</h2>
          <div className="story-content">
            {storyData.content}
          </div>
        </div>
        
        <div className="btn-container">
          <Link to="/select" className="btn btn-secondary">
            Create Another Story
          </Link>
          <button onClick={handleDownload} className="btn">
            Download Story
          </button>
        </div>
      </div>
    </div>
  );
};

export default StoryPage;