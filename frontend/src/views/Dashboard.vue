<template>
  <div class="dashboard">
    <div class="page-header">
      <h2><el-icon><Odometer /></el-icon> Главная панель</h2>
    </div>

    <!-- Статус системы -->
    <el-alert
      v-if="systemStatus"
      :title="systemStatus === 'ok' ? 'Система работает нормально' : 'Проблемы с подключением к серверу'"
      :type="systemStatus === 'ok' ? 'success' : 'error'"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <!-- Метрики -->
    <el-row :gutter="20" v-if="metrics" style="margin-bottom: 30px">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic
            title="Всего заказов"
            :value="metrics.totalOrders"
            suffix=""
          >
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic
            title="Активные заказы"
            :value="metrics.activeOrders"
            suffix=""
          >
            <template #prefix>
              <el-icon><Clock /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic
            title="Доступное оборудование"
            :value="`${metrics.availableEquipment}/${metrics.totalEquipment}`"
            suffix=""
          >
            <template #prefix>
              <el-icon><Setting /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic
            title="Материалов в базе"
            :value="metrics.totalMaterials"
            suffix=""
          >
            <template #prefix>
              <el-icon><Box /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- Графики -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Распределение заказов по статусам</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="statusChartRef" v-if="chartData.statusChart"></canvas>
            <div v-else class="chart-loading">
              <el-icon class="loading-icon"><Loading /></el-icon>
              <p>Загрузка данных...</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Заказы по типам процессов</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="processChartRef" v-if="chartData.processChart"></canvas>
            <div v-else class="chart-loading">
              <el-icon class="loading-icon"><Loading /></el-icon>
              <p>Загрузка данных...</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { api } from '../utils/api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'Dashboard',
  setup() {
    const systemStatus = ref(null)
    const metrics = ref(null)
    const chartData = ref({
      statusChart: null,
      processChart: null
    })
    
    const statusChartRef = ref(null)
    const processChartRef = ref(null)
    
    let statusChart = null
    let processChart = null

    // Проверка здоровья системы
    const checkSystemHealth = async () => {
      try {
        await api.get('/health')
        systemStatus.value = 'ok'
      } catch (error) {
        systemStatus.value = 'error'
      }
    }

    // Загрузка метрик
    const loadMetrics = async () => {
      try {
        const [ordersData, equipmentData, materialsData] = await Promise.all([
          api.get('/orders/', { limit: 500 }),
          api.get('/equipment/'),
          api.get('/materials/')
        ])

        const activeOrders = ordersData.filter(o => 
          ['planned', 'in_progress'].includes(o.status)
        ).length

        const availableEquipment = equipmentData.filter(e => e.is_available).length

        metrics.value = {
          totalOrders: ordersData.length,
          activeOrders,
          availableEquipment,
          totalEquipment: equipmentData.length,
          totalMaterials: materialsData.length
        }

        // Подготовка данных для графиков
        await prepareChartData(ordersData)
      } catch (error) {
        console.error('Error loading metrics:', error)
      }
    }

    // Подготовка данных для графиков
    const prepareChartData = async (ordersData) => {
      // График по статусам
      const statusCounts = {}
      ordersData.forEach(order => {
        const status = order.status
        statusCounts[status] = (statusCounts[status] || 0) + 1
      })

      // График по процессам
      const processCounts = {}
      ordersData.forEach(order => {
        const process = order.process_type
        processCounts[process] = (processCounts[process] || 0) + 1
      })

      chartData.value = {
        statusChart: {
          labels: Object.keys(statusCounts),
          data: Object.values(statusCounts)
        },
        processChart: {
          labels: Object.keys(processCounts),
          data: Object.values(processCounts)
        }
      }

      // Создание графиков после обновления DOM
      await nextTick()
      createCharts()
    }

    // Создание графиков
    const createCharts = () => {
      // График по статусам (круговая диаграмма)
      if (statusChartRef.value && chartData.value.statusChart) {
        const ctx = statusChartRef.value.getContext('2d')
        
        if (statusChart) {
          statusChart.destroy()
        }
        
        statusChart = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: chartData.value.statusChart.labels,
            datasets: [{
              data: chartData.value.statusChart.data,
              backgroundColor: [
                '#409EFF',
                '#67C23A', 
                '#E6A23C',
                '#F56C6C',
                '#909399'
              ]
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom'
              }
            }
          }
        })
      }

      // График по процессам (столбчатая диаграмма)
      if (processChartRef.value && chartData.value.processChart) {
        const ctx = processChartRef.value.getContext('2d')
        
        if (processChart) {
          processChart.destroy()
        }
        
        processChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: chartData.value.processChart.labels,
            datasets: [{
              data: chartData.value.processChart.data,
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
                beginAtZero: true
              }
            }
          }
        })
      }
    }

    onMounted(async () => {
      await checkSystemHealth()
      await loadMetrics()
    })

    return {
      systemStatus,
      metrics,
      chartData,
      statusChartRef,
      processChartRef
    }
  }
}
</script>

<style scoped>
.dashboard {
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

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.loading-icon {
  font-size: 24px;
  margin-bottom: 10px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 