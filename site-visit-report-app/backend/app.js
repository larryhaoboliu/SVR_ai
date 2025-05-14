require('dotenv').config();

const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const mongoose = require('mongoose');

// Load environment variables from .env file
dotenv.config();

const app = express();

// Middleware
app.use(cors());  // Enable CORS
app.use(express.json());  // Parse incoming JSON requests

// MongoDB connection (optional, if you're using MongoDB)
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
  .then(() => console.log('Connected to MongoDB'))
  .catch((err) => console.error('MongoDB connection error:', err));

// Import the routes from upload.js
const generateDescriptionRoute = require('./routes/upload');

// Use the routes with the '/api' prefix
app.use('/api', generateDescriptionRoute);

// Example route to check if the server is running
app.get('/', (req, res) => {
  res.send('Backend server is running!');
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
