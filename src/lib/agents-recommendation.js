---
import Layout from '../layouts/Layout.astro';
import Footer from '../components/Footer.astro';

// 用户需求类型定义
const userNeeds = {
  coding: {
    name: "编程辅助",
    description: "代码生成、调试、重构等编程任务",
    priorityFactors: ["reasoning", "isOpenSource", "isMultiModel", "swebench"]
  },
  automation: {
    name: "自动化任务",
    description: "流程自动化、脚本执行等",
    priorityFactors: ["isMultiModel", "isOpenSource", "reasoning", "category"]
  },
  enterprise: {
    name: "企业级应用",
    description: "需要稳定性和安全性的企业环境",
    priorityFactors: ["isOpenSource", "reasoning", "price", "region"]
  },
  learning: {
    name: "学习研究",
    description: "学习AI Agent技术、研究新功能",
    priorityFactors: ["isOpenSource", "isMultiModel", "reasoning", "community"]
  },
  local: {
    name: "本地部署",
    description: "需要在本地运行，保护数据隐私",
    priorityFactors: ["isOpenSource", "reasoning", "isMultiModel", "localSupport"]
  }
};

// 工具评分算法
function calculateToolScore(tool, userNeed) {
  let score = 0;
  const factors = userNeeds[userNeed].priorityFactors;

  // 根据不同需求类型计算分数
  factors.forEach(factor => {
    switch(factor) {
      case "reasoning":
        if (tool.reasoning) score += 30;
        break;
      case "isOpenSource":
        if (tool.isOpenSource) score += 25;
        break;
      case "isMultiModel":
        if (tool.isMultiModel) score += 20;
        break;
      case "swebench":
        if (tool.swebench !== '-') {
          // 将百分比转换为分数 (80.9% -> 80.9)
          const percentage = parseFloat(tool.swebench);
          score += (percentage / 100) * 15;
        }
        break;
      case "price":
        // 免费工具得分更高
        if (tool.price === 'Free' || tool.price.includes('Free')) score += 20;
        break;
      case "region":
        // 中国用户可能更偏好国内工具
        if (tool.region === '中国') score += 15;
        break;
      case "category":
        // 自动化类别工具得分更高
        if (tool.category === 'automation') score += 20;
        break;
      case "community":
        // 根据stars数量计算社区活跃度
        if (tool.stars !== '-') {
          const stars = parseFloat(tool.stars);
          if (stars > 50) score += 15;
        }
        break;
      case "localSupport":
        // 开源工具通常支持本地部署
        if (tool.isOpenSource) score += 25;
        break;
    }
  });

  return Math.min(score, 100); // 最高100分
}

// 推荐算法
function recommendTools(tools, userNeed, count = 3) {
  // 为每个工具计算得分
  const toolsWithScores = tools.map(tool => {
    return {
      ...tool,
      score: calculateToolScore(tool, userNeed),
      recommendation: getRecommendationReason(tool, userNeed)
    };
  });

  // 按得分排序并返回前N个
  return toolsWithScores
    .sort((a, b) => b.score - a.score)
    .slice(0, count);
}

// 获取推荐理由
function getRecommendationReason(tool, userNeed) {
  const reasons = {
    coding: [
      tool.reasoning ? "强大的推理能力适合复杂编程任务" : "",
      tool.isOpenSource ? "开源可定制，适合深度使用" : "",
      tool.swebench !== '-' ? `SWE-bench ${tool.swebench}表现优异` : "",
      tool.isMultiModel ? "多模型支持，适应不同场景" : ""
    ].filter(Boolean),
    automation: [
      tool.category === 'automation' ? "专为自动化设计" : "",
      tool.isMultiModel ? "多模型支持，适应不同任务" : "",
      tool.isOpenSource ? "开源可扩展" : ""
    ].filter(Boolean),
    enterprise: [
      tool.isOpenSource ? "开源透明，安全可控" : "",
      tool.reasoning ? "强推理能力处理复杂业务" : "",
      tool.region === '中国' ? "本土化支持" : ""
    ].filter(Boolean),
    learning: [
      tool.isOpenSource ? "开源可研究源码" : "",
      tool.isMultiModel ? "多模型对比学习" : "",
      tool.stars !== '-' && parseFloat(tool.stars) > 10 ? "社区活跃，资料丰富" : ""
    ].filter(Boolean),
    local: [
      tool.isOpenSource ? "支持本地部署，保护数据隐私" : "",
      tool.reasoning ? "本地运行仍保持强推理能力" : ""
    ].filter(Boolean)
  };

  return reasons[userNeed] && reasons[userNeed].length > 0
    ? reasons[userNeed][0]
    : "综合表现优秀";
}

// 导出函数
export { userNeeds, recommendTools, calculateToolScore };