<template>
  <!-- Upload form -->
  <div class="upload-container">
    <div class="upload-options">
      <!-- Row 1: Template Selection Mode Toggle -->
      <div class="template-mode-toggle">
        <button
          @click="useCustomTemplate = true"
          :class="{'active': useCustomTemplate}"
          class="mode-button">
          📤 Upload Custom Template
        </button>
        <button
          @click="useCustomTemplate = false"
          :class="{'active': !useCustomTemplate}"
          class="mode-button">
          📁 Use Built-in Template
        </button>
      </div>

      <!-- Row 2: Template Selection (conditional) -->
      <div v-if="!useCustomTemplate" class="template-selection">
        <label class="section-label">Select a Template:</label>
        <select v-model="selectedTemplate" class="template-selector">
          <option value="" disabled>-- Choose a template --</option>
          <option
            v-for="template in availableTemplates"
            :key="template.name"
            :value="template.name">
            {{ template.name }}
            <span v-if="template.description"> - {{ truncate(template.description, 50) }}</span>
          </option>
        </select>

        <!-- Template Preview -->
        <div v-if="selectedTemplate && getTemplateInfo(selectedTemplate)" class="template-info">
          <div class="template-description">
            <strong>{{ selectedTemplate }}</strong>: {{ getTemplateInfo(selectedTemplate).description }}
          </div>
          <div v-if="getTemplateInfo(selectedTemplate).has_preview" class="template-preview">
            <img
              :src="`/api/template-preview/${selectedTemplate}`"
              :alt="`${selectedTemplate} preview`"
              @error="handleImageError" />
          </div>
          <div v-else class="no-preview">
            <span>📄 No preview available</span>
          </div>
        </div>
      </div>

      <!-- Row 3: Custom PPTX Upload (conditional) -->
      <div v-if="useCustomTemplate" class="upload-buttons">
        <div class="upload-section">
          <label for="pptx-upload" class="upload-label">
            Upload PPTX Template
            <span v-if="pptxFile" class="uploaded-symbol">✔️</span>
          </label>
          <input
            type="file"
            id="pptx-upload"
            @change="handleFileUpload($event, 'pptx')"
            accept=".pptx" />
        </div>
      </div>

      <!-- Row 4: PDF Upload (always shown) -->
      <div class="upload-section pdf-upload">
        <label for="pdf-upload" class="upload-label">
          Upload PDF Content
          <span v-if="pdfFile" class="uploaded-symbol">✔️</span>
        </label>
        <input
          type="file"
          id="pdf-upload"
          @change="handleFileUpload($event, 'pdf')"
          accept=".pdf" />
      </div>

      <!-- Row 5: Page Count Selection -->
      <div class="selectors">
        <div class="pages-selection">
          <label class="section-label">Number of Pages:</label>
          <select v-model="selectedPages">
            <option :value="null">Auto (Dynamic)</option>
            <option v-for="page in pagesOptions" :key="page" :value="page">
              {{ page }} pages
            </option>
          </select>
        </div>
      </div>

      <!-- Row 6: Submit Button -->
      <button @click="goToGenerate" class="next-button" :disabled="!canSubmit">
        {{ canSubmit ? 'Generate Presentation' : 'Please complete all required fields' }}
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
        alert('Backend is not running or too busy. Your task will not be processed.');
        return;
      }

      // Validation
      if (!this.canSubmit) {
        if (!this.pdfFile) {
          alert('Please upload a PDF file.');
        } else if (this.useCustomTemplate && !this.pptxFile) {
          alert('Please upload a PPTX template file.');
        } else if (!this.useCustomTemplate && !this.selectedTemplate) {
          alert('Please select a template.');
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
        alert(`Failed to upload files: ${error.response?.data?.detail || error.message}`);
      }
    }
  }
}
</script>

<style scoped>
.upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  padding: 40px 20px;
  box-sizing: border-box;
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 25px;
  width: 100%;
  max-width: 800px;
  background: white;
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
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
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #eee;
}

.template-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
  line-height: 1.5;
}

.template-preview {
  margin-top: 10px;
  text-align: center;
}

.template-preview img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  .upload-options {
    padding: 25px;
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
    font-size: 16px;
  }
}
</style>
