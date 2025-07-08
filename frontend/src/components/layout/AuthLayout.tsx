import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { BookOpen } from 'lucide-react'

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 to-purple-700 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20" />
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="mb-8">
            <Link to="/" className="flex items-center space-x-3">
              <BookOpen className="h-10 w-10" />
              <span className="text-2xl font-bold">Quiz Maker</span>
            </Link>
          </div>
          
          <h1 className="text-4xl font-bold mb-6">
            AI-Powered Quiz Generation for Educators
          </h1>
          
          <p className="text-xl text-blue-100 mb-8">
            Transform your lesson content into engaging quizzes with advanced AI technology. 
            Save time and create better assessments for your students.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span>Generate questions from any document</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span>Multiple question types and difficulty levels</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span>Export to PDF or share online</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span>Track student performance</span>
            </div>
          </div>
        </div>
        
        {/* Decorative elements */}
        <div className="absolute top-20 right-20 w-32 h-32 bg-white/10 rounded-full blur-xl" />
        <div className="absolute bottom-20 left-20 w-24 h-24 bg-purple-300/20 rounded-full blur-lg" />
      </div>
      
      {/* Right side - Auth forms */}
      <div className="flex-1 flex flex-col justify-center px-6 py-12 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="lg:hidden mb-8 text-center">
            <Link to="/" className="inline-flex items-center space-x-2">
              <BookOpen className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-gray-900">Quiz Maker</span>
            </Link>
          </div>
          
          <Outlet />
        </div>
      </div>
    </div>
  )
}
