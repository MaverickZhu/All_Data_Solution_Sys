import React, { useState } from 'react';
import { searchInProject } from '../services/api';
import Button from './Button';
import Input from './Input';
import Card from './Card';
import { MagnifyingGlassIcon } from '@heroicons/react/24/solid';


const ProjectSearch = ({ projectId }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const response = await searchInProject(projectId, query);
      setResults(response.data);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="语义检索">
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="在项目中搜索文档内容..."
          className="flex-grow"
        />
        <Button 
          type="submit" 
          disabled={loading}
          className="px-4 py-2 bg-gray-200 text-gray-800 font-semibold rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900"></div>
          ) : (
            <MagnifyingGlassIcon className="h-5 w-5" />
          )}
          <span>{loading ? '搜索中...' : '搜索'}</span>
        </Button>
      </form>

      {error && <p className="text-red-500">{error}</p>}

      <div className="mt-4 space-y-4">
        {results.length > 0 ? (
          results.map((result, index) => (
            <Card key={index} subtitle={`相似度: ${result.score.toFixed(4)}`}>
              <p className="text-gray-700 whitespace-pre-wrap">{result.text}</p>
              <div className="text-xs text-gray-400 mt-2">
                来自数据源 ID: {result.data_source_id}
              </div>
            </Card>
          ))
        ) : (
          !loading && <p className="text-gray-500">输入关键词以开始搜索。</p>
        )}
      </div>
    </Card>
  );
};

export default ProjectSearch; 