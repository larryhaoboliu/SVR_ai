const { Configuration, OpenAIApi } = require('openai');

const configuration = new Configuration({
  apiKey: 'your-api-key-here',
});

const openai = new OpenAIApi(configuration);

async function testOpenAI() {
  try {
    const response = await openai.createCompletion({
      model: 'text-davinci-003',
      prompt: 'Hello, world!',
      max_tokens: 5,
    });
    console.log(response.data.choices[0].text);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testOpenAI();
