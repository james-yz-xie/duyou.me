<template>
  <div class="skywalking-monitor">
    <!-- Header -->
    <div class="monitor-header">
      <h2>SkyWalking APM 监控</h2>
      <div class="header-actions">
        <el-button 
          :type="healthStatus === 'healthy' ? 'success' : 'danger'" 
          size="small"
          @click="checkHealth"
        >
          {{ healthStatus === 'healthy' ? '● 正常' : '● 异常' }}
        </el-button>
        <el-button type="primary" size="small" @click="refreshAll">
          <i class="el-icon-refresh"></i> 刷新
        </el-button>
      </div>
    </div>

    <!-- Service Topology -->
    <el-card class="topology-card" shadow="hover">
      <div slot="header" class="card-header">
        <span>服务拓扑</span>
      </div>
      <div ref="topologyChart" class="topology-chart"></div>
    </el-card>

    <!-- Metrics Overview -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6" v-for="(metric, index) in metricsOverview" :key="index">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-content">
            <div class="metric-icon" :style="{ backgroundColor: metric.color }">
              <i :class="metric.icon"></i>
            </div>
            <div class="metric-info">
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-trend" :class="metric.trendClass">
                {{ metric.trend }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Service List and Traces -->
    <el-row :gutter="20">
      <!-- Service List -->
      <el-col :span="8">
        <el-card shadow="hover">
          <div slot="header" class="card-header">
            <span>服务列表</span>
            <el-input
              v-model="serviceSearch"
              placeholder="搜索服务"
              size="small"
              prefix-icon="el-icon-search"
              clearable
            />
          </div>
          <el-table
            :data="filteredServices"
            style="width: 100%"
            height="400"
            @row-click="onServiceClick"
            highlight-current-row
          >
            <el-table-column prop="name" label="服务名称" />
            <el-table-column prop="instanceCount" label="实例数" width="80" />
            <el-table-column label="状态" width="80">
              <template slot-scope="scope">
                <el-tag 
                  :type="scope.row.status === 'UP' ? 'success' : 'danger'" 
                  size="mini"
                >
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Recent Traces -->
      <el-col :span="16">
        <el-card shadow="hover">
          <div slot="header" class="card-header">
            <span>链路追踪</span>
            <el-button size="mini" @click="loadTraces">刷新</el-button>
          </div>
          <el-table
            :data="traces"
            style="width: 100%"
            height="400"
            v-loading="tracesLoading"
          >
            <el-table-column prop="traceId" label="Trace ID" width="200">
              <template slot-scope="scope">
                <el-link 
                  type="primary" 
                  @click="viewTraceDetail(scope.row.traceId)"
                >
                  {{ scope.row.traceId }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="service" label="服务" width="150" />
            <el-table-column prop="endpoint" label="端点" />
            <el-table-column prop="duration" label="耗时" width="100">
              <template slot-scope="scope">
                <span :class="getDurationClass(scope.row.duration)">
                  {{ scope.row.duration }}ms
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="startTime" label="开始时间" width="180" />
            <el-table-column label="状态" width="80">
              <template slot-scope="scope">
                <el-tag 
                  :type="scope.row.error ? 'danger' : 'success'" 
                  size="mini"
                >
                  {{ scope.row.error ? '错误' : '成功' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- Alarms -->
    <el-card shadow="hover" class="alarms-card">
      <div slot="header" class="card-header">
        <span>告警列表</span>
        <el-select 
          v-model="alarmLimit" 
          size="small" 
          @change="loadAlarms"
          style="width: 120px"
        >
          <el-option label="10条" :value="10" />
          <el-option label="50条" :value="50" />
          <el-option label="100条" :value="100" />
        </el-select>
      </div>
      <el-table
        :data="alarms"
        style="width: 100%"
        v-loading="alarmsLoading"
      >
        <el-table-column prop="alarmMessage" label="告警信息" />
        <el-table-column prop="serviceName" label="服务" width="150" />
        <el-table-column prop="alarmLevel" label="级别" width="80">
          <template slot-scope="scope">
            <el-tag 
              :type="getAlarmLevelType(scope.row.alarmLevel)" 
              size="mini"
            >
              {{ scope.row.alarmLevel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="startTime" label="触发时间" width="180" />
      </el-table>
    </el-card>

    <!-- Trace Detail Dialog -->
    <el-dialog
      title="链路详情"
      :visible.sync="traceDetailVisible"
      width="80%"
      top="5vh"
    >
      <div v-if="traceDetail" class="trace-detail">
        <el-timeline>
          <el-timeline-item
            v-for="(span, index) in traceDetail.spans"
            :key="index"
            :timestamp="formatTimestamp(span.startTime)"
            placement="top"
          >
            <el-card>
              <h4>{{ span.endpointName || span.serviceCode }}</h4>
              <p>Span ID: {{ span.spanId }}</p>
              <p>耗时: {{ span.endTime - span.startTime }}ms</p>
              <p v-if="span.peer">Peer: {{ span.peer }}</p>
              <el-tag 
                v-if="span.isError" 
                type="danger" 
                size="mini"
              >
                Error
              </el-tag>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import {
  getTraceDetail,
  getServiceList,
  getServiceTopology,
  getMetricsData,
  searchTraces,
  getAlarms,
  checkHealth
} from '@/api/skywalking'

export default {
  name: 'SkyWalkingMonitor',
  data() {
    return {
      healthStatus: 'unknown',
      services: [],
      serviceSearch: '',
      traces: [],
      tracesLoading: false,
      alarms: [],
      alarmsLoading: false,
      alarmLimit: 50,
      traceDetailVisible: false,
      traceDetail: null,
      topologyChart: null,
      metricsOverview: [
        { label: '总请求数', value: '0', trend: '+0%', trendClass: 'trend-up', icon: 'el-icon-s-data', color: '#409EFF' },
        { label: '平均响应时间', value: '0ms', trend: '-0%', trendClass: 'trend-down', icon: 'el-icon-time', color: '#67C23A' },
        { label: '错误率', value: '0%', trend: '+0%', trendClass: 'trend-up', icon: 'el-icon-warning', color: '#F56C6C' },
        { label: '活跃服务', value: '0', trend: '稳定', trendClass: 'trend-stable', icon: 'el-icon-connection', color: '#E6A23C' }
      ]
    }
  },
  computed: {
    filteredServices() {
      if (!this.serviceSearch) return this.services
      return this.services.filter(s => 
        s.name.toLowerCase().includes(this.serviceSearch.toLowerCase())
      )
    }
  },
  mounted() {
    this.initDashboard()
  },
  beforeDestroy() {
    if (this.topologyChart) {
      this.topologyChart.dispose()
    }
  },
  methods: {
    async initDashboard() {
      await Promise.all([
        this.checkHealth(),
        this.loadServices(),
        this.loadTraces(),
        this.loadAlarms(),
        this.loadTopology(),
        this.loadMetrics()
      ])
    },

    async refreshAll() {
      this.$message.info('正在刷新数据...')
      await this.initDashboard()
      this.$message.success('刷新完成')
    },

    async checkHealth() {
      try {
        const res = await checkHealth()
        this.healthStatus = res.data?.status || 'unhealthy'
      } catch (error) {
        this.healthStatus = 'error'
        console.error('Health check failed:', error)
      }
    },

    async loadServices() {
      try {
        const res = await getServiceList()
        this.services = res.data || []
        this.updateMetricsOverview()
      } catch (error) {
        this.$message.error('加载服务列表失败')
        console.error(error)
      }
    },

    async loadTraces() {
      this.tracesLoading = true
      try {
        const res = await searchTraces({})
        this.traces = (res.data || []).slice(0, 50)
      } catch (error) {
        this.$message.error('加载链路追踪失败')
        console.error(error)
      } finally {
        this.tracesLoading = false
      }
    },

    async loadAlarms() {
      this.alarmsLoading = true
      try {
        const res = await getAlarms(this.alarmLimit)
        this.alarms = res.data || []
      } catch (error) {
        this.$message.error('加载告警列表失败')
        console.error(error)
      } finally {
        this.alarmsLoading = false
      }
    },

    async loadTopology() {
      try {
        const res = await getServiceTopology()
        this.renderTopology(res.data)
      } catch (error) {
        console.error('加载拓扑图失败:', error)
      }
    },

    async loadMetrics() {
      try {
        const responseTime = await getMetricsData('service_resp_time')
        const throughput = await getMetricsData('service_throughput')
        const errorRate = await getMetricsData('service_error_rate')
        
        this.metricsOverview[0].value = throughput.data?.value || '0'
        this.metricsOverview[1].value = `${responseTime.data?.value || 0}ms`
        this.metricsOverview[2].value = `${errorRate.data?.value || 0}%`
        this.metricsOverview[3].value = this.services.length
      } catch (error) {
        console.error('加载指标数据失败:', error)
      }
    },

    renderTopology(data) {
      if (!this.$refs.topologyChart) return
      
      if (!this.topologyChart) {
        this.topologyChart = echarts.init(this.$refs.topologyChart)
      }

      const nodes = (data?.nodes || []).map(node => ({
        id: node.id,
        name: node.name,
        value: node.calls || 0,
        symbolSize: Math.sqrt(node.calls || 1) * 10 + 20
      }))

      const edges = (data?.edges || []).map(edge => ({
        source: edge.source,
        target: edge.target,
        value: edge.calls || 0
      }))

      const option = {
        tooltip: {},
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [{
          type: 'graph',
          layout: 'force',
          force: {
            repulsion: 100,
            gravity: 0.1,
            edgeLength: 150
          },
          roam: true,
          label: {
            show: true,
            position: 'right'
          },
          edgeSymbol: ['circle', 'arrow'],
          edgeSymbolSize: [4, 10],
          data: nodes,
          links: edges,
          lineStyle: {
            color: 'source',
            curveness: 0.3
          }
        }]
      }

      this.topologyChart.setOption(option)
    },

    onServiceClick(service) {
      this.$message.info(`查看服务: ${service.name}`)
      // TODO: Implement service detail view
    },

    async viewTraceDetail(traceId) {
      try {
        const res = await getTraceDetail(traceId)
        this.traceDetail = res.data
        this.traceDetailVisible = true
      } catch (error) {
        this.$message.error('获取链路详情失败')
        console.error(error)
      }
    },

    updateMetricsOverview() {
      // Update active services count
      this.metricsOverview[3].value = this.services.length
    },

    getDurationClass(duration) {
      if (duration > 1000) return 'duration-slow'
      if (duration > 500) return 'duration-medium'
      return 'duration-fast'
    },

    getAlarmLevelType(level) {
      const levelMap = {
        'CRITICAL': 'danger',
        'WARNING': 'warning',
        'INFO': 'info'
      }
      return levelMap[level] || 'info'
    },

    formatTimestamp(timestamp) {
      if (!timestamp) return ''
      return new Date(timestamp).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.skywalking-monitor {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.monitor-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topology-card {
  margin-bottom: 20px;
}

.topology-chart {
  height: 400px;
  width: 100%;
}

.metrics-row {
  margin-bottom: 20px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.metric-info {
  flex: 1;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.metric-trend {
  font-size: 12px;
}

.trend-up {
  color: #F56C6C;
}

.trend-down {
  color: #67C23A;
}

.trend-stable {
  color: #909399;
}

.duration-slow {
  color: #F56C6C;
  font-weight: bold;
}

.duration-medium {
  color: #E6A23C;
}

.duration-fast {
  color: #67C23A;
}

.alarms-card {
  margin-top: 20px;
}

.trace-detail {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
