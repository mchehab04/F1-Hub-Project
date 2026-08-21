'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getDriver, getSeasons, getDriverStandings, Driver, DriverStanding } from '@/lib/api';
import { TeamChip } from '@/components/TeamChip';
import { getTeamColor } from '@/lib/teamColors';

function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
}

export default function DriverProfilePage() {
  const params = useParams();
  const driverId = params?.driverId as string;

  const [driver, setDriver] = useState<Driver | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [statsMode, setStatsMode] = useState<'career' | 'season'>('career');
  const [seasons, setSeasons] = useState<number[]>([]);
  const [statsSeason, setStatsSeason] = useState<number | null>(null);
  const [seasonStanding, setSeasonStanding] = useState<DriverStanding | null>(null);
  const [loadingSeasonStats, setLoadingSeasonStats] = useState<boolean>(false);
  const [seasonStatsError, setSeasonStatsError] = useState<string | null>(null);

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

  useEffect(() => {
    getSeasons()
      .then((data) => {
        if (data && data.seasons && data.seasons.length > 0) {
          const sorted = [...data.seasons].sort((a, b) => b - a);
          setSeasons(sorted);
          setStatsSeason(sorted[0]);
        }
      })
      .catch(() => {
        // Season toggle stays unavailable if this fails; career stats still work.
      });
  }, []);

  useEffect(() => {
    if (statsMode !== 'season' || statsSeason === null || !driverId) return;

    setLoadingSeasonStats(true);
    setSeasonStatsError(null);

    getDriverStandings(statsSeason)
      .then((data) => {
        const match = (data.standings || []).find((s) => s.driver_id === driverId) ?? null;
        setSeasonStanding(match);
      })
      .catch((err) => {
        setSeasonStanding(null);
        setSeasonStatsError(err.message || `Failed to fetch ${statsSeason} standings.`);
      })
      .finally(() => setLoadingSeasonStats(false));
  }, [statsMode, statsSeason, driverId]);

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

      <header
        className="race-header-card"
        style={{ borderLeftColor: getTeamColor(driver.current_constructor_id) }}
      >
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
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
              <strong>Current Team:</strong>
              <TeamChip
                constructorId={driver.current_constructor_id}
                label={driver.current_constructor_id}
              />
            </span>
          )}
        </div>
      </header>

      <section className="section">
        <div className="stats-toggle-row">
          <h2 className="section-title" style={{ marginBottom: 0 }}>
            {statsMode === 'career' ? 'Career Statistics' : 'Season Statistics'}
          </h2>
          <div className="stats-toggle">
            <button
              type="button"
              className={statsMode === 'career' ? 'stats-toggle-btn active' : 'stats-toggle-btn'}
              onClick={() => setStatsMode('career')}
            >
              Career
            </button>
            <button
              type="button"
              className={statsMode === 'season' ? 'stats-toggle-btn active' : 'stats-toggle-btn'}
              onClick={() => setStatsMode('season')}
              disabled={seasons.length === 0}
            >
              Season
            </button>
          </div>
          {statsMode === 'season' && seasons.length > 0 && (
            <select
              className="season-selector stats-season-select"
              value={statsSeason ?? ''}
              onChange={(e) => setStatsSeason(Number(e.target.value))}
              aria-label="Season"
            >
              {seasons.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
        </div>

        {statsMode === 'career' ? (
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
        ) : loadingSeasonStats ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading {statsSeason} statistics...</p>
          </div>
        ) : seasonStatsError ? (
          <div className="error-banner">
            <strong>Error:</strong> {seasonStatsError}
          </div>
        ) : !seasonStanding ? (
          <div className="empty-state">
            <p>
              {driver.name} did not race in the {statsSeason} season.
            </p>
          </div>
        ) : (
          <div className="circuit-stats-grid">
            <div className="stat-item">
              <span className="stat-label">Position</span>
              <span className="stat-value">{ordinal(seasonStanding.position)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Points</span>
              <span className="stat-value">{seasonStanding.points}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Wins</span>
              <span className="stat-value">{seasonStanding.wins}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Podiums</span>
              <span className="stat-value">{seasonStanding.podiums}</span>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
