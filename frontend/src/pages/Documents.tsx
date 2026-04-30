import { useState, useEffect, useRef } from 'react'
import api from '../lib/api'
import { Document, DocumentUploadResponse } from '../types'
import { Upload, FileText, Trash2, RefreshCw, Loader2, CheckCircle, XCircle } from 'lucide-react'

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/v1/documents/')
      setDocuments(response.data.documents)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(`Uploading ${file.name}...`)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post<DocumentUploadResponse>('/api/v1/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setUploadProgress(`Created ${response.data.chunks_created} chunks from ${file.name}`)
      fetchDocuments()
      
      setTimeout(() => setUploadProgress(''), 3000)
    } catch (error: any) {
      setUploadProgress(`Error: ${error.response?.data?.detail || 'Upload failed'}`)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await api.delete(`/api/v1/documents/${id}`)
      fetchDocuments()
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getStatusIcon = (isProcessed: number) => {
    switch (isProcessed) {
      case 1:
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 2:
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />
    }
  }

  const getStatusText = (isProcessed: number) => {
    switch (isProcessed) {
      case 1:
        return 'Processed'
      case 2:
        return 'Error'
      default:
        return 'Processing...'
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Documents</h2>
          <p className="text-gray-600">Manage uploaded documents for RAG</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchDocuments()}
            disabled={isLoading}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            Upload Document
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      </div>

      {uploadProgress && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${
          uploadProgress.includes('Error') 
            ? 'bg-red-50 text-red-600' 
            : 'bg-blue-50 text-blue-600'
        }`}>
          {uploadProgress}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600">No documents uploaded yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Upload PDF, DOCX, or TXT files to get started
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Size</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Date</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">{doc.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 uppercase">{doc.file_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{formatFileSize(doc.file_size)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(doc.is_processed)}
                      <span className="text-sm text-gray-600">{getStatusText(doc.is_processed)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
