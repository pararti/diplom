<template>
  <div id="app">
    <el-container>
      <!-- Заголовок -->
      <el-header>
        <div class="header">
          <div class="header-title">
            <el-icon><Factory /></el-icon>
            <h1>Система планирования производства Атлантис-Пак</h1>
          </div>
          <div class="header-actions">
            <el-badge :value="systemStatus.status === 'ok' ? 0 : 1" class="status-badge">
              <el-button 
                :type="systemStatus.status === 'ok' ? 'success' : 'danger'" 
                circle 
                size="small"
                @click="checkSystemHealth"
              >
                <el-icon><Monitor /></el-icon>
              </el-button>
            </el-badge>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- Боковое меню -->
        <el-aside width="250px">
          <el-menu
            :default-active="$route.path"
            router
            class="sidebar-menu"
            background-color="#f5f7fa"
          >
            <el-menu-item index="/">
              <el-icon><Odometer /></el-icon>
              <span>Главная панель</span>
            </el-menu-item>
            
            <el-menu-item index="/orders">
              <el-icon><Document /></el-icon>
              <span>Управление заказами</span>
            </el-menu-item>
            
            <el-menu-item index="/materials">
              <el-icon><Box /></el-icon>
              <span>Материалы и оборудование</span>
            </el-menu-item>
            
            <el-menu-item index="/optimization">
              <el-icon><Lightning /></el-icon>
              <span>Оптимизация планирования</span>
            </el-menu-item>
            
            <el-menu-item index="/schedule">
              <el-icon><Calendar /></el-icon>
              <span>Текущее расписание</span>
            </el-menu-item>
            
            <el-menu-item index="/analytics">
              <el-icon><TrendCharts /></el-icon>
              <span>Аналитика и отчеты</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- Основной контент -->
        <el-main>
          <div class="main-content">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { apiClient } from './utils/api'

export default {
  name: 'App',
  setup() {
    const systemStatus = ref({ status: 'checking' })

    const checkSystemHealth = async () => {
      try {
        await apiClient.get('/health')
        systemStatus.value = { status: 'ok' }
      } catch (error) {
        systemStatus.value = { status: 'error', message: error.message }
      }
    }

    onMounted(() => {
      checkSystemHealth()
      // Проверяем статус каждые 30 секунд
      setInterval(checkSystemHealth, 30000)
    })

    return {
      systemStatus,
      checkSystemHealth
    }
  }
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-title h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.sidebar-menu {
  height: calc(100vh - 60px);
  border-right: none;
}

.main-content {
  padding: 20px;
  min-height: calc(100vh - 100px);
  background-color: #f8f9fa;
}

.status-badge {
  margin-right: 10px;
}

#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style> 