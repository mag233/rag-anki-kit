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

**RAG Anki Kit** is a comprehensive AI-powered research assistant that transforms your academic papers and documents into an intelligent knowledge pipeline. From document ingestion to knowledge graph generation, from semantic search to automated flashcard creation, this toolkit streamlines the entire research workflow.

This project represents my journey from a non-CS background into the exciting world of AI and natural language processing. Built with passion for learning and research efficiency, it integrates multiple cutting-edge technologies to create a seamless academic research experience.

---

## Key Features

### RAG (Retrieval-Augmented Generation)
- **Smart Document Processing**: Upload PDFs, Word docs, Excel files, Markdown, and HTML
- **Flexible Chunking Strategies**: Sentence-based, paragraph-based, page-based, or custom length splitting
- **Semantic Search**: Vector embeddings powered by ChromaDB for intelligent document retrieval
- **Interactive Q&A**: Ask research questions and get contextual answers with source citations

### Literature Review Assistant
- **Automated Summarization**: Generate comprehensive literature summaries from your document collection
- **Citation Management**: Automatic extraction and formatting of references
- **Research Gap Analysis**: Identify knowledge gaps and research opportunities
- **Multi-language Support**: Process documents in multiple languages

### LitMap: Knowledge Graph Generation
- **Entity & Relation Extraction**: AI-powered extraction of research entities and their relationships
- **Interactive Visualizations**: Dynamic network graphs with customizable layouts
- **Research Analytics Dashboard**: Statistical insights into your knowledge base
- **Export Capabilities**: Save graphs in multiple formats (JSON, GraphML, images)

### Anki Integration
- **Automated Flashcard Generation**: Create Q&A and cloze deletion cards from your research
- **Customizable Templates**: Tailor card formats to your learning style
- **Batch Export**: Generate hundreds of cards in minutes
- **Spaced Repetition Ready**: Seamlessly import into Anki for optimized learning

---

## Tech Stack & Architecture

This project integrates modern AI and web technologies:

- **Python**: Core backend logic and data processing
- **Streamlit**: Interactive web application framework
- **OpenAI API**: GPT-powered text analysis, summarization, and extraction
- **ChromaDB**: Vector database for semantic search and embeddings
- **NetworkX**: Graph analysis and knowledge network construction
- **Plotly**: Interactive data visualizations and analytics dashboards
- **PyMuPDF/Unstructured**: Advanced document parsing and processing
- **NumPy/Pandas**: Data manipulation and analysis
- **CSS/HTML**: Custom styling and responsive design

---

## Quick Start

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

## Usage Guide

### 1. RAG Tab - Document Processing & Q&A
- Upload your research documents (PDF, DOCX, etc.)
- Configure chunking strategy based on your needs
- Generate embeddings and build your vector database
- Ask questions and get AI-powered answers with citations

### 2. Literature Tab - Research Synthesis
- Generate comprehensive literature reviews
- Analyze multiple papers simultaneously
- Extract key findings and research trends
- Export formatted bibliographies

### 3. LitMap Tab - Knowledge Graph Generation
- **Step 1**: Select your processed project
- **Step 2**: Configure extraction settings (confidence thresholds, entity types)
- **Step 3**: Choose entity and relation types to extract
- **Step 4**: Generate the knowledge graph with real-time progress tracking
- **Step 5**: Explore interactive visualizations and analytics
- **Step 6**: Export your knowledge graph in various formats

### 4. Anki Tab - Flashcard Creation
- Generate study cards from your knowledge base
- Customize question and answer formats
- Export directly to Anki for spaced repetition learning

---

## Project Structure

```
rag-anki-kit/
├── src/                      # Main source code
│   ├── app.py               # Main Streamlit application entry point
│   ├── rag_tab.py           # Document processing & RAG functionality
│   ├── rag_components.py    # Modular UI components for RAG features
│   ├── rag_utils.py         # RAG utility classes and helper functions
│   ├── literature_tab.py    # Literature review and summarization features
│   ├── literature.py        # Literature analysis core functions
│   ├── litmap_tab.py        # Knowledge graph generation UI interface
│   ├── litmap.py            # Knowledge graph core functionality
│   ├── anki_tab.py          # Flashcard generation and export
│   ├── anki.py              # Core Anki card creation logic
│   ├── document_processing.py # Advanced document processing pipeline
│   ├── improved_document_processing.py # Enhanced processing with optimizations
│   ├── preprocess.py        # Document parsing and chunking
│   ├── processing_config.py # Processing configuration and settings
│   ├── embed.py             # Vector embedding and database operations
│   ├── retrieve.py          # Semantic search and retrieval logic
│   ├── summarize.py         # Text summarization functions
│   ├── format_template.py   # Template formatting utilities
│   ├── lang_utils.py        # Multi-language support utilities
│   ├── ui_config.py         # UI configuration and styling
│   ├── knowledge_graph/     # Knowledge graph processing module
│   │   ├── __init__.py      # Module initialization
│   │   ├── config.yaml      # Configuration for entity/relation types
│   │   ├── extractor.py     # AI-powered entity & relation extraction
│   │   ├── graph_builder.py # NetworkX graph construction and analysis
│   │   ├── visualizer.py    # Interactive graph visualizations & analytics
│   │   ├── entity_optimizer.py # Entity optimization and deduplication
│   │   ├── prompts/         # LLM prompt templates
│   │   │   ├── entity_extraction_improved.txt # Enhanced entity extraction
│   │   │   └── relation_extraction.txt # Relation extraction prompts
│   │   └── utils/           # Knowledge graph helper utilities
│   │       ├── __init__.py  # Utils module initialization
│   │       └── helpers.py   # Graph analysis and data processing helpers
│   ├── experimental/        # Experimental features and utilities
│   │   └── deep_clean.py    # Advanced data cleaning tools
│   └── projects/            # User project data storage
│       ├── [project_name]/  # Individual project directories
│       │   ├── raw_pdfs/    # Original uploaded documents
│       │   ├── processed/   # Processed document chunks and metadata
│       │   │   ├── chunks/  # Document chunk files (.json)
│       │   │   └── manifest.json # Processing metadata and file tracking
│       │   ├── vectorstore/ # Vector database storage (ChromaDB)
│       │   ├── litmap/      # Knowledge graph data (entities, relations)
│       │   └── anki_cards/  # Generated Anki flashcards (.csv)
├── assets/                  # Project assets
│   ├── logo.png            # Application logo
│   └── intro.png           # Introduction image
├── lib/                    # External frontend libraries and assets
│   ├── bindings/           # JavaScript utility bindings
│   ├── tom-select/         # Multi-select component library
│   └── vis-9.1.2/          # Network visualization library
├── .env                    # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation (English)
└── README.zh.md          # Project documentation (Chinese)
```

---

## Advanced Features

### Knowledge Graph Analytics
- **Centrality Analysis**: Identify the most important entities in your research domain
- **Community Detection**: Discover research clusters and thematic groups
- **Temporal Analysis**: Track how knowledge evolves across different papers
- **Gap Analysis**: Find underexplored connections and research opportunities

### Customization Options
- **Custom Entity Types**: Define domain-specific entities for extraction
- **Template System**: Modify AI prompts for different research domains
- **Export Formats**: Multiple output formats for different use cases
- **Language Support**: Full bilingual interface (English/Chinese)

### Performance Features
- **Batch Processing**: Handle large document collections efficiently
- **Progress Tracking**: Real-time updates on processing status
- **Cost Estimation**: Monitor OpenAI API usage and costs
- **Error Recovery**: Robust handling of processing failures

---

## Project Status

| Component | Status | Features |
|-----------|--------|----------|
| RAG Module | Complete | Document processing, semantic search, Q&A |
| Literature Review | Complete | Summarization, citation extraction |
| Knowledge Graphs | Complete | Entity extraction, graph visualization, analytics |
| Anki Integration | Complete | Automated card generation, batch export |
| Multi-language UI | Complete | English/Chinese interface |
| Visualization Optimization | Wishlist | Enhanced charts, interactive dashboards, analytics |
| LLM Prompt Control | Wishlist | Optimized prompts, configurable templates, fine-tuned extraction |
| OCR Support | Wishlist | Optical character recognition for scanned documents and images |
| Enhanced PDF Processing | Wishlist | Advanced PDF parsing, table extraction, layout analysis |

---

## Contributing

I welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution:
- Bug fixes and performance improvements
- UI/UX enhancements
- Documentation improvements
- New features and integrations
- Additional language support

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- OpenAI for their powerful GPT models
- The Streamlit team for their excellent framework
- ChromaDB for vector database capabilities
- The open-source community for inspiration and tools

---

**Built with care for researchers, students, and lifelong learners**

*Questions? Feedback? Feel free to reach out via GitHub Issues or connect with me directly!*
