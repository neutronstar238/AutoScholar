<template>
  <div id="autoscholar">
    <el-container>
      <el-header>
        <h1>🚀 AutoScholar</h1>
        <p>自主学术研究 AI Agent 系统</p>
      </el-header>
      <el-main>
        <el-card>
          <template #header>
            <span>欢迎使用 AutoScholar</span>
          </template>
          <p>正在开发中... 敬请期待！</p>
          <el-progress :percentage="40" status="active"></el-progress>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#autoscholar {
  font-family: Arial, sans-serif;
}
.el-header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  line-height: 60px;
}
.el-main {
  padding: 20px;
}
</style>
