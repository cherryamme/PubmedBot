interface BadgeProps {
  text: string;
  color?: 'green' | 'blue' | 'yellow' | 'gray' | 'red' | 'purple';
}

const colorMap = {
  green: 'bg-green-100 text-green-800',
  blue: 'bg-blue-100 text-blue-800',
  yellow: 'bg-yellow-100 text-yellow-800',
  gray: 'bg-gray-100 text-gray-600',
  red: 'bg-red-100 text-red-800',
  purple: 'bg-purple-100 text-purple-800',
};

export default function Badge({ text, color = 'gray' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorMap[color]}`}>
      {text}
    </span>
  );
}

export function IFBadge({ value, partition }: { value?: number; partition?: string }) {
  if (value == null) return null;
  let color: BadgeProps['color'] = 'gray';
  if (partition) {
    if (partition.includes('1') || partition.toUpperCase().includes('Q1')) color = 'green';
    else if (partition.includes('2') || partition.toUpperCase().includes('Q2')) color = 'blue';
    else if (partition.includes('3') || partition.toUpperCase().includes('Q3')) color = 'yellow';
  } else {
    if (value >= 10) color = 'green';
    else if (value >= 5) color = 'blue';
    else if (value >= 3) color = 'yellow';
  }
  const label = partition ? `IF ${value.toFixed(1)} · ${partition}` : `IF ${value.toFixed(1)}`;
  return <Badge text={label} color={color} />;
}

export function OABadge() {
  return <Badge text="OA" color="green" />;
}
