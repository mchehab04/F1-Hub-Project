'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getRace, getCircuit, RaceDetail, Circuit, RaceStatus, DriverResultStatus } from '@/lib/api';

export default function RaceDetailPage() {
  const params = useParams();
  const raceId = params?.raceId as string;

  const [race, setRace] = useState<RaceDetail | null>(null);
  const [circuit, setCircuit] = useState<Circuit | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!raceId) return;

    setLoading(true);
    setError(null);

    getRace(raceId)
      .then((raceData) => {
        setRace(raceData);
        // Fetch circuit details using circuit_id from race details
        if (raceData && raceData.circuit_id) {
          return getCircuit(raceData.circuit_id);
        }
        return null;
      })
      .then((circuitData) => {
        if (circuitData) {
          setCircuit(circuitData);
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch race details.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [raceId]);

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

  const getStatusBadgeText = (status: DriverResultStatus) => {
    switch (status) {
      case 'finished':
        return 'Finished';
      case 'dnf':
        return 'DNF';
      case 'dsq':
        return 'DSQ';
      case 'dns':
        return 'DNS';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading race details...</p>
        </div>
      </div>
    );
  }

  if (error || !race) {
    return (
      <div className="container">
        <div className="error-banner">
          <strong>Error:</strong> {error || 'Race not found.'}
        </div>
        <div style={{ marginTop: '1.5rem' }}>
          <Link href="/" className="back-link">
            &larr; Back to Season Overview
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href="/" className="back-link">
          &larr; Back to Season Overview
        </Link>
      </div>

      <header className="race-header-card">
        <div className="race-header-top">
          <span className="race-round">Season {race.season} &bull; Round {race.round}</span>
          <span className={getStatusBadgeClass(race.status)}>{race.status}</span>
        </div>
        <h1 className="title" style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>{race.name}</h1>
        {race.status === 'completed' && race.season >= 2018 && (
          <Link href={`/races/${race.race_id}/replay`} className="nav-link">
            Watch Replay
          </Link>
        )}
        <div className="race-header-meta">
          <span>
            <strong>Circuit ID:</strong> {race.circuit_id}
          </span>
          <span>
            <strong>Date:</strong> {new Date(race.date).toLocaleDateString(undefined, {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>
      </header>

      {circuit && (
        <section className="section">
          <h2 className="section-title">Circuit Information</h2>
          <div className="circuit-card">
            <div className="circuit-header">
              <h3 className="circuit-name">{circuit.name}</h3>
              <span className="circuit-location">{circuit.locality}, {circuit.country}</span>
            </div>
            
            <div className="circuit-stats-grid">
              <div className="stat-item">
                <span className="stat-label">Length</span>
                <span className="stat-value">{circuit.length_km} km</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Race Laps</span>
                <span className="stat-value">{circuit.laps}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">First GP Year</span>
                <span className="stat-value">{circuit.first_gp_year}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Downforce Level</span>
                <span className="stat-value capitalize">
                  {circuit.technical_characteristic.downforce_level || 'N/A'}
                </span>
              </div>
              <div className="stat-item" style={{ gridColumn: 'span 2' }}>
                <span className="stat-label">Key Trait</span>
                <span className="stat-value">
                  {circuit.technical_characteristic.key_trait || 'N/A'}
                </span>
              </div>
            </div>

            {circuit.lap_record && (
              <div className="lap-record-box">
                <strong>Lap Record:</strong> {circuit.lap_record.time} (Driver: {circuit.lap_record.driver_id}, {circuit.lap_record.year})
              </div>
            )}

            {circuit.trivia && circuit.trivia.length > 0 && (
              <div className="trivia-section">
                <h4 className="trivia-title">Circuit Trivia</h4>
                <ul className="trivia-list">
                  {circuit.trivia.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      <section className="section">
        <h2 className="section-title">Race Results</h2>
        {race.results && race.results.length > 0 ? (
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Pos</th>
                  <th>Grid</th>
                  <th>Driver ID</th>
                  <th>Constructor</th>
                  <th>Status</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {race.results.map((result, idx) => (
                  <tr key={idx} className={result.finish_position === 1 ? 'podium-1' : result.finish_position === 2 ? 'podium-2' : result.finish_position === 3 ? 'podium-3' : ''}>
                    <td className="font-bold">
                      {result.finish_position !== null ? result.finish_position : '-'}
                    </td>
                    <td>{result.grid_position}</td>
                    <td className="driver-cell">{result.driver_id}</td>
                    <td>{result.constructor_name || result.constructor_id}</td>
                    <td>
                      <span className={`status-pill status-${result.status}`}>
                        {getStatusBadgeText(result.status)}
                      </span>
                    </td>
                    <td className="font-bold">{result.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p>
              Results are not yet available for this race (Status: <strong>{race.status}</strong>).
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
