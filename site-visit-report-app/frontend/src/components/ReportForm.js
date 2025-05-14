import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import config from '../config';

const ReportForm = ({ images, setImages }) => {
  const [projectName, setProjectName] = useState(''); 
  const [reportNumber, setReportNumber] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState(''); 
  const [action, setAction] = useState('');
  const [isGenerating, setIsGenerating] = useState({}); // Track loading state for each image
  const [isSummarizing, setIsSummarizing] = useState(false); // Track summary generation state
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false); // Track PDF generation state

  // Add the missing handleCaptionChange function
  const handleCaptionChange = (index, newCaption) => {
    setImages(prevImages => {
      const updatedImages = [...prevImages];
      updatedImages[index] = {
        ...updatedImages[index],
        caption: newCaption
      };
      return updatedImages;
    });
  };

  // Add new function to handle hashtag changes
  const handleHashtagChange = (index, newHashtags) => {
    setImages(prevImages => {
      const updatedImages = [...prevImages];
      updatedImages[index] = {
        ...updatedImages[index],
        hashtags: newHashtags
      };
      return updatedImages;
    });
  };

  // Handle file changes for photo uploads
  const handleFileChange = (e) => {
    if (!e.target.files || e.target.files.length === 0) {
      return; // No files selected
    }
    
    const files = Array.from(e.target.files);
    const newImages = files.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      caption: '',
      hashtags: ''
    }));
    
    setImages([...images, ...newImages]);
    
    // Reset the input to ensure onChange will fire even if the same file is selected again
    e.target.value = '';
  };

  // Handle individual photo deletion
  const handleDeletePhoto = (index) => {
    if (window.confirm('Are you sure you want to delete this photo?')) {
      setImages(prevImages => {
        const newImages = [...prevImages];
        URL.revokeObjectURL(newImages[index].preview); // Clean up the object URL
        newImages.splice(index, 1);
        return newImages;
      });
      
      // Reset the file input so the same file can be uploaded again
      document.getElementById('Photos').value = '';
    }
  };

  // Handle all photos deletion
  const handleDeleteAllPhotos = () => {
    if (window.confirm('Are you sure you want to delete all photos?')) {
      images.forEach(image => URL.revokeObjectURL(image.preview)); // Clean up all object URLs
      setImages([]);
      
      // Reset the file input so the same files can be uploaded again
      document.getElementById('Photos').value = '';
    }
  };

  // Function to generate description for a specific image
  const generateDescription = async (index) => {
    const formData = new FormData();
    formData.append('image', images[index].file);
    formData.append('hashtags', images[index].hashtags);

    // Set loading state for this specific image
    setIsGenerating(prev => ({ ...prev, [index]: true }));

    try {
      const response = await fetch(`${config.apiBaseUrl}/analyze-image`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (data.description) {
        // Update only the caption for the specific image
        setImages(prevImages => {
          const updatedImages = [...prevImages];
          updatedImages[index] = {
            ...updatedImages[index],
            caption: data.description
          };
          return updatedImages;
        });
      } else {
        alert('Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error generating caption with Claude. Please try again.');
    } finally {
      // Clear loading state for this specific image
      setIsGenerating(prev => ({ ...prev, [index]: false }));
    }
  };

  // Function to summarize all captions using Anthropic's Claude
  const generateObservations = async () => {
    // Check if we have any images with captions
    const captionsToSummarize = images.map(img => img.caption).filter(caption => caption.trim() !== '');
    
    if (captionsToSummarize.length === 0) {
      alert('Please generate captions for at least one image first.');
      return;
    }

    setIsSummarizing(true);

    try {
      const response = await fetch(`${config.apiBaseUrl}/summarize-captions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          captions: captionsToSummarize
        }),
      });

      const data = await response.json();
      
      if (data.summary) {
        setDescription(data.summary);
      } else {
        alert('Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error generating observations. Please try again.');
    } finally {
      setIsSummarizing(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate required fields first
    if (!projectName || !reportNumber || !subject) {
      alert('Please fill in the Project, Report Number, and Subject fields');
      return;
    }

    setIsGeneratingPDF(true);

    // Generate PDF report
    generatePDFReport()
      .then(() => {
        // After PDF generation, save to database (original handleSubmit functionality)
    const formData = new FormData();
    formData.append('projectName', projectName);
    formData.append('reportNumber', reportNumber);
    formData.append('subject', subject);
        formData.append('description', description);
    formData.append('action', action);
        images.forEach((image, i) => formData.append(`photos`, image.file));

        return axios.post('/api/reports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
        });
    })
    .then(response => {
      console.log('Report created successfully:', response.data);
      // Optionally reset the form fields after successful submission
      setProjectName('100 Roy Street');  // Reset to default
      setReportNumber('SV.24');  // Reset to default
      setSubject('');
      setDescription(''); 
      setAction('');
        setImages([]);
    })
    .catch(error => {
      console.error('Error creating report:', error);
      })
      .finally(() => {
        setIsGeneratingPDF(false);
    });
  };

  // Function to generate PDF report
  const generatePDFReport = async () => {
    try {
      // Prepare images data with base64 encoding for PDF generation
      const imagesWithData = await Promise.all(
        images.map(async (image, index) => {
          let dataUrl = image.preview;

          if (!dataUrl || !dataUrl.startsWith('data:')) {
            console.log(`Image ${index + 1} preview is not a valid data URL, converting from file...`);
            
            if (!image.file) {
              console.warn(`Image ${index + 1} has no file or valid data URL, skipping`);
              return null;
            }
            
            const reader = new FileReader();
            dataUrl = await new Promise((resolve) => {
              reader.onloadend = () => resolve(reader.result);
              reader.readAsDataURL(image.file);
            });
            
            if (!dataUrl || !dataUrl.startsWith('data:')) {
              console.warn(`Failed to create a valid data URL for image ${index + 1}, skipping`);
              return null;
            }
          }

          return {
            dataUrl: dataUrl,
            caption: image.caption || '',
            hashtags: image.hashtags || ''
          };
        })
      );

      // Filter out any null entries (failed conversions)
      const validImages = imagesWithData.filter(img => img !== null);
      
      console.log(`Sending ${validImages.length} valid images for PDF generation`);

      // Prepare report data
      const reportData = {
        projectName,
        reportNumber,
        subject,
        description,
        action,
        images: validImages
      };

      // Make API call to generate PDF
      const response = await fetch(`${config.apiBaseUrl}/generate-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `Site_Visit_Report_${reportNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return Promise.resolve();  // Return a resolved promise for chaining
    } catch (error) {
      console.error('Error generating PDF report:', error);
      alert('Error generating PDF report. Please try again.');
      return Promise.reject(error);  // Return rejected promise for chaining
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 md:p-8">
      <Card className="w-full max-w-6xl mx-auto bg-white shadow-sm">
        <CardHeader className="border-b border-gray-200">
          <CardTitle className="text-2xl font-semibold text-gray-800">Site Visit Report</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 p-6 bg-white">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
              <label htmlFor="project" className="text-sm font-medium text-gray-700 block mb-2">
                  Project
                </label>
                <input
                  type="text"
                id="project"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                />
              </div>
              <div>
              <label htmlFor="ReportNumber" className="text-sm font-medium text-gray-700 block mb-2">
                  Report Number
                </label>
                <input
                  type="text"
                  value={reportNumber}
                  onChange={(e) => setReportNumber(e.target.value)}
                className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                />
              </div>
          </div>
              <div>
            <label htmlFor="Subject" className="text-sm font-medium text-gray-700 block mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                />
              </div>
              <div>
            <label htmlFor="Description" className="text-sm font-medium text-gray-700 block mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
              className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
            ></textarea>
          </div>
          <div>
            <label htmlFor="Action" className="text-sm font-medium text-gray-700 block mb-2">
              Action
            </label>
            <textarea
              id="Action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors mb-4"
              placeholder="Enter action items or recommendations..."
            ></textarea>
            <div className="flex justify-end mb-4">
                  <Button
                    type="button"
                    onClick={generateObservations}
                    className="bg-orange-500 text-white hover:bg-orange-600 transition-colors"
                    disabled={isSummarizing}
                  >
                {isSummarizing ? 'Generating...' : 'Generate Report'}
                  </Button>
                </div>
            <label htmlFor="Photos" className="text-sm font-medium text-gray-700 block">
              Upload Photos
                </label>
            <div className="mt-2">
                  <input
                    type="file"
                    id="Photos"
                onChange={handleFileChange}
                    multiple
                accept="image/*,.png,image/png"
                className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-orange-500 file:text-white hover:file:bg-orange-600 transition-colors"
                  />
                </div>
          </div>
        </CardContent>
      </Card>

      {/* Photo grid */}
      {images.length > 0 && (
        <>
          <div className="flex justify-between items-center mt-6 mb-2">
            <h3 className="text-lg font-medium text-gray-800">Uploaded Photos ({images.length})</h3>
            {images.length > 1 && (
              <Button
                type="button"
                onClick={handleDeleteAllPhotos}
                className="bg-red-500 text-white hover:bg-red-600 transition-colors text-xs py-1 px-3"
                aria-label="Delete all photos"
              >
                Delete All Photos
              </Button>
            )}
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {images.map((image, index) => (
              <div key={index} className="rounded-lg overflow-hidden bg-white border border-gray-200 relative">
                <button
                  type="button"
                  onClick={() => handleDeletePhoto(index)}
                  className="absolute right-2 top-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600 transition-colors z-10 shadow-md"
                  aria-label="Delete photo"
                >
                  ✕
                </button>
                <div className="aspect-video relative bg-gray-100">
                      <img
                        src={image.preview}
                        alt={`Preview ${index + 1}`}
                    className="w-full h-full object-cover"
                      />
                </div>
                      <div className="p-4 space-y-3">
                  <div className="space-y-2">
                        <textarea
                          value={image.caption}
                          onChange={(e) => handleCaptionChange(index, e.target.value)}
                      className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                          placeholder="Image caption..."
                          rows={3}
                        />
                    <input
                      type="text"
                      value={image.hashtags}
                      onChange={(e) => handleHashtagChange(index, e.target.value)}
                      className="w-full rounded-md border border-gray-300 bg-gray-50 text-gray-700 px-3 py-2 text-sm shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                      placeholder="Add hashtags (e.g., #window #sealant #damage)"
                    />
                  </div>
                        <Button
                          type="button"
                          onClick={() => generateDescription(index)}
                          className="w-full bg-orange-500 text-white hover:bg-orange-600 transition-colors"
                          disabled={isGenerating[index]}
                        >
                    {isGenerating[index] ? 'Generating...' : 'Generate Caption with Claude 3'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
        </>
      )}

      <CardFooter className="border-t border-gray-200/10 bg-gray-50">
        <div className="flex w-full justify-end gap-4">
          <Button 
            type="submit" 
            onClick={handleSubmit}
            className="bg-orange-500 text-white hover:bg-orange-600 transition-colors"
            disabled={isGeneratingPDF}
          >
            {isGeneratingPDF ? 'Generating Report...' : 'Create Report'}
          </Button>
        </div>
        </CardFooter>
    </div>
  );
};

export default ReportForm;
