import React, { useState, useEffect } from 'react';
import { GameModeService } from '../services';
import { TeamService } from '../services';

const TeamDisplay = ({ gameId }) => {
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const response = await TeamService.getTeamStatus(gameId);
        if (response.success) {
          setTeams(response.teams);
          if (response.teams.length > 0) {
            setSelectedTeam(response.teams[0]);
          }
        }
      } catch (err) {
        setError(`Error loading teams: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, [gameId]);

  if (loading) return <div>Loading team data...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!teams.length) return <div>No teams available</div>;

  return (
    <div className="team-display">
      <div className="team-overview">
        <h2>Team Overview</h2>
        <div className="team-stats">
          {teams.map(team => (
            <div 
              key={team.id} 
              className={`team-stat ${team.is_active ? 'active' : 'eliminated'}`}
              style={{ borderLeft: `4px solid ${team.color}` }}
              onClick={() => setSelectedTeam(team)}
            >
              <h3>{team.name}</h3>
              <div className="stat">
                <span className="label">Score:</span>
                <span className="value">${team.score.toLocaleString()}</span>
              </div>
              <div className="stat">
                <span className="label">Players:</span>
                <span className="value">{team.player_count}</span>
              </div>
              <div className="stat">
                <span className="label">Properties:</span>
                <span className="value">{team.property_count}</span>
              </div>
              <div className="stat">
                <span className="label">Shared Cash:</span>
                <span className="value">${team.shared_cash.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedTeam && (
        <div className="team-details">
          <h3>{selectedTeam.name} Details</h3>
          <div className="team-features">
            <div className="feature">
              <span className="label">Property Sharing:</span>
              <span className={`value ${selectedTeam.property_sharing_enabled ? 'enabled' : 'disabled'}`}>
                {selectedTeam.property_sharing_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="feature">
              <span className="label">Rent Immunity:</span>
              <span className={`value ${selectedTeam.rent_immunity_enabled ? 'enabled' : 'disabled'}`}>
                {selectedTeam.rent_immunity_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="feature">
              <span className="label">Income Sharing:</span>
              <span className="value">
                {(selectedTeam.income_sharing_percent * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="team-players">
            <h4>Team Players</h4>
            <ul>
              {selectedTeam.players.map(player => (
                <li key={player.id} className={player.status}>
                  {player.name} (${player.cash.toLocaleString()})
                </li>
              ))}
            </ul>
          </div>

          <div className="team-properties">
            <h4>Team Properties</h4>
            <ul>
              {selectedTeam.properties.map(property => (
                <li key={property.id}>
                  {property.name} (${property.current_price.toLocaleString()})
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamDisplay; 