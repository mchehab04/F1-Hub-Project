'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  getSeasons,
  getDriverStandings,
  getConstructorStandings,
  DriverStanding,
  ConstructorStanding,
} from '@/lib/api';
import { TeamChip } from '@/components/TeamChip';
import { getTeamColor } from '@/lib/teamColors';

function Sparkline({ trend, color }: { trend: number[]; color?: string }) {
  const max = Math.max(1, ...trend);
  return (
    <div className="sparkline" title={`Points per race: ${trend.join(', ')}`}>
      {trend.map((value, i) => (
        <span
          key={i}
          className="sparkline-bar"
          style={{
            height: `${Math.max(6, (value / max) * 100)}%`,
            backgroundColor: color,
          }}
        />
      ))}
    </div>
  );
}

function podiumClass(position: number) {
  if (position === 1) return 'podium-1';
  if (position === 2) return 'podium-2';
  if (position === 3) return 'podium-3';
  return '';
}

export default function StandingsPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [driverStandings, setDriverStandings] = useState<DriverStanding[]>([]);
  const [constructorStandings, setConstructorStandings] = useState<ConstructorStanding[]>([]);
  const [loadingSeasons, setLoadingSeasons] = useState<boolean>(true);
  const [loadingStandings, setLoadingStandings] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    if (selectedSeason === null) return;

    setLoadingStandings(true);
    setError(null);

    Promise.all([getDriverStandings(selectedSeason), getConstructorStandings(selectedSeason)])
      .then(([driversData, constructorsData]) => {
        setDriverStandings(driversData.standings || []);
        setConstructorStandings(constructorsData.standings || []);
      })
      .catch((err) => {
        setError(err.message || `Failed to fetch standings for season ${selectedSeason}.`);
      })
      .finally(() => {
        setLoadingStandings(false);
      });
  }, [selectedSeason]);

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <Link href="/" className="back-link">
            &larr; Back to Season Overview
          </Link>
          <h1 className="title" style={{ marginTop: '0.5rem' }}>
            Championship Standings
          </h1>
          <p className="subtitle">Driver and constructor points, wins, and podiums.</p>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
            <Link href="/drivers/compare" className="nav-link">
              Compare Drivers
            </Link>
            <Link href="/constructors/compare" className="nav-link">
              Compare Constructors
            </Link>
          </div>
        </div>
        {!loadingSeasons && seasons.length > 0 && (
          <div className="season-selector-wrapper">
            <label htmlFor="season-select" className="selector-label">
              Season:
            </label>
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

      {loadingSeasons || loadingStandings ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading standings...</p>
        </div>
      ) : (
        <>
          <section className="section">
            <h2 className="section-title">Driver Standings</h2>
            {driverStandings.length === 0 && !error ? (
              <div className="empty-state">
                <p>No driver standings available for {selectedSeason}.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Pos</th>
                      <th>Driver</th>
                      <th>Constructor</th>
                      <th>Points</th>
                      <th>Wins</th>
                      <th>Podiums</th>
                      <th>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {driverStandings.map((standing) => (
                      <tr key={standing.driver_id} className={podiumClass(standing.position)}>
                        <td className="font-bold">{standing.position}</td>
                        <td className="driver-cell">
                          <Link href={`/drivers/${standing.driver_id}`}>{standing.driver_id}</Link>
                        </td>
                        <td>
                          <TeamChip
                            constructorId={standing.constructor_id}
                            label={standing.constructor_name}
                          />
                        </td>
                        <td className="font-bold">{standing.points}</td>
                        <td>{standing.wins}</td>
                        <td>{standing.podiums}</td>
                        <td>
                          <Sparkline
                            trend={standing.trend}
                            color={getTeamColor(standing.constructor_id)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="section">
            <h2 className="section-title">Constructor Standings</h2>
            {constructorStandings.length === 0 && !error ? (
              <div className="empty-state">
                <p>No constructor standings available for {selectedSeason}.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Pos</th>
                      <th>Constructor</th>
                      <th>Points</th>
                      <th>Wins</th>
                      <th>Podiums</th>
                      <th>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {constructorStandings.map((standing) => (
                      <tr key={standing.constructor_id} className={podiumClass(standing.position)}>
                        <td className="font-bold">{standing.position}</td>
                        <td>
                          <TeamChip
                            constructorId={standing.constructor_id}
                            label={standing.constructor_id}
                          />
                        </td>
                        <td className="font-bold">{standing.points}</td>
                        <td>{standing.wins}</td>
                        <td>{standing.podiums}</td>
                        <td>
                          <Sparkline
                            trend={standing.trend}
                            color={getTeamColor(standing.constructor_id)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
