// Typed client for the F1Hub API, mirroring docs/api-contract.md.
// Centralizing endpoint paths + response types here is what keeps this
// frontend from drifting out of sync with an independently-built backend.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request to ${path} failed (${res.status})`);
  }
  return res.json();
}

// ---- Shared enums ----

export type RaceStatus = "upcoming" | "completed" | "postponed" | "cancelled";
export type DriverResultStatus = "finished" | "dnf" | "dsq" | "dns";

// ---- Circuits ----

export interface Circuit {
  circuit_id: string;
  name: string;
  country: string;
  locality: string;
  length_km: number;
  laps: number;
  first_gp_year: number;
  lap_record: { time: string; driver_id: string; year: number } | null;
  trivia: string[];
}

export const getCircuit = (circuitId: string) =>
  apiGet<Circuit>(`/circuits/${circuitId}`);

// ---- Seasons / calendar ----

export const getSeasons = () => apiGet<{ seasons: number[] }>("/seasons");

export interface RaceSummary {
  race_id: string;
  round: number;
  name: string;
  circuit_id: string;
  circuit_name: string;
  date: string;
  status: RaceStatus;
}

export const getSeasonRaces = (season: number) =>
  apiGet<{ season: number; races: RaceSummary[] }>(`/seasons/${season}/races`);

export interface RaceResult {
  driver_id: string;
  constructor_id: string;
  constructor_name: string;
  grid_position: number;
  finish_position: number | null;
  status: DriverResultStatus;
  points: number;
}

export interface RaceDetail {
  race_id: string;
  round: number;
  season: number;
  name: string;
  circuit_id: string;
  date: string;
  status: RaceStatus;
  results: RaceResult[] | null;
}

export const getRace = (raceId: string) =>
  apiGet<RaceDetail>(`/races/${raceId}`);

// ---- Prediction ----

export interface PredictionInputs {
  weather_category: string;
  grid: { driver_id: string; grid_position: number; constructor_id: string }[];
  derived_features: {
    circuit_overtaking_difficulty: number;
    per_constructor: {
      constructor_id: string;
      constructor_recent_form: number;
      constructor_reliability: number;
    }[];
    per_driver: {
      driver_id: string;
      driver_circuit_history: number;
      driver_historical_dnf_rate: number;
    }[];
  };
}

export interface DriverPrediction {
  driver_id: string;
  predicted_finish_position: number;
  dnf_probability: number;
}

export interface PredictionResponse {
  race_id: string;
  model_version: string;
  generated_at: string;
  inputs: PredictionInputs;
  predictions: DriverPrediction[];
}

export const getPrediction = (raceId: string) =>
  apiGet<PredictionResponse>(`/races/${raceId}/prediction`);

// ---- Model explainability ----

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelExplainResponse {
  model_version: string;
  finish_position_model: { feature_importances: FeatureImportance[] };
  dnf_model: { feature_importances: FeatureImportance[] };
}

export const getModelExplanation = (modelVersion: string) =>
  apiGet<ModelExplainResponse>(`/models/${modelVersion}/explain`);

// ---- Accuracy tracker ----

export interface AccuracySummary {
  mean_absolute_position_error: number;
  dnf_brier_score: number;
  rank_correlation: number;
  podium_hit_rate: number;
}

export interface RaceAccuracyResponse {
  race_id: string;
  model_version: string;
  per_driver: {
    driver_id: string;
    predicted_finish_position: number;
    actual_finish_position: number | null;
    actual_status: DriverResultStatus;
    position_error: number | null;
  }[];
  summary: AccuracySummary;
}

export const getRaceAccuracy = (raceId: string) =>
  apiGet<RaceAccuracyResponse>(`/races/${raceId}/accuracy`);

export interface SeasonAccuracyResponse {
  season: number;
  races: ({ race_id: string; round: number } & AccuracySummary)[];
  season_running_average: AccuracySummary;
}

export const getSeasonAccuracy = (season: number) =>
  apiGet<SeasonAccuracyResponse>(`/seasons/${season}/accuracy`);

// ---- Standings ----

export interface DriverStanding {
  driver_id: string;
  constructor_id: string;
  constructor_name: string;
  position: number;
  points: number;
  wins: number;
  podiums: number;
  trend: number[];
}

export const getDriverStandings = (season: number) =>
  apiGet<{ season: number; as_of_round: number; standings: DriverStanding[] }>(
    `/standings/drivers?season=${season}`
  );

export interface ConstructorStanding {
  constructor_id: string;
  position: number;
  points: number;
  wins: number;
  podiums: number;
  trend: number[];
}

export const getConstructorStandings = (season: number) =>
  apiGet<{
    season: number;
    as_of_round: number;
    standings: ConstructorStanding[];
  }>(`/standings/constructors?season=${season}`);

// ---- Drivers ----

export interface Driver {
  driver_id: string;
  name: string;
  nationality: string;
  date_of_birth: string;
  current_constructor_id: string;
  career: { wins: number; podiums: number; poles: number; championships: number };
}

export const getDriver = (driverId: string) =>
  apiGet<Driver>(`/drivers/${driverId}`);

export const compareDrivers = (
  driverA: string,
  driverB: string,
  season?: number
) => {
  const query = season ? `&season=${season}` : "";
  return apiGet<{
    driver_a: string;
    driver_b: string;
    season: number | null;
    head_to_head: {
      qualifying_wins: Record<string, number>;
      race_finish_wins: Record<string, number>;
      points: Record<string, number>;
    };
  }>(`/drivers/compare?driver_a=${driverA}&driver_b=${driverB}${query}`);
};

// ---- Constructors ----

export interface Constructor {
  constructor_id: string;
  name: string;
  nationality: string;
  current_drivers: string[];
  career: { wins: number; podiums: number; poles: number; championships: number };
}

export const getConstructor = (constructorId: string) =>
  apiGet<Constructor>(`/constructors/${constructorId}`);

export const compareConstructors = (
  constructorA: string,
  constructorB: string,
  season?: number
) => {
  const query = season ? `&season=${season}` : "";
  return apiGet<{
    constructor_a: string;
    constructor_b: string;
    season: number | null;
    head_to_head: {
      race_wins: Record<string, number>;
      points: Record<string, number>;
      podiums: Record<string, number>;
    };
  }>(
    `/constructors/compare?constructor_a=${constructorA}&constructor_b=${constructorB}${query}`
  );
};

// ---- Replay ----

export interface ReplayResponse {
  race_id: string;
  total_laps: number;
  drivers: {
    driver_id: string;
    laps: { lap: number; position: number; gap_to_leader_s: number }[];
  }[];
}

export const getReplay = (raceId: string) =>
  apiGet<ReplayResponse>(`/races/${raceId}/replay`);
