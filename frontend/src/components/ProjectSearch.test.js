import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProjectSearch from './ProjectSearch';
import * as api from '../services/api';

// Mock the api service
jest.mock('../services/api');

describe('ProjectSearch Component', () => {
  const projectId = '123';

  it('renders correctly', () => {
    render(<ProjectSearch projectId={projectId} />);
    expect(screen.getByPlaceholderText('在项目中搜索文档内容...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /搜索/i })).toBeInTheDocument();
  });

  it('handles user input', () => {
    render(<ProjectSearch projectId={projectId} />);
    const input = screen.getByPlaceholderText('在项目中搜索文档内容...');
    fireEvent.change(input, { target: { value: 'test query' } });
    expect(input.value).toBe('test query');
  });

  it('calls search api and displays results on success', async () => {
    const mockResults = [
      { text: 'First result text.', score: 0.9, data_source_id: 1 },
      { text: 'Second result text.', score: 0.8, data_source_id: 2 },
    ];
    api.searchInProject.mockResolvedValue({ data: mockResults });

    render(<ProjectSearch projectId={projectId} />);
    
    const input = screen.getByPlaceholderText('在项目中搜索文档内容...');
    fireEvent.change(input, { target: { value: 'test query' } });

    const searchButton = screen.getByRole('button', { name: /搜索/i });
    fireEvent.click(searchButton);

    // Check for loading state
    expect(screen.getByText('搜索中...')).toBeInTheDocument();

    // Wait for results to be displayed
    await waitFor(() => {
      expect(screen.getByText('First result text.')).toBeInTheDocument();
      expect(screen.getByText('Second result text.')).toBeInTheDocument();
    });

    // Verify API was called
    expect(api.searchInProject).toHaveBeenCalledWith(projectId, 'test query');
  });

  it('displays an error message on api failure', async () => {
    api.searchInProject.mockRejectedValue(new Error('API Error'));

    render(<ProjectSearch projectId={projectId} />);
    
    const input = screen.getByPlaceholderText('在项目中搜索文档内容...');
    fireEvent.change(input, { target: { value: 'error query' } });

    const searchButton = screen.getByRole('button', { name: /搜索/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Search failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('does not call api if query is empty', () => {
    render(<ProjectSearch projectId={projectId} />);
    const searchButton = screen.getByRole('button', { name: /搜索/i });
    fireEvent.click(searchButton);

    expect(api.searchInProject).not.toHaveBeenCalled();
  });
}); 