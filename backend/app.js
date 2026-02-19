require('dotenv').config();
const express = require('express');
const cors = require('cors');
const projectRoutes = require('./routes/projects');
const taskRoutes = require('./routes/tasks');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api', projectRoutes);
app.use('/api', taskRoutes);

module.exports = app;
