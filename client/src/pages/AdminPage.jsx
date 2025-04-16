import React from 'react';
import { Box, Typography } from '@mui/material';

function AdminPage() {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4">Admin Panel</Typography>
      <Typography>This page will contain administrative controls for the game.</Typography>
      {/* TODO: Implement admin features (e.g., view players, manage game state) */}
    </Box>
  );
}

export default AdminPage; 