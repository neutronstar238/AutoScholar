<template>
  <div class="research-page">
    <el-card class="research-card">
      <h2>🔬 研究方向推荐</h2>
      
      <el-form label-width="120px">
        <el-form-item label="研究兴趣">
          <el-select
            v-model="interests"
            multiple
            filterable
            allow-create
            placeholder="输入或选择研究兴趣（如：机器学习、自然语言处理）"
            style="width: 100%"
          >
            <el-option
              v-for="item in commonInterests"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="推荐数量">
          <el-input-number v-model="limit" :min="3" :max="10" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="getRecommendations" :loading="loading">
            获取推荐
          </el-button>
        </el-form-item>
      </el-form>
      
      <div v-if="recommendations" class="recommendations">
        <el-divider />
        <div class="markdown-content" v-html="renderedRecommendations"></div>
        
        <el-divider content-position="left">相关论文</el-divider>
        <div v-for="paper in papers" :key="paper.id" class="paper-item">
          <h4>{{ paper.title }}</h4>
          <p class="authors">{{ paper.authors.join(', ') }}</p>
          <p class="published">发布日期：{{ paper.published }}</p>
          <el-link :href="paper.url" target="_blank" type="primary">查看论文</el-link>
        </div>
      </div>
      
      <el-empty v-else description="输入研究兴趣，获取个性化推荐"></el-empty>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import { marked } from 'marked'

export default {
  name: 'Research',
  data() {
    return {
      interests: [],
      limit: 5,
      loading: false,
      recommendations: null,
      papers: [],
      commonInterests: [
        '机器学习',
        '深度学习',
        '自然语言处理',
        '计算机视觉',
        '强化学习',
        '推荐系统',
        '知识图谱',
        '大语言模型',
        '多模态学习',
        '联邦学习'
      ]
    }
  },
  computed: {
    renderedRecommendations() {
      return this.recommendations ? marked(this.recommendations) : ''
    }
  },
  methods: {
    async getRecommendations() {
      if (this.interests.length === 0) {
        this.$message.warning('请至少选择一个研究兴趣')
        return
      }
      
      this.loading = true
      try {
        const response = await axios.post('/api/v1/research/recommend', {
          interests: this.interests,
          limit: this.limit
        })
        
        if (response.data.success) {
          this.recommendations = response.data.recommendations
          this.papers = response.data.papers || []
          this.$message.success('推荐生成成功！')
        } else {
          this.$message.error('推荐失败：' + response.data.error)
        }
      } catch (error) {
        this.$message.error('请求失败：' + error.message)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.research-card {
  max-width: 1000px;
  margin: 0 auto;
}
.recommendations {
  margin-top: 20px;
}
.markdown-content {
  line-height: 1.8;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 4px;
}
.paper-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
}
.paper-item h4 {
  margin: 0 0 10px 0;
  color: #333;
}
.authors {
  color: #666;
  font-size: 14px;
  margin: 5px 0;
}
.published {
  color: #999;
  font-size: 13px;
  margin: 5px 0;
}
</style>