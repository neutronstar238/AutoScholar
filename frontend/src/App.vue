<template>
  <div id="autoscholar">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>🚀 AutoScholar</h1>
          <el-menu mode="horizontal" :default-active="$route.path" router>
            <el-menu-item index="/">文献检索</el-menu-item>
            <el-menu-item index="/notes">研究笔记</el-menu-item>
            <el-menu-item index="/research">研究方向</el-menu-item>
            <el-menu-item index="/user">用户中心</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <router-view />
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
  height: 100vh;
}
.el-container {
  height: 100%;
}
.el-header {
  background-color: #409EFF;
  color: white;
  padding: 0;
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 100%;
}
.header-content h1 {
  margin: 0;
  font-size: 24px;
}
.el-menu--horizontal {
  border-bottom: none;
  background-color: transparent;
}
.el-menu--horizontal .el-menu-item {
  color: white;
  border-bottom: 2px solid transparent;
}
.el-menu--horizontal .el-menu-item:hover,
.el-menu--horizontal .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}
.el-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>
