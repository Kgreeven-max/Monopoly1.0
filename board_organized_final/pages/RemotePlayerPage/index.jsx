import React from 'react';
import { Box, Typography } from '@mui/material';

function RemotePlayerPage() {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4">TV Display / Remote View</Typography>
      <Typography>This page will show a simplified view suitable for display screens.</Typography>
      {/* TODO: Implement display logic, likely via WebSockets */}
    </Box>
  );
}

export default RemotePlayerPage; 