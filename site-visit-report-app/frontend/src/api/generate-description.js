const { Configuration, OpenAIApi } = require('openai');

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY, // Ensure the API key is in your .env
});

const openai = new OpenAIApi({ key: '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'});

app.post('/api/generate-description', async (req, res) => {
  const { photos } = req.body; // You will need to handle uploading and parsing photos

  const prompt = `Generate a site visit report description based on the following photos: ${photos.join(', ')}`;

  try {
    const response = await openai.createCompletion({
      model: "text-davinci-003",
      prompt: prompt,
      max_tokens: 300,
    });

    const description = response.data.choices[0].text;
    res.json({ description });
  } catch (error) {
    console.error('Error generating description:', error);
    res.status(500).json({ error: 'Error generating description' });
  }
});
