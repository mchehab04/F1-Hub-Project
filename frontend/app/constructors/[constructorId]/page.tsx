'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getConstructor, Constructor } from '@/lib/api';

export default function ConstructorProfilePage() {
  const params = useParams();
  const constructorId = params?.constructorId as string;

  const [constructor, setConstructor] = useState<Constructor | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!constructorId) return;

    setLoading(true);
    setError(null);

    getConstructor(constructorId)
      .then((data) => setConstructor(data))
      .catch((err) => {
        setError(err.message || 'Failed to fetch constructor profile.');
      })
      .finally(() => setLoading(false));
  }, [constructorId]);

  if (loading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading constructor profile...</p>
        </div>
      </div>
    );
  }

  if (error || !constructor) {
    return (
      <div className="container">
        <div className="error-banner">
          <strong>Error:</strong> {error || 'Constructor not found.'}
        </div>
        <div style={{ marginTop: '1.5rem' }}>
          <Link href="/standings" className="back-link">
            &larr; Back to Standings
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href="/standings" className="back-link">
          &larr; Back to Standings
        </Link>
      </div>

      <header className="race-header-card">
        <div className="race-header-top">
          <h1 className="title" style={{ marginBottom: 0 }}>{constructor.name}</h1>
          <Link
            href={`/constructors/compare?constructor_a=${constructor.constructor_id}`}
            className="nav-link"
          >
            Compare Constructors
          </Link>
        </div>
        <div className="race-header-meta">
          <span>
            <strong>Nationality:</strong> {constructor.nationality}
          </span>
          <span>
            <strong>Current Drivers:</strong>{' '}
            {constructor.current_drivers.length > 0
              ? constructor.current_drivers.map((driverId, i) => (
                  <React.Fragment key={driverId}>
                    {i > 0 && ', '}
                    <Link href={`/drivers/${driverId}`}>{driverId}</Link>
                  </React.Fragment>
                ))
              : 'N/A'}
          </span>
        </div>
      </header>

      <section className="section">
        <h2 className="section-title">Career Statistics</h2>
        <div className="circuit-stats-grid">
          <div className="stat-item">
            <span className="stat-label">Wins</span>
            <span className="stat-value">{constructor.career.wins}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Podiums</span>
            <span className="stat-value">{constructor.career.podiums}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Poles</span>
            <span className="stat-value">{constructor.career.poles}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Championships</span>
            <span className="stat-value">{constructor.career.championships}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
