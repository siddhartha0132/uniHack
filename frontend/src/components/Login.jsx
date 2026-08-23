import React, { useState } from 'react';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('demo123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const API_BASE = (import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Login failed (${res.status}): ${text || "Invalid credentials"}`);
      }
      
      const data = await res.json();
      localStorage.setItem('veritas_token', data.access_token);
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" style={{ background: 'var(--bg)' }}>
      <div className="modal-box" style={{ maxWidth: '400px', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '24px' }}>Log in to Veritas</h2>
        {error && <div style={{ color: 'var(--red)', marginBottom: '16px' }}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <input 
            className="input" 
            type="text" 
            placeholder="Username" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
          />
          <input 
            className="input" 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
          />
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '8px' }}>
            {loading ? 'Logging in...' : 'Log in'}
          </button>
        </form>
        <p className="text-secondary" style={{ marginTop: '24px', fontSize: '12px' }}>
          Hint: use demo / demo123
        </p>
      </div>
    </div>
  );
}
