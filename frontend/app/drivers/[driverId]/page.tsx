'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getDriver, Driver } from '@/lib/api';

export default function DriverProfilePage() {
  const params = useParams();
  const driverId = params?.driverId as string;

  const [driver, setDriver] = useState<Driver | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!driverId) return;

    setLoading(true);
    setError(null);

    getDriver(driverId)
      .then((data) => setDriver(data))
      .catch((err) => {
        setError(err.message || 'Failed to fetch driver profile.');
      })
      .finally(() => setLoading(false));
  }, [driverId]);

  if (loading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading driver profile...</p>
        </div>
      </div>
    );
  }

  if (error || !driver) {
    return (
      <div className="container">
        <div className="error-banner">
          <strong>Error:</strong> {error || 'Driver not found.'}
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
          <h1 className="title" style={{ marginBottom: 0 }}>{driver.name}</h1>
          <Link href={`/drivers/compare?driver_a=${driver.driver_id}`} className="nav-link">
            Compare Drivers
          </Link>
        </div>
        <div className="race-header-meta">
          <span>
            <strong>Nationality:</strong> {driver.nationality}
          </span>
          <span>
            <strong>Date of Birth:</strong>{' '}
            {new Date(driver.date_of_birth).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
          {driver.current_constructor_id && (
            <span>
              <strong>Current Team:</strong>{' '}
              <Link href={`/constructors/${driver.current_constructor_id}`}>
                {driver.current_constructor_id}
              </Link>
            </span>
          )}
        </div>
      </header>

      <section className="section">
        <h2 className="section-title">Career Statistics</h2>
        <div className="circuit-stats-grid">
          <div className="stat-item">
            <span className="stat-label">Wins</span>
            <span className="stat-value">{driver.career.wins}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Podiums</span>
            <span className="stat-value">{driver.career.podiums}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Poles</span>
            <span className="stat-value">{driver.career.poles}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Championships</span>
            <span className="stat-value">{driver.career.championships}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
