import React, { useState } from 'react';
import axios from 'axios';

const Report = () => {
  const [file, setFile] = useState(null);
  const [observations, setObservations] = useState('');

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append('photo', file);

    const response = await axios.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    setObservations(response.data.observations);
  };

  return (
    <div>
      <h2>Create Report</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleSubmit}>Upload and Analyze</button>

      <div>
        <h3>Observations</h3>
        <textarea value={observations} readOnly />
      </div>
    </div>
  );
};

export default Report;
