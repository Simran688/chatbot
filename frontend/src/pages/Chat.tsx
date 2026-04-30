import { useState, useRef, useEffect } from 'react'
import { useChat } from '../contexts/ChatContext'
import { Send, Bot, User, Globe, FileText, Loader2, Trash2 } from 'lucide-react'

export default function Chat() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const message = input.trim()
    setInput('')
    await sendMessage(message)
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between bg-white">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
          <p className="text-sm text-gray-500">Ask about policies or general questions</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-gray-500 hover:text-red-600 transition-colors"
            title="Clear chat"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <Bot className="w-12 h-12 mx-auto mb-4 text-primary-400" />
            <p className="text-lg font-medium">Welcome to Policy Assistant</p>
            <p className="mt-2">Ask me about company policies or any general question.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              message.role === 'user' ? 'bg-primary-100' : 'bg-gray-200'
            }`}>
              {message.role === 'user' ? (
                <User className="w-4 h-4 text-primary-600" />
              ) : (
                <Bot className="w-4 h-4 text-gray-600" />
              )}
            </div>

            <div className={`max-w-[80%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}>
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>

              {/* Sources */}
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-medium text-gray-500 flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    Sources
                  </p>
                  {message.sources.slice(0, 3).map((source, idx) => (
                    <div key={idx} className="text-xs text-gray-600 bg-gray-100 p-2 rounded">
                      <span className="font-medium">{source.document}</span>
                      <span className="text-gray-400 mx-1">•</span>
                      <span className="text-gray-500">{source.text.substring(0, 100)}...</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Web Search Indicator */}
              {message.usedWebSearch && (
                <div className="mt-1 flex items-center gap-1 text-xs text-blue-600">
                  <Globe className="w-3 h-3" />
                  <span>Web search used</span>
                </div>
              )}

              {/* Query Type */}
              {message.queryType && (
                <div className="mt-1 text-xs text-gray-400">
                  {message.queryType === 'internal' ? 'Document search' : 'General knowledge'}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <Bot className="w-4 h-4 text-gray-600" />
            </div>
            <div className="bg-white border border-gray-200 p-3 rounded-lg">
              <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
