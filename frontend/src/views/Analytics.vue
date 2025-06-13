<template>
  <div class="analytics">
    <div class="page-header">
      <h2><el-icon><TrendCharts /></el-icon> Аналитика и отчеты</h2>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- Анализ отходов -->
      <el-tab-pane label="Анализ отходов" name="waste">
        <div class="filters" style="margin-bottom: 20px;">
          <el-form inline>
            <el-form-item label="Дата начала:">
              <el-date-picker 
                v-model="wasteFilters.startDate" 
                type="date"
                @change="loadWasteAnalytics"
              />
            </el-form-item>
            
            <el-form-item label="Дата окончания:">
              <el-date-picker 
                v-model="wasteFilters.endDate" 
                type="date"
                @change="loadWasteAnalytics"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="loadWasteAnalytics">
                <el-icon><Refresh /></el-icon>
                Обновить
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- Метрики отходов -->
        <el-row :gutter="20" style="margin-bottom: 30px;" v-if="wasteData">
          <el-col :span="8">
            <el-card shadow="hover">
              <el-statistic
                title="Общие отходы (кг)"
                :value="wasteData.total_waste_kg?.toFixed(2) || '0.00'"
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
                title="Всего инцидентов"
                :value="wasteData.total_incidents || 0"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #E6A23C;"><Warning /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card shadow="hover">
              <el-statistic
                title="Средние отходы на инцидент (кг)"
                :value="getAverageWaste()"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #909399;"><TrendCharts /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <!-- Графики отходов -->
        <el-row :gutter="20" v-if="wasteData">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>Отходы по типам</span>
                </div>
              </template>
              <div style="height: 400px; position: relative;">
                <canvas ref="wasteByTypeChartRef" v-if="wasteByTypeChart"></canvas>
                <div v-else class="chart-loading">
                  <p>Нет данных для отображения</p>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>Отходы по процессам</span>
                </div>
              </template>
              <div style="height: 400px; position: relative;">
                <canvas ref="wasteByProcessChartRef" v-if="wasteByProcessChart"></canvas>
                <div v-else class="chart-loading">
                  <p>Нет данных для отображения</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Загрузка оборудования -->
      <el-tab-pane label="Загрузка оборудования" name="equipment">
        <div class="filters" style="margin-bottom: 20px;">
          <el-form inline>
            <el-form-item label="Дата начала:">
              <el-date-picker 
                v-model="equipmentFilters.startDate" 
                type="date"
                @change="loadEquipmentAnalytics"
              />
            </el-form-item>
            
            <el-form-item label="Дата окончания:">
              <el-date-picker 
                v-model="equipmentFilters.endDate" 
                type="date"
                @change="loadEquipmentAnalytics"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="loadEquipmentAnalytics">
                <el-icon><Refresh /></el-icon>
                Обновить
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- Таблица загрузки оборудования -->
        <el-card shadow="hover" style="margin-bottom: 20px;" v-if="equipmentUtilization.length > 0">
          <template #header>
            <div class="card-header">
              <span>Загрузка оборудования</span>
            </div>
          </template>
          
          <el-table 
            :data="equipmentUtilization" 
            v-loading="loadingEquipment"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="equipment_name" label="Название оборудования" width="200" />
            <el-table-column prop="process_type" label="Тип процесса" width="150" />
            <el-table-column prop="utilization_rate" label="Загрузка (%)" width="120">
              <template #default="scope">
                <el-progress 
                  :percentage="Math.round(scope.row.utilization_rate * 100)" 
                  :color="getUtilizationColor(scope.row.utilization_rate)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="total_working_hours" label="Рабочих часов" width="120" />
            <el-table-column prop="scheduled_orders" label="Запланировано заказов" width="150" />
          </el-table>
        </el-card>

        <!-- График загрузки оборудования -->
        <el-card shadow="hover" v-if="equipmentChart">
          <template #header>
            <div class="card-header">
              <span>Загрузка оборудования (%)</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="equipmentChartRef"></canvas>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Общая статистика -->
      <el-tab-pane label="Общая статистика" name="general">
        <!-- Общие метрики -->
        <el-row :gutter="20" style="margin-bottom: 30px;" v-if="generalStats">
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic
                title="Общее количество заказов"
                :value="generalStats.totalOrders || 0"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #409EFF;"><Document /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic
                title="Выполненные заказы"
                :value="generalStats.completedOrders || 0"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #67C23A;"><Select /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic
                title="Общий объем производства (кг)"
                :value="Math.round(generalStats.totalQuantity || 0)"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #E6A23C;"><ScaleToOriginal /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic
                title="Средний объем заказа (кг)"
                :value="getAverageOrderQuantity()"
                suffix=""
              >
                <template #prefix>
                  <el-icon style="color: #909399;"><TrendCharts /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <!-- Дополнительные графики -->
        <el-row :gutter="20" v-if="generalStats">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>Заказы по типам продуктов</span>
                </div>
              </template>
              <div style="height: 400px; position: relative;">
                <canvas ref="productTypeChartRef" v-if="productTypeChart"></canvas>
                <div v-else class="chart-loading">
                  <p>Нет данных для отображения</p>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>Распределение заказов по приоритетам</span>
                </div>
              </template>
              <div style="height: 400px; position: relative;">
                <canvas ref="priorityChartRef" v-if="priorityChart"></canvas>
                <div v-else class="chart-loading">
                  <p>Нет данных для отображения</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { api } from '../utils/api'
import { Chart, registerables } from 'chart.js'
import { ElMessage } from 'element-plus'

Chart.register(...registerables)

export default {
  name: 'Analytics',
  setup() {
    const activeTab = ref('waste')
    const loadingWaste = ref(false)
    const loadingEquipment = ref(false)
    const loadingGeneral = ref(false)
    
    // Данные
    const wasteData = ref(null)
    const equipmentUtilization = ref([])
    const generalStats = ref(null)
    
    // Фильтры
    const wasteFilters = reactive({
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      endDate: new Date()
    })
    
    const equipmentFilters = reactive({
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      endDate: new Date()
    })
    
    // Графики
    const wasteByTypeChart = ref(null)
    const wasteByProcessChart = ref(null)
    const equipmentChart = ref(null)
    const productTypeChart = ref(null)
    const priorityChart = ref(null)
    
    // Ссылки на canvas
    const wasteByTypeChartRef = ref(null)
    const wasteByProcessChartRef = ref(null)
    const equipmentChartRef = ref(null)
    const productTypeChartRef = ref(null)
    const priorityChartRef = ref(null)
    
    // Инстансы графиков
    let wasteTypeChart = null
    let wasteProcessChart = null
    let equipmentUtilChart = null
    let productChart = null
    let priorityChartInstance = null

    // Загрузка аналитики отходов
    const loadWasteAnalytics = async () => {
      loadingWaste.value = true
      try {
        const params = {
          start_date: wasteFilters.startDate.toISOString().split('T')[0],
          end_date: wasteFilters.endDate.toISOString().split('T')[0]
        }
        
        wasteData.value = await api.get('/analytics/waste-summary', params)
        await prepareWasteCharts()
      } catch (error) {
        ElMessage.error('Ошибка загрузки аналитики отходов')
      } finally {
        loadingWaste.value = false
      }
    }

    // Загрузка аналитики оборудования
    const loadEquipmentAnalytics = async () => {
      loadingEquipment.value = true
      try {
        const params = {
          start_date: equipmentFilters.startDate.toISOString().split('T')[0],
          end_date: equipmentFilters.endDate.toISOString().split('T')[0]
        }
        
        const data = await api.get('/analytics/equipment-utilization', params)
        
        equipmentUtilization.value = Object.values(data).map(item => ({
          ...item,
          utilization_rate: item.utilization_rate || 0
        }))
        
        await prepareEquipmentChart()
      } catch (error) {
        ElMessage.error('Ошибка загрузки аналитики оборудования')
      } finally {
        loadingEquipment.value = false
      }
    }

    // Загрузка общей статистики
    const loadGeneralStats = async () => {
      loadingGeneral.value = true
      try {
        const ordersData = await api.get('/orders/', { limit: 500 })
        
        const completedOrders = ordersData.filter(o => o.status === 'completed').length
        const totalQuantity = ordersData.reduce((sum, o) => sum + parseFloat(o.quantity_kg || 0), 0)
        
        generalStats.value = {
          totalOrders: ordersData.length,
          completedOrders,
          totalQuantity,
          ordersData
        }
        
        await prepareGeneralCharts(ordersData)
      } catch (error) {
        ElMessage.error('Ошибка загрузки общей статистики')
      } finally {
        loadingGeneral.value = false
      }
    }

    // Подготовка графиков отходов
    const prepareWasteCharts = async () => {
      if (!wasteData.value) return
      
      // График по типам
      if (wasteData.value.waste_by_type && Object.keys(wasteData.value.waste_by_type).length > 0) {
        wasteByTypeChart.value = {
          labels: Object.keys(wasteData.value.waste_by_type),
          data: Object.values(wasteData.value.waste_by_type)
        }
      }
      
      // График по процессам
      if (wasteData.value.waste_by_process && Object.keys(wasteData.value.waste_by_process).length > 0) {
        wasteByProcessChart.value = {
          labels: Object.keys(wasteData.value.waste_by_process),
          data: Object.values(wasteData.value.waste_by_process)
        }
      }
      
      await nextTick()
      createWasteCharts()
    }

    // Подготовка графика оборудования
    const prepareEquipmentChart = async () => {
      if (equipmentUtilization.value.length === 0) return
      
      equipmentChart.value = {
        labels: equipmentUtilization.value.map(eq => eq.equipment_name),
        data: equipmentUtilization.value.map(eq => (eq.utilization_rate * 100).toFixed(1))
      }
      
      await nextTick()
      createEquipmentChart()
    }

    // Подготовка общих графиков
    const prepareGeneralCharts = async (ordersData) => {
      // График по типам продуктов
      const productCounts = {}
      ordersData.forEach(order => {
        const product = order.product_type
        productCounts[product] = (productCounts[product] || 0) + 1
      })
      
      if (Object.keys(productCounts).length > 0) {
        productTypeChart.value = {
          labels: Object.keys(productCounts),
          data: Object.values(productCounts)
        }
      }
      
      // График по приоритетам
      const priorityCounts = {}
      ordersData.forEach(order => {
        const priority = `Приоритет ${order.priority}`
        priorityCounts[priority] = (priorityCounts[priority] || 0) + 1
      })
      
      if (Object.keys(priorityCounts).length > 0) {
        priorityChart.value = {
          labels: Object.keys(priorityCounts),
          data: Object.values(priorityCounts)
        }
      }
      
      await nextTick()
      createGeneralCharts()
    }

    // Создание графиков отходов
    const createWasteCharts = () => {
      // График отходов по типам
      if (wasteByTypeChartRef.value && wasteByTypeChart.value) {
        const ctx = wasteByTypeChartRef.value.getContext('2d')
        
        if (wasteTypeChart) wasteTypeChart.destroy()
        
        wasteTypeChart = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: wasteByTypeChart.value.labels,
            datasets: [{
              data: wasteByTypeChart.value.data,
              backgroundColor: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
          }
        })
      }
      
      // График отходов по процессам
      if (wasteByProcessChartRef.value && wasteByProcessChart.value) {
        const ctx = wasteByProcessChartRef.value.getContext('2d')
        
        if (wasteProcessChart) wasteProcessChart.destroy()
        
        wasteProcessChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: wasteByProcessChart.value.labels,
            datasets: [{
              label: 'Отходы (кг)',
              data: wasteByProcessChart.value.data,
              backgroundColor: '#F56C6C'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
          }
        })
      }
    }

    // Создание графика оборудования
    const createEquipmentChart = () => {
      if (equipmentChartRef.value && equipmentChart.value) {
        const ctx = equipmentChartRef.value.getContext('2d')
        
        if (equipmentUtilChart) equipmentUtilChart.destroy()
        
        equipmentUtilChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: equipmentChart.value.labels,
            datasets: [{
              label: 'Загрузка (%)',
              data: equipmentChart.value.data,
              backgroundColor: '#409EFF'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { 
              y: { 
                beginAtZero: true, 
                max: 100,
                ticks: { callback: value => value + '%' }
              } 
            }
          }
        })
      }
    }

    // Создание общих графиков
    const createGeneralCharts = () => {
      // График по типам продуктов
      if (productTypeChartRef.value && productTypeChart.value) {
        const ctx = productTypeChartRef.value.getContext('2d')
        
        if (productChart) productChart.destroy()
        
        productChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: productTypeChart.value.labels,
            datasets: [{
              label: 'Количество заказов',
              data: productTypeChart.value.data,
              backgroundColor: '#67C23A'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
          }
        })
      }
      
      // График по приоритетам
      if (priorityChartRef.value && priorityChart.value) {
        const ctx = priorityChartRef.value.getContext('2d')
        
        if (priorityChartInstance) priorityChartInstance.destroy()
        
        priorityChartInstance = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: priorityChart.value.labels,
            datasets: [{
              data: priorityChart.value.data,
              backgroundColor: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
          }
        })
      }
    }

    // Утилитарные функции
    const getAverageWaste = () => {
      if (!wasteData.value || !wasteData.value.total_incidents) return '0.00'
      return (wasteData.value.total_waste_kg / wasteData.value.total_incidents).toFixed(2)
    }

    const getAverageOrderQuantity = () => {
      if (!generalStats.value || !generalStats.value.totalOrders) return '0.0'
      return (generalStats.value.totalQuantity / generalStats.value.totalOrders).toFixed(1)
    }

    const getUtilizationColor = (rate) => {
      if (rate >= 0.8) return '#67C23A'
      if (rate >= 0.6) return '#E6A23C'
      return '#F56C6C'
    }

    onMounted(() => {
      loadWasteAnalytics()
      loadEquipmentAnalytics()
      loadGeneralStats()
    })

    return {
      activeTab,
      loadingWaste,
      loadingEquipment,
      wasteData,
      equipmentUtilization,
      generalStats,
      wasteFilters,
      equipmentFilters,
      wasteByTypeChart,
      wasteByProcessChart,
      equipmentChart,
      productTypeChart,
      priorityChart,
      wasteByTypeChartRef,
      wasteByProcessChartRef,
      equipmentChartRef,
      productTypeChartRef,
      priorityChartRef,
      loadWasteAnalytics,
      loadEquipmentAnalytics,
      getAverageWaste,
      getAverageOrderQuantity,
      getUtilizationColor
    }
  }
}
</script>

<style scoped>
.analytics {
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

.filters {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}
</style> 