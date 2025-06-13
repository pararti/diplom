import axios from 'axios'

// В Docker окружении API доступно через nginx proxy
// В режиме разработки - напрямую к API серверу
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// Создаем инстанс axios с базовой конфигурацией
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Интерсептор для обработки ошибок
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Утилитарные функции для работы с API
export const api = {
  // GET запрос
  async get(endpoint, params = {}) {
    try {
      const response = await apiClient.get(endpoint, { params })
      return response.data
    } catch (error) {
      throw new Error(`GET ${endpoint}: ${error.message}`)
    }
  },

  // POST запрос
  async post(endpoint, data = {}) {
    try {
      const response = await apiClient.post(endpoint, data)
      return response.data
    } catch (error) {
      throw new Error(`POST ${endpoint}: ${error.message}`)
    }
  },

  // PUT запрос
  async put(endpoint, data = {}) {
    try {
      const response = await apiClient.put(endpoint, data)
      return response.data
    } catch (error) {
      throw new Error(`PUT ${endpoint}: ${error.message}`)
    }
  },

  // DELETE запрос
  async delete(endpoint) {
    try {
      const response = await apiClient.delete(endpoint)
      return response.data
    } catch (error) {
      throw new Error(`DELETE ${endpoint}: ${error.message}`)
    }
  }
}

export { apiClient }
export default api 