'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { getSeasons, getConstructorStandings, compareConstructors } from '@/lib/api';

type CompareResult = Awaited<ReturnType<typeof compareConstructors>>;

function rowWinner(a: number, b: number): 'a' | 'b' | null {
  if (a === b) return null;
  return a > b ? 'a' : 'b';
}

export default function ConstructorComparePage() {
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
      <ConstructorCompareContent />
    </Suspense>
  );
}

function ConstructorCompareContent() {
  const searchParams = useSearchParams();

  const [seasons, setSeasons] = useState<number[]>([]);
  const [rosterSeason, setRosterSeason] = useState<number | null>(null);
  const [scopeMode, setScopeMode] = useState<'season' | 'career'>('season');
  const [roster, setRoster] = useState<string[]>([]);
  const [constructorA, setConstructorA] = useState<string>(searchParams?.get('constructor_a') ?? '');
  const [constructorB, setConstructorB] = useState<string>('');

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
    getConstructorStandings(rosterSeason)
      .then((data) => {
        setRoster((data.standings || []).map((s) => s.constructor_id).sort());
      })
      .catch((err) => setError(err.message || `Failed to fetch constructors for season ${rosterSeason}.`))
      .finally(() => setLoadingRoster(false));
  }, [rosterSeason]);

  useEffect(() => {
    if (!constructorA || !constructorB) {
      setResult(null);
      return;
    }
    if (constructorA === constructorB) {
      setResult(null);
      setError('Choose two different constructors to compare.');
      return;
    }

    setLoadingCompare(true);
    setError(null);

    compareConstructors(
      constructorA,
      constructorB,
      scopeMode === 'season' ? rosterSeason ?? undefined : undefined
    )
      .then((data) => setResult(data))
      .catch((err) => {
        setResult(null);
        setError(err.message || 'Failed to compare constructors.');
      })
      .finally(() => setLoadingCompare(false));
  }, [constructorA, constructorB, scopeMode, rosterSeason]);

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href="/standings" className="back-link">
          &larr; Back to Standings
        </Link>
      </div>

      <header className="header">
        <div className="header-content">
          <h1 className="title">Compare Constructors</h1>
          <p className="subtitle">Head-to-head race wins, points, and podiums.</p>
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
            <label className="selector-label" htmlFor="constructor-a-select">
              Constructor A
            </label>
            <select
              id="constructor-a-select"
              className="season-selector"
              value={constructorA}
              onChange={(e) => setConstructorA(e.target.value)}
            >
              <option value="">Select a constructor</option>
              {roster.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>

          <div className="compare-field">
            <label className="selector-label" htmlFor="constructor-b-select">
              Constructor B
            </label>
            <select
              id="constructor-b-select"
              className="season-selector"
              value={constructorB}
              onChange={(e) => setConstructorB(e.target.value)}
            >
              <option value="">Select a constructor</option>
              {roster.map((id) => (
                <option key={id} value={id}>
                  {id}
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
          <p>Loading constructors for {rosterSeason}...</p>
        </div>
      )}

      {loadingCompare && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Comparing constructors...</p>
        </div>
      )}

      {result && !loadingCompare && (
        <section className="section">
          <h2 className="section-title">
            <Link href={`/constructors/${result.constructor_a}`}>{result.constructor_a}</Link>
            {' vs '}
            <Link href={`/constructors/${result.constructor_b}`}>{result.constructor_b}</Link>
            {result.season ? ` — ${result.season}` : ' — Career'}
          </h2>
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>{result.constructor_a}</th>
                  <th>{result.constructor_b}</th>
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ['Race Wins', result.head_to_head.race_wins],
                    ['Points', result.head_to_head.points],
                    ['Podiums', result.head_to_head.podiums],
                  ] as const
                ).map(([label, values]) => {
                  const winner = rowWinner(values[result.constructor_a], values[result.constructor_b]);
                  return (
                    <tr key={label}>
                      <td className="driver-cell">{label}</td>
                      <td className={winner === 'a' ? 'font-bold' : ''}>{values[result.constructor_a]}</td>
                      <td className={winner === 'b' ? 'font-bold' : ''}>{values[result.constructor_b]}</td>
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
