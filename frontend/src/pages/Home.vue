<template>
  <div class="home">
    <el-card class="search-card">
      <h2>📚 文献检索</h2>
      <el-input
        v-model="searchQuery"
        placeholder="输入搜索关键词..."
        clearable
        @keyup.enter="searchLiterature"
      >
        <template #append>
          <el-button @click="searchLiterature">搜索</el-button>
        </template>
      </el-input>
      
      <div v-loading="loading" class="results">
        <el-empty v-if="!loading && results.length === 0" description="暂无结果"></el-empty>
        <div v-for="paper in results" :key="paper.id" class="paper-item">
          <h4>{{ paper.title }}</h4>
          <p class="authors">{{ paper.authors.join(', ') }}</p>
          <p class="abstract">{{ paper.abstract }}</p>
          <el-link :href="paper.url" target="_blank" type="primary">查看全文</el-link>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      searchQuery: '',
      loading: false,
      results: []
    }
  },
  methods: {
    async searchLiterature() {
      if (!this.searchQuery) return
      
      this.loading = true
      try {
        const response = await axios.post('/api/v1/literature/search', {
          query: this.searchQuery,
          limit: 10
        })
        this.results = response.data.data.papers || []
      } catch (error) {
        this.$message.error('搜索失败：' + error.message)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.search-card {
  max-width: 800px;
  margin: 0 auto;
}
.paper-item {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
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
.abstract {
  color: #888;
  font-size: 13px;
  line-height: 1.5;
  margin: 10px 0;
}
</style>
