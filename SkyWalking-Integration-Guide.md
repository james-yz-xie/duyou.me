# SkyWalking 前端集成指南

## 文件清单

已生成的前端文件：

1. **skywalking-api-client.js** - API 客户端
2. **SkyWalking.vue** - 监控仪表板组件
3. **skywalking-route-config.js** - 路由配置

## 集成步骤

### 1. 复制文件到项目

```bash
# API 客户端
cp skywalking-api-client.js /path/to/tianji/tianji-portal-vue/src/api/skywalking.js

# Vue 组件
mkdir -p /path/to/tianji/tianji-portal-vue/src/views/monitoring
cp SkyWalking.vue /path/to/tianji/tianji-portal-vue/src/views/monitoring/SkyWalking.vue

# 路由配置（手动合并）
# 参考 skywalking-route-config.js 中的配置添加到现有路由文件
```

### 2. 安装依赖

确保项目已安装以下依赖：

```bash
cd tianji-portal-vue
npm install axios echarts element-ui
```

### 3. 配置路由

在 `tianji-portal-vue/src/router/index.js` 中添加：

```javascript
import SkyWalking from '@/views/monitoring/SkyWalking.vue'

const routes = [
  // ... existing routes
  {
    path: '/monitoring/skywalking',
    name: 'SkyWalking',
    component: SkyWalking,
    meta: {
      title: 'SkyWalking APM 监控',
      icon: 'el-icon-monitor',
      requiresAuth: true
    }
  }
]
```

### 4. 添加菜单项

在主布局或侧边栏菜单中添加导航链接：

```vue
<el-menu-item index="/monitoring/skywalking">
  <i class="el-icon-monitor"></i>
  <span slot="title">SkyWalking 监控</span>
</el-menu-item>
```

### 5. 验证后端 API

确保后端服务已启动并可访问：

```bash
# 测试健康检查接口
curl http://localhost:8080/api/skywalking/health

# 测试服务列表接口
curl http://localhost:8080/api/skywalking/services
```

### 6. 启动前端开发服务器

```bash
cd tianji-portal-vue
npm run serve
```

访问 `http://localhost:8081/monitoring/skywalking` 查看监控面板。

## 功能特性

- ✅ 服务拓扑可视化（ECharts 力导向图）
- ✅ 实时指标展示（请求数、响应时间、错误率、活跃服务）
- ✅ 服务列表管理（支持搜索过滤）
- ✅ 链路追踪列表（点击查看详情）
- ✅ 告警信息展示（可调整显示数量）
- ✅ 健康状态监控
- ✅ 一键刷新所有数据

## 注意事项

1. **API 基础路径**：确保 `skywalking-api-client.js` 中的 `baseURL` 与后端配置一致
2. **认证令牌**：如果项目使用 JWT，确保请求拦截器正确配置
3. **跨域问题**：开发环境下可能需要配置代理解决 CORS 问题
4. **ECharts 版本**：建议使用 ECharts 5.x 版本以获得最佳性能

## 后续优化建议

1. 添加 WebSocket 实时更新支持
2. 实现自定义时间范围选择器
3. 增加更多图表类型（折线图、柱状图等）
4. 添加导出报告功能
5. 实现告警规则配置界面
