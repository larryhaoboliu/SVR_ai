const express = require('express');
const router = express.Router();

// Define any report-related routes
router.get('/', (req, res) => {
  res.json({ message: 'This is the reports API' });
});

module.exports = router;
