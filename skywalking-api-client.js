/**
 * SkyWalking API Client
 * Provides methods to interact with the SkyWalking monitoring backend APIs
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/skywalking',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for adding auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('SkyWalking API Error:', error.message)
    return Promise.reject(error)
  }
)

/**
 * Get trace detail by trace ID
 * @param {string} traceId - The trace ID to query
 * @returns {Promise<Object>} Trace detail data
 */
export function getTraceDetail(traceId) {
  return apiClient.get(`/trace/${traceId}`)
}

/**
 * Get list of all monitored services
 * @returns {Promise<Array>} List of services
 */
export function getServiceList() {
  return apiClient.get('/services')
}

/**
 * Get service topology graph
 * @returns {Promise<Object>} Topology data with nodes and edges
 */
export function getServiceTopology() {
  return apiClient.get('/topology')
}

/**
 * Get metrics data for a specific metric
 * @param {string} metricName - Name of the metric
 * @param {string} [serviceId] - Optional service ID filter
 * @returns {Promise<Object>} Metrics data
 */
export function getMetricsData(metricName, serviceId) {
  const params = { metricName }
  if (serviceId) {
    params.serviceId = serviceId
  }
  return apiClient.get('/metrics', { params })
}

/**
 * Search traces with optional filters
 * @param {Object} [params] - Search parameters
 * @param {string} [params.serviceId] - Filter by service ID
 * @param {number} [params.startTime] - Start timestamp
 * @param {number} [params.endTime] - End timestamp
 * @returns {Promise<Array>} List of traces
 */
export function searchTraces(params = {}) {
  return apiClient.get('/traces/search', { params })
}

/**
 * Get recent alarms
 * @param {number} [limit=50] - Maximum number of alarms to return
 * @returns {Promise<Array>} List of alarms
 */
export function getAlarms(limit = 50) {
  return apiClient.get('/alarms', { params: { limit } })
}

/**
 * Check SkyWalking OAP server health status
 * @returns {Promise<Object>} Health check result
 */
export function checkHealth() {
  return apiClient.get('/health')
}

export default {
  getTraceDetail,
  getServiceList,
  getServiceTopology,
  getMetricsData,
  searchTraces,
  getAlarms,
  checkHealth
}
