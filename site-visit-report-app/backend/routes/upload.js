const express = require('express');
const multer = require('multer');
const OpenAIApi = require('openai');
const router = express.Router();
require('dotenv').config();

// Set up Multer for handling file uploads (stored in memory)
const upload = multer({ storage: multer.memoryStorage() });

// OpenAI API configuration
const openai = new OpenAIApi({ key: ''});

// Route to generate description based on uploaded photos
router.post('/generate-description', upload.array('photos', 10), async (req, res) => {
  const photos = req.files; // Get uploaded photos from the request

  if (!photos || photos.length === 0) {
    return res.status(400).json({ error: 'No photos uploaded' });
  }

  // For simplicity, simulate the image description
  const imageDescriptions = photos.map((photo, index) => `Image ${index + 1}: ${photo.originalname}`).join(', ');

  const prompt = `Generate a site visit report based on the following image descriptions: ${imageDescriptions}.`;

  try {
    // Call the OpenAI API to generate the description using GPT-4
    const response = await openai.createChatCompletion({
      model: "gpt-4",
      messages: [{ role: "system", content: prompt }],
      max_tokens: 300,
    });

    // Extract the generated description
    const description = response.data.choices[0].message.content.trim();
    res.json({ description });
  } catch (error) {
    console.error('Error generating description:', error.response ? error.response.data : error.message);  // Log detailed error
    res.status(500).json({ error: 'Error generating description' });
  }
});

module.exports = router;
