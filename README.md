<!-- Logo -->
<p align="center">
  <img src="assets/logo.png" alt="RAG Anki Kit: AI-Powered Literature Review & Knowledge Pipeline Logo" width="220"/>
</p>

# RAG Anki Kit: AI-Powered Literature Review & Knowledge Pipeline

[中文版说明请见 README.zh.md](README.zh.md)

---

## About This Project

<p align="center">
  <img src="assets/intro.png" alt="Project Introduction" width="400" height="400"/>
</p>

**RAG Anki Kit** is a comprehensive AI-powered research assistant that transforms your academic papers and documents into an intelligent knowledge pipeline. From advanced document ingestion to sophisticated knowledge graph generation, from semantic search to automated flashcard creation, this toolkit streamlines the entire research workflow with cutting-edge AI capabilities.

This project represents a journey into the exciting world of AI and natural language processing, featuring advanced entity optimization, incremental processing, and comprehensive analytics. Built with passion for learning and research efficiency, it integrates multiple cutting-edge technologies to create a seamless academic research experience with performance optimizations and modular architecture.

---

## ✨ Key Features

### 🔍 **Advanced RAG (Retrieval-Augmented Generation)**
- **Smart Document Processing**: Upload PDFs, Word docs, Excel files, Markdown, and HTML with advanced parsing
- **Flexible Chunking Strategies**: Sentence-based, paragraph-based, page-based, or custom length splitting
- **Intelligent Vector Database**: ChromaDB-powered semantic search with embedding optimization
- **Interactive Q&A**: Ask research questions and get contextual answers with source citations
- **Health Check Dashboard**: Real-time monitoring of document processing status and embedding coverage
- **Modular Architecture**: Optimized performance with component-based design and caching

### 📚 **Enhanced Literature Review Assistant**
- **AI-Powered Query Optimization**: Automatically improve research questions for better retrieval
- **Automated Summarization**: Generate comprehensive literature summaries from your document collection
- **Citation Management**: Automatic extraction and formatting of references
- **Research Gap Analysis**: Identify knowledge gaps and research opportunities
- **Relevance Filtering**: Configurable confidence thresholds for result quality
- **Multi-language Support**: Process documents in multiple languages with bilingual interface

### 🧠 **LitMap: Advanced Knowledge Graph Generation**
- **AI-Powered Entity & Relation Extraction**: GPT-4 powered extraction with 8 entity types and 8 relation types
- **Two-Phase Entity Optimization**: 
  - **Phase 1**: Linguistic normalization (always enabled) with abbreviation expansion and singularization
  - **Phase 2**: Semantic similarity detection using sentence transformers (optional)
- **Incremental Processing**: Smart chunk-by-chunk processing with progress tracking and state persistence
- **Advanced Processing Modes**: Full reprocessing, selective reprocessing, and incremental updates
- **Interactive Visualizations**: Dynamic network graphs with physics simulation and customizable layouts
- **Comprehensive Analytics Dashboard**: 
  - Entity influence scoring and centrality analysis
  - Most connected entities with detailed relationship analysis
  - Confidence metrics and processing statistics
- **Export Capabilities**: Save graphs in multiple formats (GEXF, GraphML, JSON, images)
- **Cost Estimation**: Real-time OpenAI API usage tracking

### 🎯 **Intelligent Anki Integration**
- **AI-Optimized Query Processing**: Automatic query enhancement for better card generation
- **Automated Flashcard Generation**: Create Q&A and cloze deletion cards from your research
- **Configurable Difficulty & Detail Levels**: Tailor card complexity to your learning needs
- **Advanced Card Preview**: Enhanced table display with text wrapping and scrolling
- **Batch Export**: Generate hundreds of cards in minutes with CSV download
- **Spaced Repetition Ready**: Seamlessly import into Anki for optimized learning

---

## 🛠 Tech Stack & Architecture

This project integrates modern AI and web technologies with advanced optimization:

- **🐍 Python**: Core backend logic with modular component architecture
- **🌊 Streamlit**: Interactive web application framework with custom styling
- **🤖 OpenAI API**: GPT-4 powered text analysis, summarization, and advanced entity extraction
- **📊 ChromaDB**: Vector database for semantic search and embeddings with intelligent caching
- **🧮 NumPy/Pandas**: Optimized data manipulation and analysis
- **🕸️ NetworkX**: Advanced graph analysis and knowledge network construction
- **📈 Plotly + Pyvis**: Interactive data visualizations, network graphs, and analytics dashboards
- **🔧 Sentence Transformers**: Optional semantic similarity for entity optimization
- **📄 PyMuPDF/Unstructured**: Advanced document parsing with multi-format support
- **⚡ Performance Optimizations**: Component caching, batch processing, and state management
- **🎨 CSS/HTML**: Custom responsive design with modern UI components
- **🌍 Multi-language**: Full bilingual interface (English/Chinese) with language-aware processing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mag233/rag-anki-kit.git
   cd rag-anki-kit
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your OpenAI API key:**
   ```bash
   # Create a .env file in the project root
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

4. **Launch the application:**
   ```bash
   streamlit run src/app.py
   ```

5. **Open your browser** and navigate to `http://localhost:8501`

---

## 📖 Usage Guide

### 1. **RAG Tab** - Document Processing & Intelligent Q&A
- **Project Management**: Create and switch between multiple research projects
- **File Upload**: Support for PDF, DOCX, Excel, Markdown, and HTML files
- **Smart Preprocessing**: Configure chunking strategy based on document type and research needs
- **Health Check Dashboard**: Monitor processing status, embedding coverage, and system health
- **Vector Database**: Generate embeddings with incremental updates and optimization
- **Intelligent Search**: Ask questions with AI-powered query optimization and get cited answers

### 2. **Literature Tab** - Advanced Research Synthesis
- **Query Enhancement**: AI-powered optimization of research questions for better retrieval
- **Comprehensive Reviews**: Generate literature reviews from multiple papers simultaneously
- **Citation Analysis**: Extract key findings, research trends, and bibliographic information
- **Relevance Control**: Configurable confidence thresholds for result quality
- **Export Options**: Formatted bibliographies and research summaries

### 3. **LitMap Tab** - Knowledge Graph Generation & Analytics
- **Step 1**: Select your processed project with health status indicators
- **Step 2**: Configure extraction settings with advanced optimization options:
  - Entity confidence thresholds and deduplication
  - Two-phase optimization (linguistic + semantic similarity)
  - Custom entity and relation types
  - Physics-enabled visualizations
- **Step 3**: Choose from 8 predefined entity types and 8 relation types, or add custom types
- **Step 4**: Generate knowledge graphs with multiple processing modes:
  - **Incremental**: Process only new chunks, preserving existing data
  - **Selective**: Reprocess selected chunks with merge capabilities
  - **Full Reprocess**: Complete regeneration from scratch
- **Step 5**: Explore interactive visualizations and comprehensive analytics:
  - Network graphs with physics simulation and customizable layouts
  - Entity influence scoring and centrality analysis
  - Most connected entities with relationship diversity metrics
  - Statistical dashboards with processing insights
- **Step 6**: Export in multiple formats (GEXF, GraphML, JSON, PNG)

### 4. **Anki Tab** - Intelligent Flashcard Creation
- **AI Query Optimization**: Enhance learning queries for better card generation
- **Configurable Generation**: Adjust difficulty, detail level, and card quantity
- **Advanced Preview**: Enhanced table display with text wrapping and comprehensive formatting
- **Multi-format Cards**: Generate Q&A and cloze deletion cards from your knowledge base
- **Batch Processing**: Create and export hundreds of cards efficiently
- **Direct Import**: Seamless CSV export for Anki integration

---

## 🏗 Project Structure

```
rag-anki-kit/
├── src/                      # Main source code with modular architecture
│   ├── app.py               # Main Streamlit application with optimized performance
│   ├── rag_tab.py           # Refactored RAG functionality with component architecture
│   ├── rag_components.py    # Modular UI components for better maintainability
│   ├── rag_utils.py         # Optimized utility classes with caching and connection management
│   ├── literature_tab.py    # Enhanced literature review with AI query optimization
│   ├── litmap_tab.py        # Advanced knowledge graph generation with state management
│   ├── anki_tab.py          # Intelligent flashcard generation with enhanced UI
│   ├── anki.py              # Core Anki card creation with AI optimization
│   ├── embed.py             # Optimized vector embedding and database operations
│   ├── literature.py        # Advanced literature analysis core functions
│   ├── preprocess.py        # Enhanced document parsing and chunking strategies
│   ├── retrieve.py          # Intelligent semantic search and retrieval logic
│   ├── summarize.py         # AI-powered text summarization functions
│   ├── format_template.py   # Advanced template formatting utilities
│   ├── lang_utils.py        # Comprehensive multi-language support utilities
│   ├── knowledge_graph/     # Advanced knowledge graph processing module
│   │   ├── __init__.py      # Module initialization
│   │   ├── config.yaml      # Comprehensive configuration for entity/relation types
│   │   ├── extractor.py     # Advanced AI-powered entity & relation extraction
│   │   ├── entity_optimizer.py # Two-phase entity optimization with semantic similarity
│   │   ├── graph_builder.py # NetworkX graph construction with advanced analytics
│   │   ├── visualizer.py    # Interactive visualizations & comprehensive analytics
│   │   ├── prompts/         # Optimized LLM prompt templates
│   │   │   ├── entity_extraction_improved.txt    # Enhanced entity extraction prompts
│   │   │   └── relation_extraction.txt  # Advanced relation extraction prompts
│   │   └── utils/           # Knowledge graph helper utilities
│   │       ├── __init__.py  # Utils module initialization
│   │       └── helpers.py   # Graph analysis and data processing helpers
│   ├── projects/            # User project data storage with organized structure
│   ├── experimental/        # Experimental features and advanced utilities
│   │   └── deep_clean.py    # Advanced data cleaning and processing tools
│   └── lib/                 # Frontend assets and external libraries
├── assets/                  # Project assets
│   ├── logo.png            # Application logo
│   └── intro.png           # Introduction image
├── lib/                    # External libraries and assets
├── .env                    # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation (English)
├── README.zh.md          # Project documentation (Chinese)
├── LITMAP_FEATURE_COMPLETE.md      # LitMap feature documentation
└── LITMAP_IMPLEMENTATION_SUMMARY.md # Implementation details
```

---

## ⚡ Performance & Technical Improvements

### Architecture Enhancements
- **Modular Component Design**: Separated UI components for better maintainability and performance
- **Intelligent Caching**: Multi-level caching for database connections, file operations, and computation results
- **State Management**: Persistent processing state with recovery capabilities and session management
- **Resource Optimization**: Connection pooling, memory management, and cleanup routines

### Processing Optimizations
- **Incremental Processing**: Smart chunk-by-chunk processing with state persistence
- **Batch Operations**: Efficient handling of large document collections
- **Progress Tracking**: Real-time progress monitoring with detailed processing statistics
- **Error Recovery**: Robust error handling with automatic retry mechanisms

### Knowledge Graph Innovations
- **Two-Phase Entity Optimization**: Linguistic normalization + optional semantic similarity
- **Advanced Analytics**: Entity influence scoring, centrality analysis, and relationship metrics
- **Custom Type Support**: User-defined entity and relation types for domain-specific research
- **Interactive Visualizations**: Physics-enabled network graphs with comprehensive dashboards

### User Experience Improvements
- **AI Query Enhancement**: Automatic optimization of research queries for better results
- **Health Monitoring**: Comprehensive system diagnostics and processing status
- **Enhanced UI Components**: Improved table displays, progress indicators, and responsive design
- **Cost Transparency**: Real-time API usage tracking and cost estimation

---

## 📊 Project Status

| Component | Status | Features |
|-----------|--------|----------|
| RAG Module | ✅ Complete | Modular architecture, intelligent caching, health monitoring |
| Literature Review | ✅ Complete | AI query optimization, advanced summarization, citation extraction |
| Knowledge Graphs | ✅ Complete | Two-phase optimization, incremental processing, advanced analytics |
| Entity Extraction | ✅ Complete | 8 entity types, improved normalization, semantic similarity |
| Relation Analysis | ✅ Complete | 8 relation types, confidence scoring, relationship analytics |
| Anki Integration | ✅ Complete | AI-enhanced generation, configurable difficulty, enhanced UI |
| Multi-language UI | ✅ Complete | Full bilingual interface with language-aware processing |
| Performance Optimization | ✅ Complete | Component caching, batch processing, state management |
| Advanced Analytics | ✅ Complete | Entity influence scoring, centrality analysis, statistical dashboards |
| Export Capabilities | ✅ Complete | Multiple formats (GEXF, GraphML, JSON, CSV, images) |
| Visualization Enhancement | 🌟 Wishlist | Advanced interactive dashboards, network layout algorithms |
| LLM Prompt Optimization | 🌟 Wishlist | Fine-tuned domain-specific prompts, adaptive extraction |
| OCR Support | 🌟 Wishlist | Optical character recognition for scanned documents and images |
| Enhanced PDF Processing | 🌟 Wishlist | Advanced table extraction, layout analysis, figure detection |
| API Integration | 🌟 Wishlist | REST API for external integrations, webhook support |

---

## 🤝 Contributing

I welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution:
- 🐛 Bug fixes and performance improvements
- 🎨 UI/UX enhancements and accessibility improvements
- 📚 Documentation improvements and tutorial creation
- 🔧 New features and integrations (OCR, enhanced PDF processing)
- 🌍 Additional language support and localization
- 🤖 LLM prompt optimization and domain-specific templates
- 📊 Advanced analytics and visualization improvements
- ⚡ Performance optimization and scalability enhancements
- 🔬 Research-specific feature development

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for their powerful GPT models and advanced language understanding
- The Streamlit team for their excellent framework and community support
- ChromaDB for robust vector database capabilities and semantic search
- NetworkX team for comprehensive graph analysis tools
- Sentence Transformers project for semantic similarity capabilities  
- The open-source community for inspiration, tools, and continuous improvement
- Research community for valuable feedback and feature suggestions

---

**Built with ❤️ for researchers, students, and lifelong learners**

*Questions? Feedback? Feel free to reach out via GitHub Issues or connect with me directly!*
