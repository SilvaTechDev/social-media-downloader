const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');
const fs = require('fs');
const { promisify } = require('util');

const app = express();
const PORT = 3000; // Fixed port number

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Ensure downloads directory exists
const mkdir = promisify(fs.mkdir);
const exists = promisify(fs.exists);

(async () => {
    if (!(await exists('downloads'))) {
        await mkdir('downloads');
    }
})();

// API Routes
app.post('/api/download', async (req, res) => {
    try {
        const response = await axios.post('http://localhost:5000/download', req.body);
        res.json(response.data);
    } catch (error) {
        console.error('Download request failed:', error.message);
        res.status(500).json({ 
            error: 'Download failed',
            details: error.response?.data || error.message
        });
    }
});

app.get('/api/progress/:id', async (req, res) => {
    try {
        const response = await axios.get(`http://localhost:5000/progress/${req.params.id}`);
        res.json(response.data);
    } catch (error) {
        console.error('Progress check failed:', error.message);
        res.status(500).json({ 
            error: 'Progress check failed',
            details: error.response?.data || error.message
        });
    }
});

app.get('/api/file/:filename', async (req, res) => {
    try {
        const filepath = path.join(__dirname, 'downloads', req.params.filename);
        
        if (!fs.existsSync(filepath)) {
            return res.status(404).json({ error: 'File not found' });
        }

        res.download(filepath, req.params.filename, (err) => {
            if (err) {
                console.error('File download failed:', err);
                res.status(500).json({ error: 'File download failed' });
            }
        });
    } catch (error) {
        console.error('File request failed:', error);
        res.status(500).json({ error: 'File request failed' });
    }
});

// Frontend route
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});