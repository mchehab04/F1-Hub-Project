'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getReplay, ReplayResponse } from '@/lib/api';

function podiumClass(position: number) {
  if (position === 1) return 'podium-1';
  if (position === 2) return 'podium-2';
  if (position === 3) return 'podium-3';
  return '';
}

export default function RaceReplayPage() {
  const params = useParams();
  const raceId = params?.raceId as string;

  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [currentLap, setCurrentLap] = useState<number>(1);
  const [playing, setPlaying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!raceId) return;

    setLoading(true);
    setError(null);

    getReplay(raceId)
      .then((data) => {
        setReplay(data);
        setCurrentLap(1);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch replay data.');
      })
      .finally(() => setLoading(false));
  }, [raceId]);

  useEffect(() => {
    if (!playing || !replay) return;

    intervalRef.current = setInterval(() => {
      setCurrentLap((lap) => {
        if (lap >= replay.total_laps) {
          setPlaying(false);
          return lap;
        }
        return lap + 1;
      });
    }, 500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, replay]);

  const { leaderboard, retired } = useMemo(() => {
    if (!replay) return { leaderboard: [], retired: [] as string[] };

    const board = replay.drivers
      .map((driver) => ({
        driver_id: driver.driver_id,
        entry: driver.laps.find((l) => l.lap === currentLap),
        maxLap: driver.laps.length > 0 ? driver.laps[driver.laps.length - 1].lap : 0,
      }))
      .filter((d) => d.entry);

    board.sort((a, b) => a.entry!.position - b.entry!.position);

    const retiredIds = replay.drivers
      .filter((driver) => {
        const maxLap = driver.laps.length > 0 ? driver.laps[driver.laps.length - 1].lap : 0;
        return maxLap < currentLap;
      })
      .map((d) => d.driver_id);

    return { leaderboard: board, retired: retiredIds };
  }, [replay, currentLap]);

  if (loading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading replay...</p>
        </div>
      </div>
    );
  }

  if (error || !replay) {
    return (
      <div className="container">
        <div className="error-banner">
          <strong>Error:</strong> {error || 'Replay not found.'}
        </div>
        <div style={{ marginTop: '1.5rem' }}>
          <Link href={`/races/${raceId}`} className="back-link">
            &larr; Back to Race
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href={`/races/${raceId}`} className="back-link">
          &larr; Back to Race
        </Link>
      </div>

      <header className="header">
        <div className="header-content">
          <h1 className="title">Race Replay</h1>
          <p className="subtitle">
            {replay.race_id} &bull; {replay.total_laps} laps
          </p>
        </div>
      </header>

      <div className="replay-controls">
        <button
          type="button"
          className="nav-link"
          onClick={() => setPlaying((p) => !p)}
          disabled={currentLap >= replay.total_laps && !playing}
        >
          {playing ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          className="nav-link"
          onClick={() => {
            setPlaying(false);
            setCurrentLap((lap) => Math.max(1, lap - 1));
          }}
          disabled={currentLap <= 1}
        >
          &larr; Prev Lap
        </button>
        <input
          type="range"
          className="replay-slider"
          min={1}
          max={replay.total_laps}
          value={currentLap}
          onChange={(e) => {
            setPlaying(false);
            setCurrentLap(Number(e.target.value));
          }}
        />
        <button
          type="button"
          className="nav-link"
          onClick={() => {
            setPlaying(false);
            setCurrentLap((lap) => Math.min(replay.total_laps, lap + 1));
          }}
          disabled={currentLap >= replay.total_laps}
        >
          Next Lap &rarr;
        </button>
        <span className="replay-lap-label">
          Lap {currentLap} / {replay.total_laps}
        </span>
      </div>

      <section className="section">
        <div className="table-responsive">
          <table className="results-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Driver</th>
                <th>Gap to Leader</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map(({ driver_id, entry }) => (
                <tr key={driver_id} className={podiumClass(entry!.position)}>
                  <td className="font-bold">{entry!.position}</td>
                  <td className="driver-cell">
                    <Link href={`/drivers/${driver_id}`}>{driver_id}</Link>
                  </td>
                  <td>{entry!.position === 1 ? 'Leader' : `+${entry!.gap_to_leader_s.toFixed(3)}s`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {retired.length > 0 && (
          <div className="empty-state" style={{ marginTop: '1rem', textAlign: 'left' }}>
            <p>
              <strong>Already retired by lap {currentLap}:</strong>{' '}
              {retired.map((driverId, i) => (
                <React.Fragment key={driverId}>
                  {i > 0 && ', '}
                  <Link href={`/drivers/${driverId}`}>{driverId}</Link>
                </React.Fragment>
              ))}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
