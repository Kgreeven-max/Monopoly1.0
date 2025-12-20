interface SystemStats {
  activeGames: number;
  totalPlayers: number;
  gamesPlayedToday: number;
  serverUptime: number;
  memoryUsage: number;
  cpuUsage: number;
}

interface StatsCardsProps {
  stats: SystemStats | null;
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      label: 'Active Games',
      value: stats?.activeGames ?? '-',
      icon: '🎮',
      color: 'text-blue-400',
    },
    {
      label: 'Total Players',
      value: stats?.totalPlayers ?? '-',
      icon: '👥',
      color: 'text-green-400',
    },
    {
      label: 'Games Today',
      value: stats?.gamesPlayedToday ?? '-',
      icon: '📊',
      color: 'text-yellow-400',
    },
    {
      label: 'Server Uptime',
      value: stats ? formatUptime(stats.serverUptime) : '-',
      icon: '⏱️',
      color: 'text-purple-400',
    },
    {
      label: 'Memory Usage',
      value: stats ? `${stats.memoryUsage.toFixed(1)}%` : '-',
      icon: '💾',
      color: stats && stats.memoryUsage > 80 ? 'text-red-400' : 'text-cyan-400',
    },
    {
      label: 'CPU Usage',
      value: stats ? `${stats.cpuUsage.toFixed(1)}%` : '-',
      icon: '⚡',
      color: stats && stats.cpuUsage > 80 ? 'text-red-400' : 'text-emerald-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="card">
          <div className="flex items-center gap-2 mb-2">
            <span>{card.icon}</span>
            <span className="text-sm text-slate-400">{card.label}</span>
          </div>
          <p className={`text-2xl font-bold ${card.color}`}>
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }

  return `${hours}h ${minutes}m`;
}
