import { cn } from '../utils/cn';

export interface AvatarProps {
  name?: string;
  emoji?: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'h-8 w-8 text-sm',
  md: 'h-10 w-10 text-base',
  lg: 'h-12 w-12 text-xl',
  xl: 'h-16 w-16 text-2xl',
};

export function Avatar({ name, emoji, color, size = 'md', className }: AvatarProps) {
  // Generate color from name if not provided
  const bgColor = color || generateColor(name || '');

  // Get initials from name
  const initials = name
    ? name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '?';

  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center font-bold text-white',
        sizeClasses[size],
        className
      )}
      style={{ backgroundColor: bgColor }}
    >
      {emoji || initials}
    </div>
  );
}

function generateColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }

  const colors = [
    '#e74c3c',
    '#3498db',
    '#2ecc71',
    '#9b59b6',
    '#f39c12',
    '#1abc9c',
    '#e91e63',
    '#00bcd4',
  ];

  return colors[Math.abs(hash) % colors.length];
}
