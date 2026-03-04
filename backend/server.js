const express = require('express');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://127.0.0.1:5050';
console.log('--- BACKEND CONFIGURATION ---');
console.log('ML_SERVICE_URL:', ML_SERVICE_URL);
console.log('PORT:', PORT);
console.log('----------------------------');

app.use(cors());
app.use(express.json());

// Proxy route to ML Service
app.post('/api/chat', async (req, res) => {
    const targetUrl = `${ML_SERVICE_URL}/query`;
    console.log(`Forwarding query to: ${targetUrl}`);

    try {
        const response = await axios.post(targetUrl, req.body, {
            timeout: 60000
        });
        res.json(response.data);
    } catch (error) {
        console.error(`ERROR calling ML Service at ${targetUrl}:`, error.message);

        if (error.response) {
            console.error('ML Service Status:', error.response.status);
            console.error('ML Service Data:', error.response.data);
            return res.status(error.response.status).json(error.response.data);
        }

        // Generic fallback with diagnostic info
        res.json({
            response: `Connection Error: Backend could not reach AI service at ${ML_SERVICE_URL}.`,
            diagnostics: {
                target: targetUrl,
                error: error.message,
                hint: "Check if ML_SERVICE_URL in Render matches your ML service's public URL and remove any ':5050' if present."
            }
        });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'Backend is running' });
});

app.listen(PORT, () => {
    console.log(`Backend Server running on port ${PORT}`);
});
