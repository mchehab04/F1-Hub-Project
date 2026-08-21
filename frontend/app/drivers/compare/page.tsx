'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { getSeasons, getDriverStandings, compareDrivers, DriverStanding } from '@/lib/api';
import { getTeamColor } from '@/lib/teamColors';

type CompareResult = Awaited<ReturnType<typeof compareDrivers>>;

function rowWinner(a: number, b: number): 'a' | 'b' | null {
  if (a === b) return null;
  return a > b ? 'a' : 'b';
}

export default function DriverComparePage() {
  return (
    <Suspense
      fallback={
        <div className="container">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        </div>
      }
    >
      <DriverCompareContent />
    </Suspense>
  );
}

function DriverCompareContent() {
  const searchParams = useSearchParams();

  const [seasons, setSeasons] = useState<number[]>([]);
  const [rosterSeason, setRosterSeason] = useState<number | null>(null);
  const [scopeMode, setScopeMode] = useState<'season' | 'career'>('season');
  const [roster, setRoster] = useState<DriverStanding[]>([]);
  const [driverA, setDriverA] = useState<string>(searchParams?.get('driver_a') ?? '');
  const [driverB, setDriverB] = useState<string>('');

  const [result, setResult] = useState<CompareResult | null>(null);
  const [loadingSeasons, setLoadingSeasons] = useState<boolean>(true);
  const [loadingRoster, setLoadingRoster] = useState<boolean>(false);
  const [loadingCompare, setLoadingCompare] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSeasons()
      .then((data) => {
        if (data && data.seasons && data.seasons.length > 0) {
          const sorted = [...data.seasons].sort((a, b) => b - a);
          setSeasons(sorted);
          setRosterSeason(sorted[0]);
        } else {
          setError('No seasons found.');
        }
      })
      .catch((err) => setError(err.message || 'Failed to connect to backend server.'))
      .finally(() => setLoadingSeasons(false));
  }, []);

  useEffect(() => {
    if (rosterSeason === null) return;
    setLoadingRoster(true);
    getDriverStandings(rosterSeason)
      .then((data) => {
        setRoster(
          [...(data.standings || [])].sort((a, b) => a.driver_id.localeCompare(b.driver_id))
        );
      })
      .catch((err) => setError(err.message || `Failed to fetch drivers for season ${rosterSeason}.`))
      .finally(() => setLoadingRoster(false));
  }, [rosterSeason]);

  useEffect(() => {
    if (!driverA || !driverB) {
      setResult(null);
      return;
    }
    if (driverA === driverB) {
      setResult(null);
      setError('Choose two different drivers to compare.');
      return;
    }

    setLoadingCompare(true);
    setError(null);

    compareDrivers(driverA, driverB, scopeMode === 'season' ? rosterSeason ?? undefined : undefined)
      .then((data) => setResult(data))
      .catch((err) => {
        setResult(null);
        setError(err.message || 'Failed to compare drivers.');
      })
      .finally(() => setLoadingCompare(false));
  }, [driverA, driverB, scopeMode, rosterSeason]);

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href="/standings" className="back-link">
          &larr; Back to Standings
        </Link>
      </div>

      <header className="header">
        <div className="header-content">
          <h1 className="title">Compare Drivers</h1>
          <p className="subtitle">Head-to-head qualifying, race finishes, and points.</p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loadingSeasons ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading seasons...</p>
        </div>
      ) : (
        <div className="compare-form">
          <div className="compare-field">
            <label className="selector-label" htmlFor="driver-a-select">
              Driver A
            </label>
            <select
              id="driver-a-select"
              className="season-selector"
              value={driverA}
              onChange={(e) => setDriverA(e.target.value)}
            >
              <option value="">Select a driver</option>
              {roster.map((d) => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.driver_id}
                </option>
              ))}
            </select>
          </div>

          <div className="compare-field">
            <label className="selector-label" htmlFor="driver-b-select">
              Driver B
            </label>
            <select
              id="driver-b-select"
              className="season-selector"
              value={driverB}
              onChange={(e) => setDriverB(e.target.value)}
            >
              <option value="">Select a driver</option>
              {roster.map((d) => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.driver_id}
                </option>
              ))}
            </select>
          </div>

          <div className="compare-field">
            <label className="selector-label" htmlFor="scope-select">
              Scope
            </label>
            <select
              id="scope-select"
              className="season-selector"
              value={scopeMode}
              onChange={(e) => setScopeMode(e.target.value as 'season' | 'career')}
            >
              <option value="season">Season</option>
              <option value="career">Career</option>
            </select>
          </div>

          {scopeMode === 'season' && (
            <div className="compare-field">
              <label className="selector-label" htmlFor="roster-season-select">
                Season
              </label>
              <select
                id="roster-season-select"
                className="season-selector"
                value={rosterSeason ?? ''}
                onChange={(e) => setRosterSeason(Number(e.target.value))}
              >
                {seasons.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {loadingRoster && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading drivers for {rosterSeason}...</p>
        </div>
      )}

      {loadingCompare && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Comparing drivers...</p>
        </div>
      )}

      {result && !loadingCompare && (
        <section className="section">
          <h2 className="section-title">
            <Link href={`/drivers/${result.driver_a}`}>{result.driver_a}</Link>
            {' vs '}
            <Link href={`/drivers/${result.driver_b}`}>{result.driver_b}</Link>
            {result.season ? ` — ${result.season}` : ' — Career'}
          </h2>
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th
                    className="compare-th-team"
                    style={
                      {
                        '--team-color': getTeamColor(
                          roster.find((d) => d.driver_id === result.driver_a)?.constructor_id
                        ),
                      } as React.CSSProperties
                    }
                  >
                    {result.driver_a}
                  </th>
                  <th
                    className="compare-th-team"
                    style={
                      {
                        '--team-color': getTeamColor(
                          roster.find((d) => d.driver_id === result.driver_b)?.constructor_id
                        ),
                      } as React.CSSProperties
                    }
                  >
                    {result.driver_b}
                  </th>
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ['Qualifying Wins', result.head_to_head.qualifying_wins],
                    ['Race Finish Wins', result.head_to_head.race_finish_wins],
                    ['Points', result.head_to_head.points],
                  ] as const
                ).map(([label, values]) => {
                  const winner = rowWinner(values[result.driver_a], values[result.driver_b]);
                  return (
                    <tr key={label}>
                      <td className="driver-cell">{label}</td>
                      <td className={winner === 'a' ? 'font-bold' : ''}>{values[result.driver_a]}</td>
                      <td className={winner === 'b' ? 'font-bold' : ''}>{values[result.driver_b]}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
