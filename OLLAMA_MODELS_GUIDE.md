# 🤖 Ollama Models for File Finding & Summarization

## 📋 Available Models Overview

Based on your Ollama installation, here are the models available for file analysis tasks:

### 1. **llama3.2:3b** 🏆 **RECOMMENDED**
- **Size**: 2.0 GB
- **Architecture**: Llama 3.2
- **Context Window**: 131,072 tokens (excellent for long file analysis)
- **Capabilities**: Text completion, tool calling
- **Best for**:
  - ✅ Complex file categorization
  - ✅ Detailed cleanup recommendations
  - ✅ Duplicate file analysis
  - ✅ Large document summarization
  - ✅ Pattern recognition in file systems

### 2. **tinyllama:1.1b** ⚡ **FAST OPTION**
- **Size**: 637 MB
- **Architecture**: Llama
- **Context Window**: 2,048 tokens (limited but sufficient for basic tasks)
- **Capabilities**: Text completion
- **Best for**:
  - ✅ Quick file type identification
  - ✅ Basic cleanup suggestions
  - ✅ Simple duplicate detection
  - ✅ Fast batch processing

### 3. **moondream:latest** 🔍 **SPECIALIZED**
- **Size**: 1.7 GB
- **Architecture**: Phi-2 with vision capabilities
- **Context Window**: 2,048 tokens
- **Capabilities**: Text completion, vision analysis
- **Best for**:
  - ✅ Image file analysis
  - ✅ Mixed content (documents with images)
  - ✅ Visual file type detection
  - ✅ Screenshot/file preview analysis

### 4. **granite-code:3b** 💻 **CODE SPECIALIST**
- **Size**: ~2.0 GB
- **Architecture**: Granite (IBM's code-focused model)
- **Context Window**: 2,000+ tokens
- **Capabilities**: Code understanding, completion, analysis
- **Best for**:
  - ✅ Programming file analysis
  - ✅ Code documentation generation
  - ✅ Configuration file parsing
  - ✅ Script and automation file review
  - ✅ Repository structure analysis
  - ✅ Dependency analysis

### 5. **nomic-embed-text:latest** 📊 **EMBEDDING MODEL**
- **Size**: 274 MB
- **Architecture**: Text embedding model
- **Capabilities**: Text embeddings for similarity search
- **Best for**:
  - ✅ Finding similar files
  - ✅ Content-based duplicate detection
  - ✅ Semantic file clustering
  - ✅ Advanced similarity analysis

## 🎯 Model Recommendations by Task

### **File Finding Tasks:**

| Task | Best Model | Why | Alternative |
|------|------------|-----|-------------|
| **Find duplicates** | llama3.2:3b | Excellent reasoning for content analysis | nomic-embed-text |
| **Categorize files** | llama3.2:3b | Large context for detailed analysis | tinyllama |
| **Find old files** | tinyllama | Fast processing of metadata | llama3.2:3b |
| **Find large files** | tinyllama | Quick size-based analysis | Any model |
| **Find temp files** | tinyllama | Pattern matching for temp files | llama3.2:3b |

### **File Summarization Tasks:**

| Task | Best Model | Why | Alternative |
|------|------------|-----|-------------|
| **Document summary** | llama3.2:3b | Large context for comprehensive summaries | moondream |
| **Code file analysis** | granite-code:3b | Specialized for code understanding | llama3.2:3b |
| **Log file analysis** | llama3.2:3b | Pattern recognition in logs | tinyllama |
| **Image content** | moondream | Vision capabilities for images | llama3.2:3b |
| **Config files** | granite-code:3b | Excellent at parsing configurations | llama3.2:3b |
| **Batch processing** | tinyllama | Fast processing of multiple files | llama3.2:3b |

## 🚀 Usage Examples

### **Basic File Analysis:**
```bash
# Using llama3.2:3b (recommended)
curl -X POST http://127.0.0.1:5000/api/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze this file: /Users/john/Documents/report.pdf (2.5MB, modified 2024-01-15). Should I keep or delete it?", "model": "llama3.2:3b"}'
```

### **Batch File Processing:**
```bash
# Using tinyllama for speed
curl -X POST http://127.0.0.1:5000/api/ollama/analyze-files \
  -H "Content-Type: application/json" \
  -d '{"files": ["/tmp/cache.db", "/Users/john/Downloads/temp.exe"], "model": "tinyllama:1.1b"}'
```

### **Code File Analysis:**
```bash
# Using granite-code for programming files
curl -X POST http://127.0.0.1:5000/api/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze this Python script for potential cleanup", "model": "granite-code:3b"}'
```

### **Duplicate Analysis:**
```bash
# Using nomic-embed-text for similarity
curl -X POST http://127.0.0.1:5000/api/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "These files appear to be duplicates. Which should I keep?", "model": "nomic-embed-text:latest"}'
```

## ⚡ Performance Comparison

| Model | Speed | Quality | Context | Best Use Case |
|-------|-------|---------|---------|---------------|
| llama3.2:3b | Medium | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Complex analysis |
| granite-code:3b | Medium | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Code analysis |
| tinyllama:1.1b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Quick tasks |
| moondream:latest | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐ | Visual content |
| nomic-embed-text | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Similarity search |

## 🔧 Integration with TidyMe

### **Current Integration:**
- ✅ Ollama chat endpoint: `/api/ollama/chat`
- ✅ File analysis endpoint: `/api/ollama/analyze-files`
- ✅ Report generation: `/api/ollama/generate-report`
- ✅ Model selection support

### **Recommended Workflow:**

1. **Initial Scan**: Use `tinyllama:1.1b` for fast file categorization
2. **Code Files**: Use `granite-code:3b` for programming and config files
3. **Detailed Analysis**: Use `llama3.2:3b` for complex documents
4. **Content Similarity**: Use `nomic-embed-text:latest` for duplicates
5. **Visual Files**: Use `moondream:latest` for images/documents

## 📊 Expected Performance (After Download Completes)

### **File Analysis Speed:**
- **tinyllama:1.1b**: ~2-3 seconds per file
- **granite-code:3b**: ~4-6 seconds per file
- **llama3.2:3b**: ~5-8 seconds per file
- **moondream:latest**: ~3-5 seconds per file
- **nomic-embed-text**: ~1-2 seconds per file

### **Batch Processing:**
- **Small batches (10 files)**: 30-60 seconds
- **Medium batches (50 files)**: 2-5 minutes
- **Large batches (100+ files)**: 5-15 minutes

## 🎯 Best Practices

### **For File Finding:**
1. Start with `tinyllama` for initial categorization
2. Use `llama3.2:3b` for files requiring detailed analysis
3. Reserve `moondream` for visual content
4. Use `nomic-embed-text` for content-based duplicate detection

### **For File Summarization:**
1. Use `granite-code:3b` for code and configuration files
2. Use `llama3.2:3b` for comprehensive document summaries
3. Use `tinyllama` for quick overviews
4. Use `moondream` for documents with images/charts
5. Combine models for multi-stage analysis

### **Performance Optimization:**
1. **Batch similar files together** (all documents, all images, etc.)
2. **Use appropriate model size** for task complexity
3. **Cache results** for frequently analyzed files
4. **Process in background** using TidyMe's task system

## 🚨 Current Status

**Models are currently downloading in the background.** Once complete:

1. **llama3.2:3b** will be your primary model for complex analysis
2. **granite-code:3b** will be your specialist for code and config files
3. **tinyllama:1.1b** will be ready for quick tasks
4. **moondream:latest** will handle visual content
5. **nomic-embed-text:latest** will enable advanced similarity detection

## 🔄 Next Steps

1. **Wait for downloads to complete** (check with `ollama list`)
2. **Test each model** with sample files
3. **Configure TidyMe** to use appropriate models for different tasks
4. **Set up automated workflows** using the task dependency system

---

**🎯 TL;DR: Use `llama3.2:3b` for most file analysis tasks. It's the best balance of speed, quality, and capabilities.**