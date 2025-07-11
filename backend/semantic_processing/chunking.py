import nltk

# 确保 'punkt' 数据集已经下载
# 在 Dockerfile 中我们已经通过 nltk.download('punkt') 完成了这一步
# 如果在本地非 Docker 环境运行，需要确保已执行过一次下载
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Downloading 'punkt' tokenizer data...")
    nltk.download('punkt', quiet=True)

def chunk_text_by_sentence(text: str) -> list[str]:
    """
    将文本按句子分割成块。

    Args:
        text: 需要分割的文本。

    Returns:
        一个由句子字符串组成的列表。
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # 使用 NLTK 的句子分词器
    sentences = nltk.sent_tokenize(text)
    
    # 返回非空的句子列表
    return [sentence.strip() for sentence in sentences if sentence.strip()] 