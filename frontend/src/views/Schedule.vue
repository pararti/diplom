<template>
  <div class="schedule">
    <div class="page-header">
      <h2><el-icon><Calendar /></el-icon> Текущее расписание</h2>
    </div>

    <!-- Фильтры -->
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>Фильтры</span>
        </div>
      </template>
      
      <el-form :model="filters" inline>
        <el-form-item label="Дата начала:">
          <el-date-picker 
            v-model="filters.startDate" 
            type="date"
            @change="loadSchedule"
          />
        </el-form-item>
        
        <el-form-item label="Дата окончания:">
          <el-date-picker 
            v-model="filters.endDate" 
            type="date"
            @change="loadSchedule"
          />
        </el-form-item>
        
        <el-form-item label="Оборудование:">
          <el-select 
            v-model="filters.equipmentId" 
            placeholder="Все оборудование"
            clearable
            @change="loadSchedule"
            style="width: 250px;"
          >
            <el-option 
              v-for="equipment in equipmentOptions" 
              :key="equipment.id"
              :label="equipment.name"
              :value="equipment.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadSchedule">
            <el-icon><Refresh /></el-icon>
            Обновить
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Таблица расписания -->
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>Расписание производства</span>
        </div>
      </template>
      
      <el-table 
        :data="scheduleData" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="order_number" label="Номер заказа" width="150" />
        <el-table-column prop="equipment_name" label="Оборудование" width="200" />
        <el-table-column prop="product_type" label="Тип продукта" width="120" />
        <el-table-column prop="process_type" label="Тип процесса" width="140" />
        <el-table-column prop="scheduled_start" label="Начало" width="160">
          <template #default="scope">
            {{ formatDateTime(scope.row.scheduled_start) }}
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_end" label="Окончание" width="160">
          <template #default="scope">
            {{ formatDateTime(scope.row.scheduled_end) }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity_kg" label="Количество (кг)" width="120" />
        <el-table-column prop="setup_time_minutes" label="Наладка (мин)" width="120" />
        <el-table-column prop="processing_time_minutes" label="Обработка (мин)" width="140" />
      </el-table>
    </el-card>

    <!-- Диаграмма Ганта -->
    <el-card shadow="hover" v-if="scheduleData.length > 0">
      <template #header>
        <div class="card-header">
          <span>Диаграмма Ганта</span>
        </div>
      </template>
      
      <div class="gantt-container">
        <div class="gantt-header">
          <div class="gantt-equipment-column">Оборудование</div>
          <div class="gantt-timeline">
            <div class="gantt-days">
              <div 
                v-for="day in ganttDays" 
                :key="day.date"
                class="gantt-day"
                :style="{ width: dayWidth + 'px' }"
              >
                {{ day.label }}
              </div>
            </div>
            <div class="gantt-hours">
              <div 
                v-for="hour in ganttHours" 
                :key="hour"
                class="gantt-hour"
                :style="{ width: hourWidth + 'px' }"
              >
                {{ hour }}:00
              </div>
            </div>
          </div>
        </div>
        
        <div class="gantt-content">
          <div 
            v-for="equipment in equipmentRows" 
            :key="equipment.id"
            class="gantt-row"
          >
            <div class="gantt-equipment-label">
              {{ equipment.name }}
            </div>
            <div class="gantt-timeline-row">
              <div 
                v-for="task in equipment.tasks" 
                :key="task.id"
                class="gantt-task"
                :style="getTaskStyle(task)"
                :title="getTaskTooltip(task)"
              >
                <div class="gantt-task-content">
                  {{ task.order_number }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '../utils/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'Schedule',
  setup() {
    const loading = ref(false)
    const scheduleData = ref([])
    const equipmentOptions = ref([])
    
    const filters = reactive({
      startDate: new Date(),
      endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // +7 дней
      equipmentId: null
    })

    // Параметры диаграммы Ганта
    const hourWidth = 40
    const dayWidth = hourWidth * 24
    const rowHeight = 50

    // Загрузка расписания
    const loadSchedule = async () => {
      loading.value = true
      try {
        const params = {
          start_date: filters.startDate.toISOString().split('T')[0],
          end_date: filters.endDate.toISOString().split('T')[0]
        }
        
        if (filters.equipmentId) {
          params.equipment_id = filters.equipmentId
        }

        scheduleData.value = await api.get('/schedule/', params)
      } catch (error) {
        ElMessage.error('Ошибка загрузки расписания')
      } finally {
        loading.value = false
      }
    }

    // Загрузка оборудования для фильтра
    const loadEquipment = async () => {
      try {
        equipmentOptions.value = await api.get('/equipment/')
      } catch (error) {
        ElMessage.error('Ошибка загрузки оборудования')
      }
    }

    // Дни для заголовка диаграммы Ганта
    const ganttDays = computed(() => {
      const days = []
      const start = new Date(filters.startDate)
      const end = new Date(filters.endDate)
      
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        days.push({
          date: d.toISOString().split('T')[0],
          label: d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
        })
      }
      
      return days
    })

    // Часы для заголовка диаграммы Ганта
    const ganttHours = computed(() => {
      const hours = []
      for (let h = 0; h < 24; h++) {
        hours.push(h.toString().padStart(2, '0'))
      }
      return hours
    })

    // Строки оборудования для диаграммы Ганта
    const equipmentRows = computed(() => {
      const equipmentMap = new Map()
      
      // Инициализация всех единиц оборудования
      equipmentOptions.value.forEach(eq => {
        equipmentMap.set(eq.id, {
          id: eq.id,
          name: eq.name,
          tasks: []
        })
      })
      
      // Добавление задач к оборудованию
      scheduleData.value.forEach(schedule => {
        const equipmentId = schedule.equipment_id
        if (equipmentMap.has(equipmentId)) {
          equipmentMap.get(equipmentId).tasks.push({
            id: schedule.id,
            order_number: schedule.order_number,
            start: new Date(schedule.scheduled_start),
            end: new Date(schedule.scheduled_end),
            product_type: schedule.product_type,
            process_type: schedule.process_type
          })
        }
      })
      
      return Array.from(equipmentMap.values()).filter(eq => 
        !filters.equipmentId || eq.id === filters.equipmentId
      )
    })

    // Стиль для задачи в диаграмме Ганта
    const getTaskStyle = (task) => {
      const startTime = task.start.getTime()
      const endTime = task.end.getTime()
      const periodStart = filters.startDate.getTime()
      const periodEnd = filters.endDate.getTime()
      
      // Позиция и ширина в пикселях
      const left = Math.max(0, (startTime - periodStart) / (1000 * 60 * 60) * hourWidth)
      const width = Math.max(10, (endTime - startTime) / (1000 * 60 * 60) * hourWidth)
      
      // Цвет в зависимости от типа процесса
      const colors = {
        extrusion: '#409EFF',
        ringing: '#67C23A',
        corrugation_soft: '#E6A23C',
        corrugation_hard: '#F56C6C'
      }
      
      return {
        left: left + 'px',
        width: width + 'px',
        backgroundColor: colors[task.process_type] || '#909399',
        height: (rowHeight - 10) + 'px',
        lineHeight: (rowHeight - 10) + 'px'
      }
    }

    // Подсказка для задачи
    const getTaskTooltip = (task) => {
      return `${task.order_number}\n${task.product_type} - ${task.process_type}\n${formatDateTime(task.start)} - ${formatDateTime(task.end)}`
    }

    // Форматирование даты и времени
    const formatDateTime = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    onMounted(() => {
      loadEquipment()
      loadSchedule()
    })

    return {
      loading,
      scheduleData,
      equipmentOptions,
      filters,
      ganttDays,
      ganttHours,
      equipmentRows,
      dayWidth,
      hourWidth,
      loadSchedule,
      getTaskStyle,
      getTaskTooltip,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.schedule {
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

/* Диаграмма Ганта */
.gantt-container {
  overflow-x: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.gantt-header {
  display: flex;
  background: #f5f7fa;
  border-bottom: 2px solid #dcdfe6;
  position: sticky;
  top: 0;
  z-index: 10;
}

.gantt-equipment-column {
  width: 200px;
  min-width: 200px;
  padding: 10px;
  font-weight: 600;
  border-right: 1px solid #dcdfe6;
  background: #f5f7fa;
}

.gantt-timeline {
  flex: 1;
  min-width: 0;
}

.gantt-days {
  display: flex;
  border-bottom: 1px solid #dcdfe6;
}

.gantt-day {
  border-right: 1px solid #dcdfe6;
  padding: 5px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
}

.gantt-hours {
  display: flex;
}

.gantt-hour {
  border-right: 1px solid #e4e7ed;
  padding: 2px;
  text-align: center;
  font-size: 10px;
  color: #909399;
}

.gantt-content {
  background: white;
}

.gantt-row {
  display: flex;
  border-bottom: 1px solid #e4e7ed;
  min-height: 50px;
}

.gantt-equipment-label {
  width: 200px;
  min-width: 200px;
  padding: 15px 10px;
  border-right: 1px solid #dcdfe6;
  background: #fafafa;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.gantt-timeline-row {
  flex: 1;
  position: relative;
  min-height: 50px;
}

.gantt-task {
  position: absolute;
  top: 5px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

.gantt-task:hover {
  opacity: 0.8;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.gantt-task-content {
  padding: 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 