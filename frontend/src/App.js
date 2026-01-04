import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoginPage from './components/LoginPage';
import DashboardPage from './components/DashboardPage';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if session exists in localStorage
    const savedSessionId = localStorage.getItem('sessionId');
    const savedUser = localStorage.getItem('user');
    
    if (savedSessionId && savedUser) {
      setSessionId(savedSessionId);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (sessionId, user) => {
    setSessionId(sessionId);
    setUser(user);
    localStorage.setItem('sessionId', sessionId);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = async () => {
    const currentSessionId = sessionId;
    // Clear local state first
    setSessionId(null);
    setUser(null);
    localStorage.removeItem('sessionId');
    localStorage.removeItem('user');
    
    // Call backend logout (fire and forget)
    if (currentSessionId) {
      try {
        await axios.post('http://localhost:8000/logout', {
          sessionId: currentSessionId
        });
      } catch (err) {
        // Ignore errors on logout
      }
    }
  };

  return (
    <div className="App">
      {!sessionId ? (
        <LoginPage onLogin={handleLogin} />
      ) : (
        <DashboardPage sessionId={sessionId} user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;

