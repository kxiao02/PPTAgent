<template>
  <div class="upload-container">
    <h1 class="main-title">PPT 自动生成</h1>

    <div class="upload-options">
      <!-- 模板选择模式 -->
      <div class="template-mode-toggle">
        <button
          @click="useCustomTemplate = true"
          :class="{'active': useCustomTemplate}"
          class="mode-button">
          上传自定义模板
        </button>
        <button
          @click="useCustomTemplate = false"
          :class="{'active': !useCustomTemplate}"
          class="mode-button">
          使用内置模板
        </button>
      </div>

      <!-- 内置模板选择 -->
      <div v-if="!useCustomTemplate" class="template-selection">
        <label class="section-label">选择模板</label>
        <select v-model="selectedTemplate" class="template-selector">
          <option value="" disabled>-- 请选择模板 --</option>
          <option
            v-for="template in availableTemplates"
            :key="template.name"
            :value="template.name">
            {{ template.name }} - {{ template.description }}
          </option>
        </select>

        <!-- 模板预览 -->
        <div v-if="selectedTemplate && getTemplateInfo(selectedTemplate)" class="template-info">
          <div class="template-description">
            {{ getTemplateInfo(selectedTemplate).description }}
          </div>
          <div v-if="getTemplateInfo(selectedTemplate).has_preview" class="template-preview">
            <img
              :src="`/api/template-preview/${selectedTemplate}`"
              :alt="`${selectedTemplate} 预览`"
              @error="handleImageError" />
          </div>
          <div v-else class="no-preview">
            <span>暂无预览</span>
          </div>
        </div>
      </div>

      <!-- 自定义 PPTX 上传 -->
      <div v-if="useCustomTemplate" class="upload-buttons">
        <div class="upload-section">
          <label for="pptx-upload" class="upload-label">
            上传 PPTX 模板
            <span v-if="pptxFile" class="uploaded-symbol">✓</span>
          </label>
          <input
            type="file"
            id="pptx-upload"
            @change="handleFileUpload($event, 'pptx')"
            accept=".pptx" />
        </div>
      </div>

      <!-- PDF 上传 -->
      <div class="upload-section pdf-upload">
        <label for="pdf-upload" class="upload-label">
          上传 PDF 内容
          <span v-if="pdfFile" class="uploaded-symbol">✓</span>
        </label>
        <input
          type="file"
          id="pdf-upload"
          @change="handleFileUpload($event, 'pdf')"
          accept=".pdf" />
      </div>

      <!-- 页数选择 -->
      <div class="selectors">
        <div class="pages-selection">
          <label class="section-label">页数</label>
          <select v-model="selectedPages">
            <option :value="null">自动</option>
            <option v-for="page in pagesOptions" :key="page" :value="page">
              {{ page }} 页
            </option>
          </select>
        </div>
      </div>

      <!-- 提交按钮 -->
      <button @click="goToGenerate" class="next-button" :disabled="!canSubmit">
        {{ canSubmit ? '开始生成' : '请完成必填项' }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UploadComponent',
  data() {
    return {
      useCustomTemplate: false,
      selectedTemplate: 'default',
      availableTemplates: [],
      pptxFile: null,
      pdfFile: null,
      selectedPages: null,  // Default to Auto (Dynamic)
      pagesOptions: Array.from({ length: 12 }, (_, i) => i + 3),
    }
  },
  computed: {
    canSubmit() {
      // PDF is required
      if (!this.pdfFile) return false;

      // If using custom template, PPTX file is required
      if (this.useCustomTemplate && !this.pptxFile) return false;

      // If using built-in template, template must be selected
      if (!this.useCustomTemplate && !this.selectedTemplate) return false;

      return true;
    }
  },
  mounted() {
    this.fetchTemplates();
  },
  methods: {
    async fetchTemplates() {
      try {
        const response = await this.$axios.get('/api/templates');
        this.availableTemplates = response.data.templates;
        console.log(`Loaded ${this.availableTemplates.length} templates`);
      } catch (error) {
        console.error("Failed to fetch templates:", error);
        this.availableTemplates = [];
      }
    },

    handleFileUpload(event, fileType) {
      console.log("File uploaded:", fileType);
      const file = event.target.files[0];
      if (fileType === 'pptx') {
        this.pptxFile = file;
      } else if (fileType === 'pdf') {
        this.pdfFile = file;
      }
    },

    getTemplateInfo(templateName) {
      return this.availableTemplates.find(t => t.name === templateName);
    },

    truncate(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    handleImageError(event) {
      console.warn("Failed to load template preview image");
      event.target.style.display = 'none';
    },

    async goToGenerate() {
      // Backend health check
      try {
        await this.$axios.get('/');
      } catch (error) {
        console.error(error);
        alert('后端服务未运行或繁忙，任务无法处理');
        return;
      }

      // Validation
      if (!this.canSubmit) {
        if (!this.pdfFile) {
          alert('请上传 PDF 文件');
        } else if (this.useCustomTemplate && !this.pptxFile) {
          alert('请上传 PPTX 模板文件');
        } else if (!this.useCustomTemplate && !this.selectedTemplate) {
          alert('请选择模板');
        }
        return;
      }

      // Prepare form data
      const formData = new FormData();

      if (this.useCustomTemplate && this.pptxFile) {
        formData.append('pptxFile', this.pptxFile);
      } else {
        formData.append('selectedTemplate', this.selectedTemplate);
      }

      formData.append('pdfFile', this.pdfFile);

      if (this.selectedPages !== null) {
        formData.append('numberOfPages', this.selectedPages);
      }

      // Submit
      try {
        const uploadResponse = await this.$axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        const taskId = uploadResponse.data.task_id;
        console.log("Task ID:", taskId);

        // Navigate to Generate component with taskId
        this.$router.push({ name: 'Generate', state: { taskId: taskId } });
      } catch (error) {
        console.error("Upload error:", error);
        alert(`上传失败：${error.response?.data?.detail || error.message}`);
      }
    }
  }
}
</script>

<style scoped>
* {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  padding: 20px 20px 40px;
  box-sizing: border-box;
  overflow-y: auto;
}

.main-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin: 10px 0 20px;
  text-align: center;
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  max-width: 800px;
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
  display: block;
}

/* Template Mode Toggle */
.template-mode-toggle {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 10px;
}

.mode-button {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid transparent;
  border-radius: 8px;
  background: white;
  color: #666;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-button:hover {
  border-color: #42b983;
  color: #42b983;
}

.mode-button.active {
  background: #42b983;
  color: white;
  border-color: #42b983;
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.3);
}

/* Template Selection */
.template-selection {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.template-selector {
  padding: 12px 15px;
  border-radius: 8px;
  border: 2px solid #ddd;
  font-size: 15px;
  transition: border-color 0.3s;
  background: white;
}

.template-selector:focus {
  outline: none;
  border-color: #42b983;
}

.template-info {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #eee;
}

.template-description {
  color: #555;
  font-size: 13px;
  margin-bottom: 8px;
  line-height: 1.6;
}

.template-preview {
  margin-top: 8px;
  text-align: center;
}

.template-preview img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  object-fit: contain;
}

.no-preview {
  text-align: center;
  padding: 30px;
  color: #999;
  font-size: 16px;
}

/* Upload Section */
.upload-buttons,
.upload-section {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.upload-section.pdf-upload {
  margin-top: 10px;
}

.upload-label {
  position: relative;
  background-color: #42b983;
  color: white;
  padding: 14px 30px;
  border-radius: 8px;
  cursor: pointer;
  width: 100%;
  max-width: 300px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  font-size: 16px;
  font-weight: 500;
}

.upload-label:hover {
  background-color: #369870;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(66, 185, 131, 0.3);
}

.upload-section input[type="file"] {
  display: none;
}

.uploaded-symbol {
  position: absolute;
  right: 15px;
  color: #90ee90;
  font-size: 20px;
}

/* Page Selection */
.selectors {
  display: flex;
  justify-content: center;
  width: 100%;
}

.pages-selection {
  flex: 1;
  max-width: 300px;
}

.pages-selection select {
  width: 100%;
  padding: 12px 15px;
  border-radius: 8px;
  border: 2px solid #ddd;
  font-size: 15px;
  transition: border-color 0.3s;
  background: white;
}

.pages-selection select:focus {
  outline: none;
  border-color: #42b983;
}

/* Next Button */
.next-button {
  background-color: #35495e;
  color: white;
  padding: 16px 40px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  width: 100%;
  max-width: 400px;
  margin: 20px auto 0;
  font-size: 18px;
  font-weight: 700;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(53, 73, 94, 0.3);
}

.next-button:hover:not(:disabled) {
  background-color: #2c3e50;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(53, 73, 94, 0.4);
}

.next-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  box-shadow: none;
  font-size: 14px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .upload-container {
    padding: 15px 10px 40px;
  }

  .main-title {
    font-size: 24px;
    margin: 5px 0 15px;
  }

  .upload-options {
    padding: 20px;
    gap: 15px;
    margin-bottom: 15px;
  }

  .template-mode-toggle {
    flex-direction: column;
    gap: 10px;
  }

  .mode-button {
    width: 100%;
  }

  .upload-label {
    max-width: 100%;
  }

  .pages-selection {
    max-width: 100%;
  }

  .next-button {
    max-width: 100%;
    font-size: 15px;
  }

  .template-preview img {
    max-height: 150px;
  }
}
</style>
