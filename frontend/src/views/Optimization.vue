<template>
  <div class="optimization">
    <div class="page-header">
      <h2><el-icon><Lightning /></el-icon> Оптимизация планирования</h2>
    </div>

    <!-- Параметры оптимизации -->
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>Параметры оптимизации</span>
        </div>
      </template>
      
      <el-form :model="optimizationParams" label-width="200px" style="max-width: 1200px;">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Алгоритм:">
              <el-select v-model="optimizationParams.algorithm" style="width: 100%;">
                <el-option 
                  label="Гибридный (рекомендуется)" 
                  value="hybrid"
                />
                <el-option 
                  label="Генетический алгоритм" 
                  value="genetic"
                />
                <el-option 
                  label="Метод ветвей и границ" 
                  value="branch_bound"
                />
              </el-select>
              <div class="help-text">
                Hybrid - комбинирует генетический алгоритм и метод ветвей и границ для оптимального результата
              </div>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="Горизонт планирования (дни):">
              <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <el-slider
                  v-model="optimizationParams.planning_horizon"
                  :min="1"
                  :max="90"
                  style="flex: 1;"
                />
                <el-input-number
                  v-model="optimizationParams.planning_horizon"
                  :min="1"
                  :max="90"
                  style="width: 100px;"
                />
              </div>
              <div class="help-text">
                Период планирования производства: {{ optimizationParams.planning_horizon }} дней
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" v-if="['genetic', 'hybrid'].includes(optimizationParams.algorithm)">
          <el-col :span="12">
            <el-form-item label="Размер популяции:">
              <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <el-slider
                  v-model="optimizationParams.population_size"
                  :min="20"
                  :max="500"
                  style="flex: 1;"
                />
                <el-input-number
                  v-model="optimizationParams.population_size"
                  :min="20"
                  :max="500"
                  style="width: 100px;"
                />
              </div>
              <div class="help-text">
                Количество особей в популяции генетического алгоритма
              </div>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="Количество поколений:">
              <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <el-slider
                  v-model="optimizationParams.generations"
                  :min="10"
                  :max="200"
                  style="flex: 1;"
                />
                <el-input-number
                  v-model="optimizationParams.generations"
                  :min="10"
                  :max="200"
                  style="width: 100px;"
                />
              </div>
              <div class="help-text">
                Число итераций эволюции генетического алгоритма
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Дополнительная информация о выбранном алгоритме -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="24">
            <el-alert
              v-if="optimizationParams.algorithm === 'hybrid'"
              title="Гибридный алгоритм"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>Автоматически выбирает оптимальный метод:</p>
                <ul style="margin: 5px 0 0 20px;">
                  <li>≤15 заказов: метод ветвей и границ (100% точность)</li>
                  <li>>15 заказов: генетический алгоритм (85-95% точность, быстрое выполнение)</li>
                </ul>
              </template>
            </el-alert>
            
            <el-alert
              v-if="optimizationParams.algorithm === 'genetic'"
              title="Генетический алгоритм"
              type="warning"
              :closable="false"
              show-icon
            >
              Эвристический метод с хорошей масштабируемостью. Точность: 85-95% от оптимума.
            </el-alert>
            
            <el-alert
              v-if="optimizationParams.algorithm === 'branch_bound'"
              title="Метод ветвей и границ"
              type="success"
              :closable="false"
              show-icon
            >
              Точный алгоритм (100% оптимум). Рекомендуется для небольшого количества заказов (≤20).
            </el-alert>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- Кнопка запуска и результаты -->
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Запуск оптимизации</span>
        </div>
      </template>
      
      <el-button 
        type="primary" 
        size="large"
        :loading="optimizing"
        @click="runOptimization"
        style="margin-bottom: 20px;"
      >
        <el-icon><Lightning /></el-icon>
        {{ optimizing ? 'Выполняется оптимизация...' : 'Запустить оптимизацию' }}
      </el-button>
      
      <div class="optimization-status" v-if="optimizing">
        <el-progress 
          :percentage="optimizationProgress" 
          :status="optimizationProgress === 100 ? 'success' : ''"
        />
        <p style="margin-top: 10px; color: #666;">
          Это может занять некоторое время. Пожалуйста, подождите...
        </p>
      </div>

      <!-- Результаты оптимизации -->
      <div v-if="optimizationResult" style="margin-top: 20px;">
        <el-alert
          title="Оптимизация завершена успешно!"
          type="success"
          :closable="false"
          style="margin-bottom: 20px;"
        />
        
        <!-- Метрики результатов -->
        <el-row :gutter="20" style="margin-bottom: 30px;">
          <el-col :span="8">
            <el-card shadow="hover">
              <el-statistic
                title="Общие отходы (кг)"
                :value="parseFloat(optimizationResult.total_waste_kg).toFixed(2)"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #F56C6C;"><Warning /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card shadow="hover">
              <el-statistic
                title="Время выполнения (ч)"
                :value="parseFloat(optimizationResult.total_processing_time_hours).toFixed(1)"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #E6A23C;"><Clock /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card shadow="hover">
              <el-statistic
                title="Время оптимизации (сек)"
                :value="optimizationResult.optimization_time_seconds.toFixed(2)"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #67C23A;"><Timer /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <!-- График загрузки оборудования -->
        <el-card shadow="hover" style="margin-bottom: 20px;" v-if="utilizationChart">
          <template #header>
            <div class="card-header">
              <span>Загрузка оборудования (%)</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="utilizationChartRef"></canvas>
          </div>
        </el-card>

        <!-- Таблица расписания -->
        <el-card shadow="hover" v-if="optimizationResult.schedule">
          <template #header>
            <div class="card-header">
              <span>Оптимизированное расписание</span>
            </div>
          </template>
          <el-table 
            :data="optimizationResult.schedule" 
            stripe
            style="width: 100%"
            max-height="400"
          >
            <el-table-column prop="order_id" label="ID заказа" width="100" />
            <el-table-column prop="equipment_id" label="ID оборудования" width="120" />
            <el-table-column prop="start_time" label="Время начала" width="150" />
            <el-table-column prop="end_time" label="Время окончания" width="150" />
            <el-table-column prop="setup_time" label="Время наладки (мин)" width="140" />
            <el-table-column prop="processing_time" label="Время обработки (мин)" width="160" />
            <el-table-column prop="waste_kg" label="Отходы (кг)" width="120" />
          </el-table>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, nextTick } from 'vue'
import { api } from '../utils/api'
import { Chart, registerables } from 'chart.js'
import { ElMessage } from 'element-plus'

Chart.register(...registerables)

export default {
  name: 'Optimization',
  setup() {
    const optimizing = ref(false)
    const optimizationProgress = ref(0)
    const optimizationResult = ref(null)
    const utilizationChart = ref(null)
    const utilizationChartRef = ref(null)
    
    let utilizationChartInstance = null

    const optimizationParams = reactive({
      algorithm: 'hybrid',
      planning_horizon: 30,
      population_size: 100,
      generations: 50
    })

    // Запуск оптимизации
    const runOptimization = async () => {
      optimizing.value = true
      optimizationProgress.value = 0
      optimizationResult.value = null

      // Симуляция прогресса
      const progressInterval = setInterval(() => {
        if (optimizationProgress.value < 95) {
          optimizationProgress.value += Math.random() * 10
          // Округляем до сотых
          optimizationProgress.value = Math.round(optimizationProgress.value * 100) / 100
        }
      }, 500)

      try {
        const params = {
          algorithm: optimizationParams.algorithm,
          planning_horizon_days: optimizationParams.planning_horizon,
          population_size: optimizationParams.population_size,
          generations: optimizationParams.generations
        }

        console.log('Отправка запроса оптимизации:', params)
        
        // API ожидает параметры как query parameters, а не в теле запроса
        const queryParams = new URLSearchParams({
          algorithm: optimizationParams.algorithm,
          planning_horizon_days: optimizationParams.planning_horizon.toString(),
          population_size: optimizationParams.population_size.toString(),
          generations: optimizationParams.generations.toString()
        })
        
        const result = await api.post(`/optimize/schedule?${queryParams}`)
        console.log('Результат оптимизации:', result)
        
        clearInterval(progressInterval)
        optimizationProgress.value = 100
        
        // Проверяем, что результат не пустой
        if (!result || typeof result !== 'object') {
          throw new Error('Получен пустой или некорректный ответ от сервера')
        }
        
        optimizationResult.value = result
        ElMessage.success('Оптимизация завершена успешно!')
        
        // Создание графика загрузки оборудования
        if (result.equipment_utilization) {
          await prepareUtilizationChart(result.equipment_utilization)
        }
        
      } catch (error) {
        clearInterval(progressInterval)
        console.error('Детали ошибки оптимизации:', error)
        
        // Более детальная обработка ошибок
        let errorMessage = 'Ошибка при выполнении оптимизации'
        if (error.response) {
          // Ошибка HTTP ответа
          errorMessage = `Ошибка сервера: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`
        } else if (error.request) {
          // Запрос был отправлен, но ответа не получено
          errorMessage = 'Сервер не отвечает. Проверьте подключение к API.'
        } else if (error.message) {
          // Другие ошибки
          errorMessage = error.message
        }
        
        ElMessage.error(errorMessage)
      } finally {
        optimizing.value = false
      }
    }

    // Подготовка графика загрузки оборудования
    const prepareUtilizationChart = async (utilization) => {
      const equipmentIds = Object.keys(utilization)
      const utilizationValues = equipmentIds.map(id => utilization[id] * 100)
      
      utilizationChart.value = {
        labels: equipmentIds.map(id => `Оборудование ${id}`),
        data: utilizationValues
      }
      
      await nextTick()
      createUtilizationChart()
    }

    // Создание графика загрузки
    const createUtilizationChart = () => {
      if (utilizationChartRef.value && utilizationChart.value) {
        const ctx = utilizationChartRef.value.getContext('2d')
        
        if (utilizationChartInstance) {
          utilizationChartInstance.destroy()
        }
        
        utilizationChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: utilizationChart.value.labels,
            datasets: [{
              label: 'Загрузка (%)',
              data: utilizationChart.value.data,
              backgroundColor: '#409EFF',
              borderColor: '#337ECC',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                  callback: function(value) {
                    return value + '%'
                  }
                }
              }
            }
          }
        })
      }
    }

    return {
      optimizing,
      optimizationProgress,
      optimizationResult,
      optimizationParams,
      utilizationChart,
      utilizationChartRef,
      runOptimization
    }
  }
}
</script>

<style scoped>
.optimization {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  line-height: 1.4;
}

.optimization-status {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

/* Стили для слайдеров */
.el-slider {
  margin: 8px 0;
}

.el-input-number {
  border-radius: 4px;
}

/* Отступы для алертов */
.el-alert {
  margin-bottom: 15px;
}

.el-alert ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.el-alert li {
  margin: 4px 0;
  color: #606266;
}

/* Улучшенные отступы для form-item */
.el-form-item {
  margin-bottom: 25px;
}

.el-form-item__label {
  font-weight: 500;
  color: #303133;
}

/* Адаптивность */
@media (max-width: 768px) {
  .el-form {
    max-width: 100% !important;
  }
  
  .el-col {
    margin-bottom: 20px;
  }
  
  .el-form-item__label {
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 5px;
  }
}
</style> 