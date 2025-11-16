import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const videoApiClient = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 minutes for large file uploads
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

const videoApiService = {
  // Upload video
  uploadVideo: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await videoApiClient.post('/video/upload', formData, {
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        if (onProgress) onProgress(percentCompleted);
      },
    });
    
    return response.data;
  },

  // Get video info
  getVideoInfo: async (videoId) => {
    const response = await axios.get(`${API_BASE}/video/${videoId}/info`);
    return response.data;
  },

  // Get video stream URL
  getVideoStreamUrl: (videoId) => {
    return `${API_BASE}/video/${videoId}/stream`;
  },

  // Get thumbnail URL
  getThumbnailUrl: (videoId) => {
    return `${API_BASE}/video/${videoId}/thumbnail`;
  },

  // Trim video
  trimVideo: async (videoId, startTime, endTime) => {
    const response = await axios.post(`${API_BASE}/video/trim`, {
      video_id: videoId,
      start_time: startTime,
      end_time: endTime,
    });
    return response.data;
  },

  // Cut video
  cutVideo: async (videoId, segments) => {
    const response = await axios.post(`${API_BASE}/video/cut`, {
      video_id: videoId,
      segments: segments,
    });
    return response.data;
  },

  // Generate captions
  generateCaptions: async (videoId, language = null) => {
    const response = await axios.post(`${API_BASE}/video/captions`, {
      video_id: videoId,
      language: language,
    });
    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId) => {
    const response = await axios.get(`${API_BASE}/job/${jobId}`);
    return response.data;
  },

  // Poll job until complete
  pollJobStatus: async (jobId, onProgress) => {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const status = await videoApiService.getJobStatus(jobId);
          
          if (onProgress) onProgress(status);
          
          if (status.status === 'completed') {
            clearInterval(interval);
            resolve(status);
          } else if (status.status === 'failed') {
            clearInterval(interval);
            reject(new Error(status.error || 'Job failed'));
          }
        } catch (error) {
          clearInterval(interval);
          reject(error);
        }
      }, 2000); // Poll every 2 seconds
    });
  },

  // Download processed video
  getDownloadUrl: (resultId) => {
    return `${API_BASE}/video/download/${resultId}`;
  },

  // Download SRT
  getSrtUrl: (captionId) => {
    return `${API_BASE}/captions/${captionId}/srt`;
  },

  // Download VTT
  getVttUrl: (captionId) => {
    return `${API_BASE}/captions/${captionId}/vtt`;
  },

  // List videos
  listVideos: async () => {
    const response = await axios.get(`${API_BASE}/videos`);
    return response.data;
  },
};

export default videoApiService;
