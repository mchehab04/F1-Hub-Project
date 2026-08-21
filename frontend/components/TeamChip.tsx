'use client';

import Link from 'next/link';
import { getContrastText, getTeamColor } from '@/lib/teamColors';

export function TeamChip({
  constructorId,
  label,
}: {
  constructorId: string;
  label: string;
}) {
  const color = getTeamColor(constructorId);
  const textColor = getContrastText(color);

  return (
    <Link
      href={`/constructors/${constructorId}`}
      className="team-chip"
      style={{ backgroundColor: color, color: textColor }}
    >
      {label}
    </Link>
  );
}
