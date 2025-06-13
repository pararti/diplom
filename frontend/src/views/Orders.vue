<template>
  <div class="orders">
    <div class="page-header">
      <h2><el-icon><Document /></el-icon> Управление заказами</h2>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- Список заказов -->
      <el-tab-pane label="Список заказов" name="list">
        <!-- Панель фильтров и поиска -->
        <el-card class="filter-card" shadow="never">
          <el-row :gutter="20" align="middle">
            <el-col :span="6">
              <el-input
                v-model="searchQuery"
                placeholder="Поиск по номеру заказа..."
                @input="handleSearch"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filters.status" placeholder="Статус" @change="loadOrders" clearable>
                <el-option label="Запланированные" value="planned" />
                <el-option label="В процессе" value="in_progress" />
                <el-option label="Завершенные" value="completed" />
                <el-option label="Отмененные" value="cancelled" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filters.processType" placeholder="Процесс" @change="loadOrders" clearable>
                <el-option label="Экструзия" value="extrusion" />
                <el-option label="Кольцевание" value="ringing" />
                <el-option label="Гофрирование мягкое" value="corrugation_soft" />
                <el-option label="Гофрирование жесткое" value="corrugation_hard" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filters.productType" placeholder="Продукт" @change="loadOrders" clearable>
                <el-option label="Оболочка" value="shell" />
                <el-option label="Пленка" value="film" />
                <el-option label="Этикетка" value="label" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-button-group>
                <el-button type="primary" @click="exportOrders">
                  <el-icon><Download /></el-icon> Экспорт CSV
                </el-button>
                <el-button type="success" @click="showImportDialog = true">
                  <el-icon><Upload /></el-icon> Импорт CSV
                </el-button>
              </el-button-group>
            </el-col>
          </el-row>
        </el-card>

        <!-- Таблица заказов -->
        <el-card class="table-card" shadow="never">
          <el-table 
            :data="displayOrders" 
            v-loading="loading"
            stripe
            border
            style="width: 100%"
            :default-sort="{ prop: 'order_date', order: 'descending' }"
            height="600"
          >
            <el-table-column prop="order_number" label="Номер заказа" width="140" fixed="left" sortable />
            <el-table-column prop="product_type" label="Тип продукта" width="120" sortable>
              <template #default="scope">
                <el-tag size="small" :type="getProductTypeColor(scope.row.product_type)">
                  {{ getProductTypeText(scope.row.product_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="process_type" label="Тип процесса" width="140" sortable>
              <template #default="scope">
                <el-tag size="small" :type="getProcessTypeColor(scope.row.process_type)">
                  {{ getProcessTypeText(scope.row.process_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quantity_kg" label="Количество (кг)" width="130" sortable align="right">
              <template #default="scope">
                <strong>{{ Number(scope.row.quantity_kg).toLocaleString() }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="Статус" width="120" sortable>
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)" size="small">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="Приоритет" width="100" sortable align="center">
              <template #default="scope">
                <el-tag size="small" :type="getPriorityColor(scope.row.priority)">
                  {{ scope.row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="Дата заказа" width="120" sortable />
            <el-table-column prop="delivery_date" label="Дата поставки" width="120" sortable />
            <el-table-column prop="color" label="Цвет" width="100">
              <template #default="scope">
                <span v-if="scope.row.color">{{ scope.row.color }}</span>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="caliber" label="Калибр" width="100">
              <template #default="scope">
                <span v-if="scope.row.caliber">{{ scope.row.caliber }}</span>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="Действия" width="200" fixed="right">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editOrder(scope.row)"
                  :icon="Edit"
                >
                  Изменить
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteOrder(scope.row)"
                  :icon="Delete"
                >
                  Удалить
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Создать заказ -->
      <el-tab-pane label="Создать заказ" name="create">
        <el-card shadow="never">
          <el-form 
            :model="newOrder" 
            :rules="orderRules" 
            ref="newOrderForm"
            label-width="180px"
            style="max-width: 1000px;"
          >
            <el-row :gutter="30">
              <el-col :span="12">
                <h3>Основная информация</h3>
                <el-form-item label="Номер заказа" prop="order_number">
                  <el-input v-model="newOrder.order_number" placeholder="ORD-2024-00001" />
                </el-form-item>
                
                <el-form-item label="Тип продукта" prop="product_type">
                  <el-select v-model="newOrder.product_type" style="width: 100%">
                    <el-option label="Оболочка" value="shell" />
                    <el-option label="Пленка" value="film" />
                    <el-option label="Этикетка" value="label" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="Тип процесса" prop="process_type">
                  <el-select v-model="newOrder.process_type" style="width: 100%">
                    <el-option label="Экструзия" value="extrusion" />
                    <el-option label="Кольцевание" value="ringing" />
                    <el-option label="Гофрирование мягкое" value="corrugation_soft" />
                    <el-option label="Гофрирование жесткое" value="corrugation_hard" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="Материал" prop="material_id">
                  <el-select v-model="newOrder.material_id" style="width: 100%" filterable>
                    <el-option 
                      v-for="material in materials" 
                      :key="material.id"
                      :label="`${material.name} (${material.type})`"
                      :value="material.id" 
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="Количество (кг)" prop="quantity_kg">
                  <el-input-number 
                    v-model="newOrder.quantity_kg" 
                    :min="0.1" 
                    :step="0.1"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <h3>Дополнительные параметры</h3>
                <el-form-item label="Ширина (мм)">
                  <el-input-number 
                    v-model="newOrder.width_mm" 
                    :min="0" 
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="Толщина (мм)">
                  <el-input-number 
                    v-model="newOrder.thickness_mm" 
                    :min="0" 
                    :step="0.01"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="Цвет">
                  <el-input v-model="newOrder.color" placeholder="прозрачный" />
                </el-form-item>
                
                <el-form-item label="Калибр">
                  <el-input v-model="newOrder.caliber" placeholder="D300" />
                </el-form-item>
                
                <el-form-item label="Дата заказа" prop="order_date">
                  <el-date-picker 
                    v-model="newOrder.order_date" 
                    type="date"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="Дата поставки" prop="delivery_date">
                  <el-date-picker 
                    v-model="newOrder.delivery_date" 
                    type="date"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="Приоритет" prop="priority">
                  <div class="priority-slider">
                    <el-slider 
                      v-model="newOrder.priority" 
                      :min="1" 
                      :max="5" 
                      show-stops
                      :marks="{ 1: '1', 2: '2', 3: '3', 4: '4', 5: '5' }"
                      style="width: 300px; margin-bottom: 20px;"
                    />
                    <div class="priority-value">Значение: {{ newOrder.priority }}</div>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-divider />
            
            <el-form-item>
              <el-button type="primary" @click="createOrder" :loading="creating" size="large">
                <el-icon><Plus /></el-icon> Создать заказ
              </el-button>
              <el-button @click="resetForm" size="large">Очистить</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

        <!-- Редактировать заказ -->
      <el-tab-pane label="Изменить заказ" name="edit" v-if="editingOrder">
        <el-card shadow="never">
          <el-form 
            :model="editingOrder" 
            ref="editOrderForm"
            label-width="180px"
            style="max-width: 600px;"
          >
            <el-form-item label="Номер заказа">
              <el-input :value="editingOrder.order_number" disabled />
            </el-form-item>
            
            <el-form-item label="Статус">
              <el-select v-model="editingOrder.status" style="width: 100%">
                <el-option label="Запланированный" value="planned" />
                <el-option label="В процессе" value="in_progress" />
                <el-option label="Завершенный" value="completed" />
                <el-option label="Отмененный" value="cancelled" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="Приоритет">
              <div class="priority-slider">
                <el-slider 
                  v-model="editingOrder.priority" 
                  :min="1" 
                  :max="5" 
                  show-stops
                  :marks="{ 1: '1', 2: '2', 3: '3', 4: '4', 5: '5' }"
                  style="width: 300px; margin-bottom: 20px;"
                />
                <div class="priority-value">Значение: {{ editingOrder.priority }}</div>
              </div>
            </el-form-item>
            
            <el-form-item label="Планируемое начало">
              <el-date-picker 
                v-model="editingOrder.planned_start" 
                type="datetime"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="updateOrder" :loading="updating">
                Обновить заказ
              </el-button>
              <el-button @click="cancelEdit">Отмена</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Диалог импорта CSV -->
    <el-dialog 
      v-model="showImportDialog" 
      title="Импорт заказов из CSV" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-section">
        <el-alert
          title="Формат CSV файла"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <p>CSV файл должен содержать следующие колонки:</p>
          <code>order_number,product_type,process_type,material_id,quantity_kg,color,caliber,width_mm,thickness_mm,order_date,delivery_date,priority</code>
        </el-alert>
        
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :show-file-list="false"
          accept=".csv"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            Перетащите CSV файл сюда или <em>нажмите для выбора</em>
          </div>
        </el-upload>
        
        <div v-if="csvFile" style="margin-top: 15px;">
          <el-tag type="success">{{ csvFile.name }}</el-tag>
          <el-button type="text" @click="csvFile = null" style="margin-left: 10px;">Удалить</el-button>
        </div>
        
        <div v-if="importPreview.length > 0" style="margin-top: 20px;">
          <h4>Предварительный просмотр (первые 5 строк):</h4>
          <el-table :data="importPreview.slice(0, 5)" size="small" border>
            <el-table-column prop="order_number" label="Номер" width="120" />
            <el-table-column prop="product_type" label="Продукт" width="100" />
            <el-table-column prop="process_type" label="Процесс" width="120" />
            <el-table-column prop="quantity_kg" label="Кол-во" width="80" />
          </el-table>
          <p style="margin-top: 10px; color: #666;">
            Всего строк для импорта: {{ importPreview.length }}
          </p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showImportDialog = false">Отмена</el-button>
        <el-button 
          type="primary" 
          @click="importOrders" 
          :loading="importing"
          :disabled="!csvFile"
        >
          Импортировать
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { api } from '../utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, 
  Search, 
  Download, 
  Upload, 
  Edit, 
  Plus,
  UploadFilled,
  Delete
} from '@element-plus/icons-vue'

export default {
  name: 'Orders',
  components: {
    Document,
    Search,
    Download,
    Upload,
    Edit,
    Plus,
    UploadFilled,
    Delete
  },
  setup() {
    const activeTab = ref('list')
    const loading = ref(false)
    const creating = ref(false)
    const updating = ref(false)
    const importing = ref(false)
    
    const orders = ref([])
    const materials = ref([])
    const editingOrder = ref(null)
    const searchQuery = ref('')
    const searchResults = ref([])
    const showImportDialog = ref(false)
    const csvFile = ref(null)
    const importPreview = ref([])
    
    const filters = reactive({
      status: '',
      processType: '',
      productType: ''
    })
    
    const newOrder = reactive({
      order_number: '',
      product_type: '',
      process_type: '',
      material_id: null,
      quantity_kg: 100,
      width_mm: null,
      thickness_mm: null,
      color: '',
      caliber: '',
      order_date: new Date(),
      delivery_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      priority: 1
    })
    
    const orderRules = {
      order_number: [
        { required: true, message: 'Номер заказа обязателен', trigger: 'blur' }
      ],
      product_type: [
        { required: true, message: 'Выберите тип продукта', trigger: 'change' }
      ],
      process_type: [
        { required: true, message: 'Выберите тип процесса', trigger: 'change' }
      ],
      material_id: [
        { required: true, message: 'Выберите материал', trigger: 'change' }
      ],
      quantity_kg: [
        { required: true, message: 'Укажите количество', trigger: 'blur' }
      ]
    }

    // Вычисляемое свойство для отображаемых заказов
    const displayOrders = computed(() => {
      return searchQuery.value ? searchResults.value : orders.value
    })

    // Загрузка заказов
    const loadOrders = async () => {
      loading.value = true
      try {
        const params = { limit: 500 }
        if (filters.status) params.status = filters.status
        if (filters.processType) params.process_type = filters.processType
        if (filters.productType) params.product_type = filters.productType
        
        orders.value = await api.get('/orders/', params)
      } catch (error) {
        ElMessage.error('Ошибка загрузки заказов')
      } finally {
        loading.value = false
      }
    }

    // Поиск заказов
    const handleSearch = async () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }
      
      try {
        searchResults.value = await api.get('/orders/search', { q: searchQuery.value })
      } catch (error) {
        ElMessage.error('Ошибка поиска заказов')
      }
    }

    // Загрузка материалов
    const loadMaterials = async () => {
      try {
        materials.value = await api.get('/materials/')
      } catch (error) {
        ElMessage.error('Ошибка загрузки материалов')
      }
    }

    // Создание заказа
    const createOrder = async () => {
      creating.value = true
      try {
        const orderData = {
          ...newOrder,
          order_date: newOrder.order_date.toISOString().split('T')[0],
          delivery_date: newOrder.delivery_date.toISOString().split('T')[0],
          width_mm: newOrder.width_mm || null,
          thickness_mm: newOrder.thickness_mm || null,
          color: newOrder.color || null,
          caliber: newOrder.caliber || null
        }
        
        await api.post('/orders/', orderData)
        ElMessage.success('Заказ успешно создан!')
        resetForm()
        loadOrders()
        activeTab.value = 'list'
      } catch (error) {
        ElMessage.error('Ошибка при создании заказа')
      } finally {
        creating.value = false
      }
    }

    // Редактирование заказа
    const editOrder = (order) => {
      editingOrder.value = { ...order }
      if (editingOrder.value.planned_start) {
        editingOrder.value.planned_start = new Date(editingOrder.value.planned_start)
      }
      activeTab.value = 'edit'
    }

    // Обновление заказа
    const updateOrder = async () => {
      updating.value = true
      try {
        const updateData = {
          status: editingOrder.value.status,
          priority: editingOrder.value.priority
        }
        
        if (editingOrder.value.planned_start) {
          updateData.planned_start = editingOrder.value.planned_start.toISOString()
        }
        
        await api.put(`/orders/${editingOrder.value.id}`, updateData)
        ElMessage.success('Заказ успешно обновлен!')
        loadOrders()
        cancelEdit()
      } catch (error) {
        ElMessage.error('Ошибка при обновлении заказа')
      } finally {
        updating.value = false
      }
    }

    // Отмена редактирования
    const cancelEdit = () => {
      editingOrder.value = null
      activeTab.value = 'list'
    }

    // Сброс формы
    const resetForm = () => {
      Object.assign(newOrder, {
        order_number: '',
        product_type: '',
        process_type: '',
        material_id: null,
        quantity_kg: 100,
        width_mm: null,
        thickness_mm: null,
        color: '',
        caliber: '',
        order_date: new Date(),
        delivery_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        priority: 1
      })
    }

    // Экспорт заказов
    const exportOrders = () => {
      const csv = [
        'order_number,product_type,process_type,material_id,quantity_kg,color,caliber,width_mm,thickness_mm,order_date,delivery_date,priority,status',
        ...orders.value.map(order => 
          `${order.order_number},${order.product_type},${order.process_type},${order.material_id},${order.quantity_kg},${order.color || ''},${order.caliber || ''},${order.width_mm || ''},${order.thickness_mm || ''},${order.order_date},${order.delivery_date},${order.priority},${order.status}`
        )
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `orders_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    }

    // Обработка выбора файла для импорта
    const handleFileChange = (file) => {
      csvFile.value = file.raw
      parseCSV(file.raw)
    }

    // Парсинг CSV файла
    const parseCSV = (file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target.result
        const lines = text.split('\n').filter(line => line.trim())
        const headers = lines[0].split(',').map(h => h.trim())
        
        const data = []
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',').map(v => v.trim())
          if (values.length === headers.length) {
            const row = {}
            headers.forEach((header, index) => {
              row[header] = values[index] || null
            })
            data.push(row)
          }
        }
        
        importPreview.value = data
      }
      reader.readAsText(file)
    }

    // Импорт заказов
    const importOrders = async () => {
      importing.value = true
      try {
        const result = await api.post('/orders/bulk-import', importPreview.value)
        
        if (result.created_count > 0) {
          ElMessage.success(`Успешно импортировано ${result.created_count} заказов`)
        }
        
        if (result.error_count > 0) {
          ElMessageBox.alert(
            result.errors.join('\n'),
            `Ошибки импорта (${result.error_count})`,
            { type: 'warning' }
          )
        }
        
        showImportDialog.value = false
        csvFile.value = null
        importPreview.value = []
        loadOrders()
      } catch (error) {
        ElMessage.error('Ошибка при импорте заказов')
      } finally {
        importing.value = false
      }
    }

    // Утилиты для отображения
    const getStatusType = (status) => {
      const types = {
        planned: 'info',
        in_progress: 'warning',
        completed: 'success',
        cancelled: 'danger'
      }
      return types[status] || 'info'
    }

    const getStatusText = (status) => {
      const texts = {
        planned: 'Запланированный',
        in_progress: 'В процессе',
        completed: 'Завершенный',
        cancelled: 'Отмененный'
      }
      return texts[status] || status
    }

    const getProductTypeColor = (type) => {
      const colors = {
        shell: 'primary',
        film: 'success',
        label: 'warning'
      }
      return colors[type] || 'info'
    }

    const getProductTypeText = (type) => {
      const texts = {
        shell: 'Оболочка',
        film: 'Пленка',
        label: 'Этикетка'
      }
      return texts[type] || type
    }

    const getProcessTypeColor = (type) => {
      const colors = {
        extrusion: 'primary',
        ringing: 'success',
        corrugation_soft: 'warning',
        corrugation_hard: 'danger'
      }
      return colors[type] || 'info'
    }

    const getProcessTypeText = (type) => {
      const texts = {
        extrusion: 'Экструзия',
        ringing: 'Кольцевание',
        corrugation_soft: 'Гофрирование мягкое',
        corrugation_hard: 'Гофрирование жесткое'
      }
      return texts[type] || type
    }

    const getPriorityColor = (priority) => {
      const colors = {
        1: 'primary',
        2: 'info',
        3: 'success',
        4: 'warning',
        5: 'danger'
      }
      return colors[priority] || 'info'
    }

    const deleteOrder = async (order) => {
      try {
        await ElMessageBox.confirm(
          `Вы уверены, что хотите удалить заказ "${order.order_number}"?`,
          'Подтверждение удаления',
          {
            confirmButtonText: 'Удалить',
            cancelButtonText: 'Отмена',
            type: 'warning',
          }
        )
        
        await api.delete(`/orders/${order.id}`)
        ElMessage.success('Заказ успешно удален!')
        loadOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Ошибка при удалении заказа')
        }
      }
    }

    onMounted(() => {
      loadOrders()
      loadMaterials()
    })

    return {
      activeTab,
      loading,
      creating,
      updating,
      importing,
      orders,
      materials,
      editingOrder,
      searchQuery,
      searchResults,
      showImportDialog,
      csvFile,
      importPreview,
      filters,
      newOrder,
      orderRules,
      displayOrders,
      loadOrders,
      handleSearch,
      createOrder,
      editOrder,
      updateOrder,
      cancelEdit,
      resetForm,
      exportOrders,
      handleFileChange,
      importOrders,
      getStatusType,
      getStatusText,
      getProductTypeColor,
      getProductTypeText,
      getProcessTypeColor,
      getProcessTypeText,
      getPriorityColor,
      deleteOrder
    }
  }
}
</script>

<style scoped>
.orders {
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

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  border: none;
}

.text-muted {
  color: #909399;
}

.import-section {
  padding: 10px 0;
}

.import-section code {
  background: #f5f7fa;
  padding: 5px;
  border-radius: 3px;
  font-size: 12px;
  word-break: break-all;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.el-rate) {
  height: auto;
}

.priority-slider {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.priority-value {
  font-weight: 500;
  color: #409eff;
  margin-top: 5px;
}

:deep(.el-slider) {
  margin: 10px 0;
}

:deep(.el-slider__input) {
  width: 50px !important;
}

:deep(.el-table .el-slider) {
  margin: 5px 0;
}

:deep(.el-upload-dragger) {
  width: 100%;
}

h3 {
  color: #409eff;
  margin-bottom: 20px;
  font-size: 16px;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 10px;
}
</style> 