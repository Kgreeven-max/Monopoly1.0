// React Component Template
// Copy this template when creating new React components

import React, { useState, useEffect } from 'react'
import { ComponentProps } from '@/types'

// Define component props interface
interface ComponentTemplateProps {
  // Add props here
  title: string
  data?: any[]
  onAction?: (data: any) => void
  className?: string
}

// Main component
export const ComponentTemplate: React.FC<ComponentTemplateProps> = ({
  title,
  data = [],
  onAction,
  className = ''
}) => {
  // State management
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Effects
  useEffect(() => {
    // Component initialization logic
  }, [])
  
  // Event handlers
  const handleAction = (actionData: any) => {
    try {
      setLoading(true)
      setError(null)
      
      // Action logic here
      onAction?.(actionData)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }
  
  // Render helpers
  const renderContent = () => {
    if (loading) {
      return <div className="animate-spin">Loading...</div>
    }
    
    if (error) {
      return (
        <div className="text-red-500 p-4 border border-red-300 rounded">
          Error: {error}
        </div>
      )
    }
    
    return (
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index} className="p-2 border rounded">
            {/* Render item content */}
          </div>
        ))}
      </div>
    )
  }
  
  // Main render
  return (
    <div className={`component-template ${className}`}>
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      {renderContent()}
      
      <button
        onClick={() => handleAction({})}
        disabled={loading}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Action'}
      </button>
    </div>
  )
}

// Export default component
export default ComponentTemplate

// Example usage:
// import { ComponentTemplate } from '@/components/ComponentTemplate'
//
// const MyPage = () => {
//   const handleAction = (data: any) => {
//     console.log('Action performed:', data)
//   }
//
//   return (
//     <ComponentTemplate
//       title="My Component"
//       data={[{ id: 1, name: 'Item 1' }]}
//       onAction={handleAction}
//     />
//   )
// }