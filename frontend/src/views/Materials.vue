<template>
  <div class="materials">
    <div class="page-header">
      <h2><el-icon><Box /></el-icon> Материалы и оборудование</h2>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- Материалы -->
      <el-tab-pane label="Материалы" name="materials">
        <!-- Панель управления материалами -->
        <el-card class="control-card" shadow="never">
          <el-row :gutter="20" align="middle">
            <el-col :span="6">
              <el-input
                v-model="materialsSearch"
                placeholder="Поиск материалов..."
                @input="filterMaterials"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="4">
              <el-select v-model="materialTypeFilter" placeholder="Тип материала" @change="filterMaterials" clearable>
                <el-option 
                  v-for="type in types" 
                  :key="type.name"
                  :label="type.name"
                  :value="type.name" 
                />
              </el-select>
            </el-col>
            <el-col :span="14">
              <el-button-group>
                <el-button type="primary" @click="showCreateMaterialDialog = true">
                  <el-icon><Plus /></el-icon> Добавить материал
                </el-button>
                <el-button type="success" @click="exportMaterials">
                  <el-icon><Download /></el-icon> Экспорт CSV
                </el-button>
                <el-button type="warning" @click="showImportMaterialsDialog = true">
                  <el-icon><Upload /></el-icon> Импорт CSV
                </el-button>
              </el-button-group>
            </el-col>
          </el-row>
        </el-card>

        <!-- Таблица материалов -->
        <el-card shadow="never">
          <el-table 
            :data="filteredMaterials" 
            v-loading="loadingMaterials"
            stripe
            border
            style="width: 100%"
            height="600"
          >
            <el-table-column prop="name" label="Название" width="200" sortable />
            <el-table-column prop="type" label="Тип" width="120" sortable>
              <template #default="scope">
                {{ scope.row.type || '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="color" label="Цвет" width="100" />
            <el-table-column prop="density" label="Плотность" width="120" align="right" sortable>
              <template #default="scope">
                {{ scope.row.density ? Number(scope.row.density).toFixed(3) + ' г/см³' : '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="cost_per_kg" label="Стоимость за кг" width="140" align="right" sortable>
              <template #default="scope">
                {{ scope.row.cost_per_kg ? Number(scope.row.cost_per_kg).toLocaleString() + ' ₽' : '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="available_quantity" label="Доступно (кг)" width="140" align="right" sortable>
              <template #default="scope">
                <span :class="{ 'low-stock': scope.row.available_quantity < scope.row.minimum_stock }">
                  {{ Number(scope.row.available_quantity).toLocaleString() }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="minimum_stock" label="Мин. запас (кг)" width="140" align="right" sortable>
              <template #default="scope">
                {{ scope.row.minimum_stock ? Number(scope.row.minimum_stock).toLocaleString() : '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="supplier" label="Поставщик" min-width="150" />
            <el-table-column label="Действия" width="180" fixed="right">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editMaterial(scope.row)"
                  :icon="Edit"
                >
                  Изменить
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteMaterial(scope.row)"
                  :icon="Delete"
                >
                  Удалить
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- График по типам материалов -->
        <el-card shadow="never" style="margin-top: 20px;" v-if="materialTypeChart">
          <template #header>
            <div class="card-header">
              <span>Количество материалов по типам</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="materialTypeChartRef"></canvas>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Оборудование -->
      <el-tab-pane label="Оборудование" name="equipment">
        <!-- Панель управления оборудованием -->
        <el-card class="control-card" shadow="never">
          <el-row :gutter="20" align="middle">
            <el-col :span="6">
              <el-input
                v-model="equipmentSearch"
                placeholder="Поиск оборудования..."
                @input="filterEquipment"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="4">
              <el-select v-model="processTypeFilter" placeholder="Тип процесса" @change="filterEquipment" clearable>
                <el-option label="Экструзия" value="extrusion" />
                <el-option label="Кольцевание" value="ringing" />
                <el-option label="Гофрирование мягкое" value="corrugation_soft" />
                <el-option label="Гофрирование жесткое" value="corrugation_hard" />
              </el-select>
            </el-col>
            <el-col :span="14">
              <el-button-group>
                <el-button type="primary" @click="showCreateEquipmentDialog = true">
                  <el-icon><Plus /></el-icon> Добавить оборудование
                </el-button>
                <el-button type="success" @click="exportEquipment">
                  <el-icon><Download /></el-icon> Экспорт CSV
                </el-button>
                <el-button type="warning" @click="showImportEquipmentDialog = true">
                  <el-icon><Upload /></el-icon> Импорт CSV
                </el-button>
              </el-button-group>
            </el-col>
          </el-row>
        </el-card>

        <!-- Таблица оборудования -->
        <el-card shadow="never">
          <el-table 
            :data="filteredEquipment" 
            v-loading="loadingEquipment"
            stripe
            border
            style="width: 100%"
            height="600"
          >
            <el-table-column prop="name" label="Название" width="200" sortable />
            <el-table-column prop="process_type" label="Тип процесса" width="150" sortable>
              <template #default="scope">
                <el-tag size="small" :type="getProcessTypeColor(scope.row.process_type)">
                  {{ getProcessTypeText(scope.row.process_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="capacity_per_hour" label="Производительность (кг/ч)" width="180" align="right" sortable>
              <template #default="scope">
                {{ scope.row.capacity_per_hour ? Number(scope.row.capacity_per_hour).toLocaleString() : '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="setup_time_minutes" label="Время наладки (мин)" width="160" align="right" sortable>
              <template #default="scope">
                {{ scope.row.setup_time_minutes || '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="is_available" label="Доступность" width="120" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.is_available ? 'success' : 'danger'" size="small">
                  {{ scope.row.is_available ? 'Доступно' : 'Недоступно' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="specifications" label="Спецификации" min-width="150">
              <template #default="scope">
                {{ scope.row.specifications || '—' }}
              </template>
            </el-table-column>
            <el-table-column label="Действия" width="180" fixed="right">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editEquipment(scope.row)"
                  :icon="Edit"
                >
                  Изменить
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteEquipment(scope.row)"
                  :icon="Delete"
                >
                  Удалить
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- График распределения оборудования -->
        <el-card shadow="never" style="margin-top: 20px;" v-if="equipmentProcessChart">
          <template #header>
            <div class="card-header">
              <span>Распределение оборудования по процессам</span>
            </div>
          </template>
          <div style="height: 400px; position: relative;">
            <canvas ref="equipmentProcessChartRef"></canvas>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Диалог создания/редактирования материала -->
    <el-dialog 
      v-model="showCreateMaterialDialog" 
      :title="editingMaterial ? 'Редактировать материал' : 'Добавить материал'" 
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form 
        :model="materialForm" 
        :rules="materialRules" 
        ref="materialFormRef"
        label-width="160px"
      >
        <el-form-item label="Название" prop="name">
          <el-input v-model="materialForm.name" placeholder="Полиэтилен высокого давления" />
        </el-form-item>
        
        <el-form-item label="Тип" prop="type">
          <el-select v-model="materialForm.type" placeholder="Выбрать" style="width: 100%">
            <el-option 
              v-for="type in types" 
              :key="type.name"
              :label="type.name"
              :value="type.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Цвет">
          <el-input v-model="materialForm.color" placeholder="прозрачный" />
        </el-form-item>
        
        <el-form-item label="Плотность (г/см³)">
          <el-input-number 
            v-model="materialForm.density" 
            :min="0" 
            :step="0.001"
            :precision="3"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Стоимость (₽/кг)">
          <el-input-number 
            v-model="materialForm.cost_per_kg" 
            :min="0" 
            :step="0.01"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Доступное количество (кг)" prop="available_quantity">
          <el-input-number 
            v-model="materialForm.available_quantity" 
            :min="0" 
            :step="0.1"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Минимальный запас (кг)">
          <el-input-number 
            v-model="materialForm.minimum_stock" 
            :min="0" 
            :step="0.1"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Поставщик">
          <el-input v-model="materialForm.supplier" placeholder="ООО 'Пластик'" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="cancelMaterialEdit">Отмена</el-button>
        <el-button 
          type="primary" 
          @click="saveMaterial" 
          :loading="savingMaterial"
        >
          {{ editingMaterial ? 'Обновить' : 'Создать' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Диалог создания/редактирования оборудования -->
    <el-dialog 
      v-model="showCreateEquipmentDialog" 
      :title="editingEquipment ? 'Редактировать оборудование' : 'Добавить оборудование'" 
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form 
        :model="equipmentForm" 
        :rules="equipmentRules" 
        ref="equipmentFormRef"
        label-width="180px"
      >
        <el-form-item label="Название" prop="name">
          <el-input v-model="equipmentForm.name" placeholder="Экструдер ЭП-63" />
        </el-form-item>
        
        <el-form-item label="Тип процесса" prop="process_type">
          <el-select v-model="equipmentForm.process_type" placeholder="Выбрать" style="width: 100%">
            <el-option label="Экструзия" value="extrusion" />
            <el-option label="Кольцевание" value="ringing" />
            <el-option label="Гофрирование мягкое" value="corrugation_soft" />
            <el-option label="Гофрирование жесткое" value="corrugation_hard" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Производительность (кг/ч)">
          <el-input-number 
            v-model="equipmentForm.capacity_per_hour" 
            :min="0" 
            :step="0.1"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Время наладки (мин)">
          <el-input-number 
            v-model="equipmentForm.setup_time_minutes" 
            :min="0" 
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="Доступность">
          <el-switch 
            v-model="equipmentForm.is_available"
            active-text="Доступно"
            inactive-text="Недоступно"
          />
        </el-form-item>
        
        <el-form-item label="Спецификации">
          <el-input 
            v-model="equipmentForm.specifications" 
            type="textarea"
            :rows="3"
            placeholder="Дополнительные технические характеристики..."
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="cancelEquipmentEdit">Отмена</el-button>
        <el-button 
          type="primary" 
          @click="saveEquipment" 
          :loading="savingEquipment"
        >
          {{ editingEquipment ? 'Обновить' : 'Создать' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Диалог импорта материалов -->
    <el-dialog 
      v-model="showImportMaterialsDialog" 
      title="Импорт материалов из CSV" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-section">
        <el-alert
          title="Формат CSV файла для материалов"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <p>CSV файл должен содержать следующие колонки:</p>
          <code>name,type,color,density,cost_per_kg,available_quantity,minimum_stock,supplier</code>
        </el-alert>
        
        <el-upload
          ref="materialUploadRef"
          :auto-upload="false"
          :on-change="handleMaterialFileChange"
          :show-file-list="false"
          accept=".csv"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            Перетащите CSV файл сюда или <em>нажмите для выбора</em>
          </div>
        </el-upload>
        
        <div v-if="materialCsvFile" style="margin-top: 15px;">
          <el-tag type="success">{{ materialCsvFile.name }}</el-tag>
          <el-button type="text" @click="materialCsvFile = null" style="margin-left: 10px;">Удалить</el-button>
        </div>
        
        <div v-if="materialImportPreview.length > 0" style="margin-top: 20px;">
          <h4>Предварительный просмотр (первые 5 строк):</h4>
          <el-table :data="materialImportPreview.slice(0, 5)" size="small" border>
            <el-table-column prop="name" label="Название" width="150" />
            <el-table-column prop="type" label="Тип" width="80" />
            <el-table-column prop="available_quantity" label="Количество" width="100" />
          </el-table>
          <p style="margin-top: 10px; color: #666;">
            Всего строк для импорта: {{ materialImportPreview.length }}
          </p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showImportMaterialsDialog = false">Отмена</el-button>
        <el-button 
          type="primary" 
          @click="importMaterials" 
          :loading="importingMaterials"
          :disabled="!materialCsvFile"
        >
          Импортировать
        </el-button>
      </template>
    </el-dialog>

    <!-- Диалог импорта оборудования -->
    <el-dialog 
      v-model="showImportEquipmentDialog" 
      title="Импорт оборудования из CSV" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-section">
        <el-alert
          title="Формат CSV файла для оборудования"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <p>CSV файл должен содержать следующие колонки:</p>
          <code>name,process_type,capacity_per_hour,setup_time_minutes,is_available,specifications</code>
        </el-alert>
        
        <el-upload
          ref="equipmentUploadRef"
          :auto-upload="false"
          :on-change="handleEquipmentFileChange"
          :show-file-list="false"
          accept=".csv"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            Перетащите CSV файл сюда или <em>нажмите для выбора</em>
          </div>
        </el-upload>
        
        <div v-if="equipmentCsvFile" style="margin-top: 15px;">
          <el-tag type="success">{{ equipmentCsvFile.name }}</el-tag>
          <el-button type="text" @click="equipmentCsvFile = null" style="margin-left: 10px;">Удалить</el-button>
        </div>
        
        <div v-if="equipmentImportPreview.length > 0" style="margin-top: 20px;">
          <h4>Предварительный просмотр (первые 5 строк):</h4>
          <el-table :data="equipmentImportPreview.slice(0, 5)" size="small" border>
            <el-table-column prop="name" label="Название" width="150" />
            <el-table-column prop="process_type" label="Процесс" width="120" />
            <el-table-column prop="capacity_per_hour" label="Производительность" width="120" />
          </el-table>
          <p style="margin-top: 10px; color: #666;">
            Всего строк для импорта: {{ equipmentImportPreview.length }}
          </p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showImportEquipmentDialog = false">Отмена</el-button>
        <el-button 
          type="primary" 
          @click="importEquipment" 
          :loading="importingEquipment"
          :disabled="!equipmentCsvFile"
        >
          Импортировать
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { api } from '../utils/api'
import { Chart, registerables } from 'chart.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Box, 
  Search, 
  Download, 
  Upload, 
  Edit, 
  Delete,
  Plus,
  UploadFilled 
} from '@element-plus/icons-vue'

Chart.register(...registerables)

export default {
  name: 'Materials',
  components: {
    Box,
    Search,
    Download,
    Upload,
    Edit,
    Delete,
    Plus,
    UploadFilled
  },
  setup() {
    const activeTab = ref('materials')
    const loadingMaterials = ref(false)
    const loadingEquipment = ref(false)
    const savingMaterial = ref(false)
    const savingEquipment = ref(false)
    const importingMaterials = ref(false)
    const importingEquipment = ref(false)
    
    const materials = ref([])
    const equipment = ref([])
    const types = ref([])
    const editingMaterial = ref(null)
    const editingEquipment = ref(null)
    
    // Поиск и фильтрация
    const materialsSearch = ref('')
    const equipmentSearch = ref('')
    const materialTypeFilter = ref('')
    const processTypeFilter = ref('')
    
    // Диалоги
    const showCreateMaterialDialog = ref(false)
    const showCreateEquipmentDialog = ref(false)
    const showImportMaterialsDialog = ref(false)
    const showImportEquipmentDialog = ref(false)
    
    // Импорт
    const materialCsvFile = ref(null)
    const equipmentCsvFile = ref(null)
    const materialImportPreview = ref([])
    const equipmentImportPreview = ref([])
    
    // Графики
    const materialTypeChart = ref(null)
    const equipmentProcessChart = ref(null)
    const materialTypeChartRef = ref(null)
    const equipmentProcessChartRef = ref(null)
    
    let materialChart = null
    let equipmentChart = null
    
    // Формы
    const materialForm = reactive({
      name: '',
      type: '',
      color: '',
      density: null,
      cost_per_kg: null,
      available_quantity: 0,
      minimum_stock: null,
      supplier: ''
    })

    const equipmentForm = reactive({
      name: '',
      process_type: '',
      capacity_per_hour: null,
      setup_time_minutes: null,
      is_available: true,
      specifications: ''
    })

    // Правила валидации
    const materialRules = {
      name: [
        { required: true, message: 'Название обязательно', trigger: 'blur' }
      ],
      type: [
        { required: true, message: 'Выберите тип материала', trigger: 'change' }
      ],
      available_quantity: [
        { required: true, message: 'Укажите доступное количество', trigger: 'blur' }
      ]
    }

    const equipmentRules = {
      name: [
        { required: true, message: 'Название обязательно', trigger: 'blur' }
      ],
      process_type: [
        { required: true, message: 'Выберите тип процесса', trigger: 'change' }
      ]
    }

    // Фильтрованные данные
    const filteredMaterials = computed(() => {
      return materials.value.filter(material => {
        const matchesSearch = !materialsSearch.value || 
          material.name.toLowerCase().includes(materialsSearch.value.toLowerCase()) ||
          (material.supplier && material.supplier.toLowerCase().includes(materialsSearch.value.toLowerCase()))
        
        const matchesType = !materialTypeFilter.value || 
          material.type === materialTypeFilter.value
        
        return matchesSearch && matchesType
      })
    })

    const filteredEquipment = computed(() => {
      return equipment.value.filter(eq => {
        const matchesSearch = !equipmentSearch.value || 
          eq.name.toLowerCase().includes(equipmentSearch.value.toLowerCase())
        
        const matchesProcess = !processTypeFilter.value || eq.process_type === processTypeFilter.value
        
        return matchesSearch && matchesProcess
      })
    })

    // API методы для материалов
    const loadMaterials = async () => {
      loadingMaterials.value = true
      try {
        materials.value = await api.get('/materials/')
        await prepareMaterialChart()
      } catch (error) {
        ElMessage.error('Ошибка загрузки материалов')
      } finally {
        loadingMaterials.value = false
      }
    }

    // Загрузка типов материалов
    const loadTypes = async () => {
      console.log('🔄 Загружаю типы материалов...')
      try {
        const response = await api.get('/materials/types/')
        // Преобразуем массив строк в объекты для совместимости
        types.value = response.map(typeName => ({
          id: typeName,
          name: typeName,
          description: typeName
        }))
        console.log('✅ Типы материалов загружены:', types.value)
      } catch (error) {
        console.error('❌ Ошибка загрузки типов материалов:', error)
        ElMessage.error('Ошибка загрузки типов материалов')
      }
    }

    const saveMaterial = async () => {
      savingMaterial.value = true
      try {
        if (editingMaterial.value) {
          await api.put(`/materials/${editingMaterial.value.id}`, materialForm)
          ElMessage.success('Материал успешно обновлен!')
        } else {
          await api.post('/materials/', materialForm)
          ElMessage.success('Материал успешно создан!')
        }
        
        cancelMaterialEdit()
        loadMaterials()
      } catch (error) {
        ElMessage.error('Ошибка при сохранении материала')
      } finally {
        savingMaterial.value = false
      }
    }

    const editMaterial = (material) => {
      editingMaterial.value = material
      Object.assign(materialForm, {
        name: material.name,
        type: material.type || '',
        color: material.color || '',
        density: material.density ? Number(material.density) : null,
        cost_per_kg: material.cost_per_kg ? Number(material.cost_per_kg) : null,
        available_quantity: Number(material.available_quantity),
        minimum_stock: material.minimum_stock ? Number(material.minimum_stock) : null,
        supplier: material.supplier || ''
      })
      showCreateMaterialDialog.value = true
    }

    const deleteMaterial = async (material) => {
      try {
        await ElMessageBox.confirm(
          `Вы уверены, что хотите удалить материал "${material.name}"?`,
          'Подтверждение удаления',
          {
            confirmButtonText: 'Удалить',
            cancelButtonText: 'Отмена',
            type: 'warning',
          }
        )
        
        await api.delete(`/materials/${material.id}`)
        ElMessage.success('Материал успешно удален!')
        loadMaterials()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Ошибка при удалении материала')
        }
      }
    }

    const cancelMaterialEdit = () => {
      editingMaterial.value = null
      showCreateMaterialDialog.value = false
      Object.assign(materialForm, {
        name: '',
        type: '',
        color: '',
        density: null,
        cost_per_kg: null,
        available_quantity: 0,
        minimum_stock: null,
        supplier: ''
      })
    }

    // API методы для оборудования
    const loadEquipment = async () => {
      loadingEquipment.value = true
      try {
        equipment.value = await api.get('/equipment/')
        await prepareEquipmentChart()
      } catch (error) {
        ElMessage.error('Ошибка загрузки оборудования')
      } finally {
        loadingEquipment.value = false
      }
    }

    const saveEquipment = async () => {
      savingEquipment.value = true
      try {
        if (editingEquipment.value) {
          await api.put(`/equipment/${editingEquipment.value.id}`, equipmentForm)
          ElMessage.success('Оборудование успешно обновлено!')
        } else {
          await api.post('/equipment/', equipmentForm)
          ElMessage.success('Оборудование успешно создано!')
        }
        
        cancelEquipmentEdit()
        loadEquipment()
      } catch (error) {
        ElMessage.error('Ошибка при сохранении оборудования')
      } finally {
        savingEquipment.value = false
      }
    }

    const editEquipment = (eq) => {
      editingEquipment.value = eq
      Object.assign(equipmentForm, {
        name: eq.name,
        process_type: eq.process_type,
        capacity_per_hour: eq.capacity_per_hour ? Number(eq.capacity_per_hour) : null,
        setup_time_minutes: eq.setup_time_minutes || null,
        is_available: eq.is_available,
        specifications: eq.specifications || ''
      })
      showCreateEquipmentDialog.value = true
    }

    const deleteEquipment = async (eq) => {
      try {
        await ElMessageBox.confirm(
          `Вы уверены, что хотите удалить оборудование "${eq.name}"?`,
          'Подтверждение удаления',
          {
            confirmButtonText: 'Удалить',
            cancelButtonText: 'Отмена',
            type: 'warning',
          }
        )
        
        await api.delete(`/equipment/${eq.id}`)
        ElMessage.success('Оборудование успешно удалено!')
        loadEquipment()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Ошибка при удалении оборудования')
        }
      }
    }

    const cancelEquipmentEdit = () => {
      editingEquipment.value = null
      showCreateEquipmentDialog.value = false
      Object.assign(equipmentForm, {
        name: '',
        process_type: '',
        capacity_per_hour: null,
        setup_time_minutes: null,
        is_available: true,
        specifications: ''
      })
    }

    // Экспорт/импорт материалов
    const exportMaterials = () => {
      const csv = [
        'name,type,color,density,cost_per_kg,available_quantity,minimum_stock,supplier',
        ...materials.value.map(material => 
          `"${material.name}","${material.type || ''}","${material.color || ''}",${material.density || ''},${material.cost_per_kg || ''},${material.available_quantity},${material.minimum_stock || ''},"${material.supplier || ''}"`
        )
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `materials_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    }

    const handleMaterialFileChange = (file) => {
      materialCsvFile.value = file.raw
      parseCSV(file.raw, (data) => {
        // Преобразуем название типа в type
        data.forEach(row => {
          if (row.type) {
            const foundType = types.value.find(t => t.name === row.type || t.description === row.type)
            if (foundType) {
              row.type = foundType.name
            } else {
              // Если тип не найден, оставляем как есть для отображения ошибки
              row.type = null
            }
          }
        })
        materialImportPreview.value = data
      })
    }

    const importMaterials = async () => {
      importingMaterials.value = true
      try {
        const result = await api.post('/materials/bulk-import', materialImportPreview.value)
        
        if (result.created_count > 0) {
          ElMessage.success(`Успешно импортировано ${result.created_count} материалов`)
        }
        
        if (result.error_count > 0) {
          ElMessageBox.alert(
            result.errors.join('\n'),
            `Ошибки импорта (${result.error_count})`,
            { type: 'warning' }
          )
        }
        
        showImportMaterialsDialog.value = false
        materialCsvFile.value = null
        materialImportPreview.value = []
        loadMaterials()
      } catch (error) {
        ElMessage.error('Ошибка при импорте материалов')
      } finally {
        importingMaterials.value = false
      }
    }

    // Экспорт/импорт оборудования
    const exportEquipment = () => {
      const csv = [
        'name,process_type,capacity_per_hour,setup_time_minutes,is_available,specifications',
        ...equipment.value.map(eq => 
          `"${eq.name}",${eq.process_type},${eq.capacity_per_hour || ''},${eq.setup_time_minutes || ''},${eq.is_available},"${eq.specifications || ''}"`
        )
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `equipment_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    }

    const handleEquipmentFileChange = (file) => {
      equipmentCsvFile.value = file.raw
      parseCSV(file.raw, (data) => {
        // Преобразуем is_available в boolean
        data.forEach(row => {
          if (row.is_available !== undefined) {
            row.is_available = row.is_available === 'true' || row.is_available === '1'
          }
        })
        equipmentImportPreview.value = data
      })
    }

    const importEquipment = async () => {
      importingEquipment.value = true
      try {
        const result = await api.post('/equipment/bulk-import', equipmentImportPreview.value)
        
        if (result.created_count > 0) {
          ElMessage.success(`Успешно импортировано ${result.created_count} единиц оборудования`)
        }
        
        if (result.error_count > 0) {
          ElMessageBox.alert(
            result.errors.join('\n'),
            `Ошибки импорта (${result.error_count})`,
            { type: 'warning' }
          )
        }
        
        showImportEquipmentDialog.value = false
        equipmentCsvFile.value = null
        equipmentImportPreview.value = []
        loadEquipment()
      } catch (error) {
        ElMessage.error('Ошибка при импорте оборудования')
      } finally {
        importingEquipment.value = false
      }
    }

    // Утилиты
    const parseCSV = (file, callback) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target.result
        const lines = text.split('\n').filter(line => line.trim())
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
        
        const data = []
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''))
          if (values.length === headers.length) {
            const row = {}
            headers.forEach((header, index) => {
              row[header] = values[index] || null
            })
            data.push(row)
          }
        }
        
        callback(data)
      }
      reader.readAsText(file)
    }

    const filterMaterials = () => {
      // Фильтрация происходит автоматически через computed свойство
    }

    const filterEquipment = () => {
      // Фильтрация происходит автоматически через computed свойство
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

    // Графики
    const prepareMaterialChart = async () => {
      if (!materials.value.length) return

      const typeCounts = {}
      materials.value.forEach(material => {
        const typeName = material.type || 'Неизвестный'
        typeCounts[typeName] = (typeCounts[typeName] || 0) + 1
      })

      materialTypeChart.value = {
        labels: Object.keys(typeCounts),
        data: Object.values(typeCounts)
      }

      await nextTick()
      createMaterialChart()
    }

    const prepareEquipmentChart = async () => {
      if (!equipment.value.length) return

      const processCounts = {}
      equipment.value.forEach(eq => {
        const process = eq.process_type
        processCounts[process] = (processCounts[process] || 0) + 1
      })

      equipmentProcessChart.value = {
        labels: Object.keys(processCounts),
        data: Object.values(processCounts)
      }

      await nextTick()
      createEquipmentChart()
    }

    const createMaterialChart = () => {
      if (materialTypeChartRef.value && materialTypeChart.value) {
        const ctx = materialTypeChartRef.value.getContext('2d')
        
        if (materialChart) {
          materialChart.destroy()
        }
        
        materialChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: materialTypeChart.value.labels,
            datasets: [{
              label: 'Количество материалов',
              data: materialTypeChart.value.data,
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

    const createEquipmentChart = () => {
      if (equipmentProcessChartRef.value && equipmentProcessChart.value) {
        const ctx = equipmentProcessChartRef.value.getContext('2d')
        
        if (equipmentChart) {
          equipmentChart.destroy()
        }
        
        equipmentChart = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: equipmentProcessChart.value.labels.map(getProcessTypeText),
            datasets: [{
              data: equipmentProcessChart.value.data,
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
    }

    onMounted(() => {
      console.log('🚀 Компонент Materials mounted, загружаю данные...')
      loadTypes()
      loadMaterials()
      loadEquipment()
    })

    return {
      activeTab,
      loadingMaterials,
      loadingEquipment,
      savingMaterial,
      savingEquipment,
      importingMaterials,
      importingEquipment,
      
      materials,
      equipment,
      types,
      editingMaterial,
      editingEquipment,
      
      materialsSearch,
      equipmentSearch,
      materialTypeFilter,
      processTypeFilter,
      
      showCreateMaterialDialog,
      showCreateEquipmentDialog,
      showImportMaterialsDialog,
      showImportEquipmentDialog,
      
      materialCsvFile,
      equipmentCsvFile,
      materialImportPreview,
      equipmentImportPreview,
      
      materialForm,
      equipmentForm,
      materialRules,
      equipmentRules,
      
      filteredMaterials,
      filteredEquipment,
      
      loadMaterials,
      loadTypes,
      saveMaterial,
      editMaterial,
      deleteMaterial,
      cancelMaterialEdit,
      
      loadEquipment,
      saveEquipment,
      editEquipment,
      deleteEquipment,
      cancelEquipmentEdit,
      
      exportMaterials,
      exportEquipment,
      handleMaterialFileChange,
      handleEquipmentFileChange,
      importMaterials,
      importEquipment,
      
      filterMaterials,
      filterEquipment,
      getProcessTypeText,
      getProcessTypeColor,
      
      materialTypeChart,
      equipmentProcessChart,
      materialTypeChartRef,
      equipmentProcessChartRef
    }
  }
}
</script>

<style scoped>
.materials {
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

.control-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}

.low-stock {
  color: #F56C6C;
  font-weight: bold;
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

:deep(.el-upload-dragger) {
  width: 100%;
}
</style> 