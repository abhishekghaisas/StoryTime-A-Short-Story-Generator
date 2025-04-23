import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const WelcomePage = () => {
  const [hasSavedStories, setHasSavedStories] = useState(false);
  
  // Check if there are any saved stories
  useEffect(() => {
    const savedStoriesJSON = localStorage.getItem('savedStories');
    const savedStories = savedStoriesJSON ? JSON.parse(savedStoriesJSON) : [];
    setHasSavedStories(savedStories.length > 0);
  }, []);

  return (
    <div className="container">
      <div className="welcome-container">
        <h1 className="welcome-title">✨ Nap! Nap! ✨</h1>
        <p className="welcome-subtitle">
          Create magical, personalized bedtime stories for your little ones
        </p>
        
        <div className="card">
          <h2>How it Works</h2>
          <p>
            Our AI story maker creates fun, one-of-a-kind bedtime stories based on the themes and genres you pick. 
            Every story is unique and perfect for making bedtime a little more magical. ✨
          </p>
          <p>
            Simply choose a theme like "space" or "animals," select a genre such as
            "adventure" or "fairy tale," and let our AI create a magical story
            for your child.
          </p>
          <div className="btn-container">
            <Link to="/select" className="btn">
              Create a Story
            </Link>
            {hasSavedStories && (
              <Link to="/saved-stories" className="btn btn-secondary">
                View Saved Stories
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;
