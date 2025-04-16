# Pi-nopoly Client

This is the client application for Pi-nopoly, a modern take on the classic board game. The client is built with React and communicates with the server using WebSockets.

## Features

- User authentication and registration
- Real-time game updates via WebSockets
- Mobile-responsive design
- Different interfaces for players, admins, and TV display
- Comprehensive financial management system:
  - Real-time financial dashboard
  - Loan management with dynamic calculations
  - CD investment interface
  - HELOC management for property-backed loans

## Setup and Installation

### Prerequisites

- Node.js (v14.0.0 or later)
- npm (v6.0.0 or later)

### Installation

1. Clone the repository
2. Navigate to the client directory: `cd client`
3. Install dependencies: `npm install`
4. Create a `.env` file with the following content:
   ```
   VITE_API_URL=http://localhost:8000/api
   VITE_WS_URL=ws://localhost:8000
   ```

### Development

To start the development server:

```bash
npm run dev
```

The client will run on `http://localhost:3000` by default.

### Building for Production

To create a production build:

```bash
npm run build
```

This will generate optimized assets in the `dist` directory.

## Project Structure

```
client/
├── public/        # Static assets
├── src/
│   ├── contexts/  # React contexts for state management
│   ├── pages/     # Page components
│   ├── components/ # Reusable components
│   │   ├── FinancialDashboard.jsx  # Financial management interface
│   │   ├── NewLoanModal.jsx        # Loan creation modal
│   │   ├── PropertyCard.jsx        # Property display component
│   │   └── PropertyList.jsx        # Property management interface
│   ├── styles/    # CSS stylesheets
│   ├── App.jsx    # Main App component
│   └── index.jsx  # Entry point
└── index.html     # HTML template
```

## Technologies Used

- React (UI library)
- React Router (routing)
- Socket.io Client (WebSockets)
- Vite (build tool)

## Available Routes

- `/` - Home page / login
- `/play` - Player interface
  - `/play/finance` - Financial management dashboard
  - `/play/properties` - Property management
- `/admin` - Admin dashboard
- `/board` - TV display

## Component Usage

### Financial Dashboard

```jsx
// Example usage in a game component
import FinancialDashboard from '../components/FinancialDashboard';

function GameInterface({ player }) {
  const handleTransactionComplete = () => {
    // Refresh game state
  };

  return (
    <FinancialDashboard
      playerId={player.id}
      playerPin={player.pin}
      playerCash={player.cash}
      onTransactionComplete={handleTransactionComplete}
    />
  );
}
```

### Loan Creation

```jsx
// Example usage in a game component
import NewLoanModal from '../components/NewLoanModal';

function LoanSection({ player, interestRate }) {
  const handleLoanConfirm = (amount) => {
    // Process loan creation
  };

  return (
    <NewLoanModal
      onClose={() => setShowModal(false)}
      onConfirm={handleLoanConfirm}
      playerCash={player.cash}
      interestRate={interestRate}
      maxLoanAmount={5000}
    />
  );
}
```

## License

This project is licensed under the MIT License. 