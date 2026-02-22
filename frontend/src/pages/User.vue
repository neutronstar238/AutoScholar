<template>
  <div class="user-page">
    <el-card class="user-card">
      <h2>👤 用户中心</h2>
      
      <el-form label-width="120px">
        <el-form-item label="用户名">
          <el-input v-model="user.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="user.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="API Key">
          <el-input 
            v-model="user.apiKey" 
            type="password" 
            placeholder="请输入 API Key"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="testConnection">测试连接</el-button>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <div class="stats">
        <h3>使用统计</h3>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="文献检索次数" :value="stats.searches" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="生成笔记数" :value="stats.notes" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="使用天数" :value="stats.days" />
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'User',
  data() {
    return {
      user: {
        username: '',
        email: '',
        apiKey: ''
      },
      stats: {
        searches: 0,
        notes: 0,
        days: 0
      }
    }
  },
  methods: {
    saveSettings() {
      this.$message.success('设置已保存')
    },
    testConnection() {
      this.$message.info('连接测试功能开发中...')
    }
  }
}
</script>

<style scoped>
.user-card {
  max-width: 800px;
  margin: 0 auto;
}
.stats {
  margin-top: 20px;
}
</style>
