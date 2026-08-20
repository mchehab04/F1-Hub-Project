'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSeasons, getSeasonRaces, RaceSummary, RaceStatus } from '@/lib/api';

export default function SeasonOverviewPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [races, setRaces] = useState<RaceSummary[]>([]);
  const [loadingSeasons, setLoadingSeasons] = useState<boolean>(true);
  const [loadingRaces, setLoadingRaces] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch seasons on load
  useEffect(() => {
    getSeasons()
      .then((data) => {
        if (data && data.seasons && data.seasons.length > 0) {
          const sortedSeasons = [...data.seasons].sort((a, b) => b - a);
          setSeasons(sortedSeasons);
          setSelectedSeason(sortedSeasons[0]);
        } else {
          setError('No seasons found.');
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to connect to backend server. Is the backend running?');
      })
      .finally(() => {
        setLoadingSeasons(false);
      });
  }, []);

  // Fetch races when selectedSeason changes
  useEffect(() => {
    if (selectedSeason === null) return;

    setLoadingRaces(true);
    setError(null);

    getSeasonRaces(selectedSeason)
      .then((data) => {
        setRaces(data.races || []);
      })
      .catch((err) => {
        setError(err.message || `Failed to fetch races for season ${selectedSeason}.`);
      })
      .finally(() => {
        setLoadingRaces(false);
      });
  }, [selectedSeason]);

  const getStatusBadgeClass = (status: RaceStatus) => {
    switch (status) {
      case 'completed':
        return 'badge badge-completed';
      case 'upcoming':
        return 'badge badge-upcoming';
      case 'postponed':
        return 'badge badge-postponed';
      case 'cancelled':
        return 'badge badge-cancelled';
      default:
        return 'badge';
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <h1 className="title">F1Hub Season Overview</h1>
          <p className="subtitle">Explore Formula 1 seasons, race calendars, and circuit details.</p>
        </div>
        {!loadingSeasons && seasons.length > 0 && (
          <div className="season-selector-wrapper">
            <label htmlFor="season-select" className="selector-label">Season:</label>
            <select
              id="season-select"
              className="season-selector"
              value={selectedSeason ?? ''}
              onChange={(e) => setSelectedSeason(Number(e.target.value))}
            >
              {seasons.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      {error && (
        <div className="error-banner">
          <strong>Backend Connection Error:</strong> {error}
          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
            Please ensure the FastAPI backend is running at <code>http://localhost:8000</code>.
          </div>
        </div>
      )}

      {loadingSeasons ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading seasons...</p>
        </div>
      ) : (
        <>
          {loadingRaces ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading races for {selectedSeason}...</p>
            </div>
          ) : races.length === 0 && !error ? (
            <div className="empty-state">
              <p>No races found for the {selectedSeason} season.</p>
            </div>
          ) : (
            <div className="race-grid">
              {races.map((race) => (
                <Link
                  key={race.race_id}
                  href={`/races/${race.race_id}`}
                  className="race-card-link"
                >
                  <div className="race-card">
                    <div className="race-card-header">
                      <span className="race-round">Round {race.round}</span>
                      <span className={getStatusBadgeClass(race.status)}>
                        {race.status}
                      </span>
                    </div>
                    <h2 className="race-name">{race.name}</h2>
                    <div className="race-circuit">
                      <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      </svg>
                      {race.circuit_name}
                    </div>
                    <div className="race-date">
                      <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                      </svg>
                      {new Date(race.date).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
