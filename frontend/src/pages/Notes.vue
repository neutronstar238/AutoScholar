<template>
  <div class="notes-page">
    <el-card class="notes-card">
      <h2>📝 研究笔记</h2>
      
      <el-input
        v-model="paperUrl"
        placeholder="输入论文 URL (如：https://arxiv.org/abs/2401.12345)"
        clearable
        class="url-input"
      >
        <template #append>
          <el-button type="primary" @click="generateNote" :loading="generating">
            生成笔记
          </el-button>
        </template>
      </el-input>

      <div v-loading="loading" class="notes-list">
        <el-empty v-if="!loading && notes.length === 0" description="暂无笔记，输入论文 URL 生成"></el-empty>
        
        <div v-for="note in notes" :key="note.id" class="note-item">
          <h4>{{ note.title }}</h4>
          <el-tag size="small">{{ note.model }}</el-tag>
          <div class="note-content" v-html="renderedContent(note.content)"></div>
          <div class="note-actions">
            <el-button size="small" @click="copyNote(note)">复制</el-button>
            <el-button size="small" type="danger" @click="deleteNote(note)">删除</el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import { marked } from 'marked'

export default {
  name: 'Notes',
  data() {
    return {
      paperUrl: '',
      loading: false,
      generating: false,
      notes: []
    }
  },
  methods: {
    async generateNote() {
      if (!this.paperUrl) {
        this.$message.warning('请输入论文 URL')
        return
      }
      
      this.generating = true
      try {
        const response = await axios.post('/api/v1/notes/generate', {
          paper_url: this.paperUrl
        })
        
        if (response.data.success) {
          this.notes.unshift({
            id: Date.now(),
            title: '研究笔记',
            content: response.data.note,
            model: response.data.model,
            created_at: new Date()
          })
          this.$message.success('笔记生成成功！')
          this.paperUrl = ''
        } else {
          this.$message.error('生成失败：' + response.data.error)
        }
      } catch (error) {
        this.$message.error('请求失败：' + error.message)
      } finally {
        this.generating = false
      }
    },
    renderedContent(content) {
      return marked(content || '')
    },
    copyNote(note) {
      navigator.clipboard.writeText(note.content)
      this.$message.success('已复制到剪贴板')
    },
    deleteNote(note) {
      this.notes = this.notes.filter(n => n.id !== note.id)
      this.$message.success('已删除')
    }
  }
}
</script>

<style scoped>
.notes-card {
  max-width: 900px;
  margin: 0 auto;
}
.url-input {
  margin: 20px 0;
}
.note-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
}
.note-item h4 {
  margin: 0 0 10px 0;
}
.note-content {
  margin: 15px 0;
  line-height: 1.6;
}
.note-actions {
  text-align: right;
}
</style>
