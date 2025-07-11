"""
LlamaIndex 使用示例
演示如何使用LlamaIndex构建简单的RAG应用
"""
import os
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

def basic_example():
    """基本使用示例"""
    print("📚 LlamaIndex 基本示例")
    print("-" * 40)
    
    # 创建文档
    documents = [
        Document(text="人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"),
        Document(text="机器学习是人工智能的一个子集，它使计算机能够从数据中学习，而无需明确编程。"),
        Document(text="深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的复杂模式。"),
        Document(text="自然语言处理（NLP）是人工智能的一个分支，专注于使计算机能够理解、解释和生成人类语言。"),
    ]
    
    # 使用模拟模型（不需要API密钥）
    Settings.embed_model = MockEmbedding(embed_dim=384)
    Settings.llm = MockLLM()
    
    # 创建索引
    print("🔧 创建向量索引...")
    index = VectorStoreIndex.from_documents(documents)
    print("✅ 索引创建成功！")
    
    # 创建查询引擎
    query_engine = index.as_query_engine()
    
    # 测试查询
    queries = [
        "什么是人工智能？",
        "机器学习和深度学习有什么关系？",
        "NLP是什么？"
    ]
    
    print("\n🔍 测试查询:")
    for query in queries:
        print(f"\n问题: {query}")
        # 注意：使用MockLLM时，响应是模拟的
        response = query_engine.query(query)
        print(f"回答: {response}")

def advanced_example():
    """高级示例：使用实际的嵌入模型"""
    print("\n\n🚀 LlamaIndex 高级示例")
    print("-" * 40)
    
    # 如果要使用OpenAI
    # os.environ['OPENAI_API_KEY'] = 'your-api-key'
    # from llama_index.llms.openai import OpenAI
    # from llama_index.embeddings.openai import OpenAIEmbedding
    # Settings.llm = OpenAI(model="gpt-3.5-turbo")
    # Settings.embed_model = OpenAIEmbedding()
    
    # 使用本地嵌入模型
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        print("🔧 加载本地嵌入模型...")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # 创建更复杂的文档
        documents = [
            Document(
                text="LlamaIndex是一个数据框架，用于构建LLM应用程序。它提供了数据连接器、索引结构、查询接口等功能。",
                metadata={"source": "documentation", "category": "framework"}
            ),
            Document(
                text="RAG（检索增强生成）是一种结合检索和生成的技术，可以提高LLM回答的准确性和相关性。",
                metadata={"source": "tutorial", "category": "technique"}
            ),
        ]
        
        # 创建索引
        index = VectorStoreIndex.from_documents(documents)
        
        # 配置查询参数
        query_engine = index.as_query_engine(
            similarity_top_k=2,  # 返回最相似的2个节点
            response_mode="compact"  # 紧凑的响应模式
        )
        
        print("✅ 高级索引创建成功！")
        print("\n📝 文档元数据示例:")
        for doc in documents:
            print(f"  - {doc.metadata}")
            
    except Exception as e:
        print(f"⚠️ 高级示例需要额外配置: {e}")

def save_and_load_example():
    """持久化示例"""
    print("\n\n💾 索引持久化示例")
    print("-" * 40)
    
    # 使用模拟模型
    Settings.embed_model = MockEmbedding(embed_dim=384)
    Settings.llm = MockLLM()
    
    # 创建并保存索引
    documents = [Document(text="这是一个持久化测试文档")]
    index = VectorStoreIndex.from_documents(documents)
    
    # 保存索引
    print("💾 保存索引到磁盘...")
    index.storage_context.persist(persist_dir="./storage")
    print("✅ 索引已保存！")
    
    # 加载索引
    print("\n📂 从磁盘加载索引...")
    from llama_index.core import StorageContext, load_index_from_storage
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    loaded_index = load_index_from_storage(storage_context)
    print("✅ 索引加载成功！")

if __name__ == "__main__":
    # 运行示例
    basic_example()
    advanced_example()
    save_and_load_example()
    
    print("\n\n🎉 所有示例运行完成！")
    print("\n💡 提示:")
    print("1. 生产环境中，建议使用真实的LLM和嵌入模型")
    print("2. 可以集成向量数据库（如Milvus）来存储大规模数据")
    print("3. 查看官方文档了解更多高级功能：https://docs.llamaindex.ai/") 