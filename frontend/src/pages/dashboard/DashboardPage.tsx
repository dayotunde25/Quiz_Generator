import React from 'react'
import { Link } from 'react-router-dom'
import { Plus, FileText, Upload, BarChart3 } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here's what's happening with your quizzes today.
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <Link
          to="/dashboard/quizzes/create"
          className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg shadow-soft hover:shadow-medium transition-shadow"
        >
          <div>
            <span className="rounded-lg inline-flex p-3 bg-primary-50 text-primary-600 ring-4 ring-white">
              <Plus className="h-6 w-6" />
            </span>
          </div>
          <div className="mt-4">
            <h3 className="text-lg font-medium text-gray-900">
              Create Quiz
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Generate a new quiz from text or documents
            </p>
          </div>
        </Link>

        <Link
          to="/dashboard/quizzes"
          className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg shadow-soft hover:shadow-medium transition-shadow"
        >
          <div>
            <span className="rounded-lg inline-flex p-3 bg-blue-50 text-blue-600 ring-4 ring-white">
              <FileText className="h-6 w-6" />
            </span>
          </div>
          <div className="mt-4">
            <h3 className="text-lg font-medium text-gray-900">
              My Quizzes
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              View and manage your created quizzes
            </p>
          </div>
        </Link>

        <Link
          to="/dashboard/files"
          className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg shadow-soft hover:shadow-medium transition-shadow"
        >
          <div>
            <span className="rounded-lg inline-flex p-3 bg-green-50 text-green-600 ring-4 ring-white">
              <Upload className="h-6 w-6" />
            </span>
          </div>
          <div className="mt-4">
            <h3 className="text-lg font-medium text-gray-900">
              Files
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Manage your uploaded documents
            </p>
          </div>
        </Link>

        <Link
          to="/dashboard/analytics"
          className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg shadow-soft hover:shadow-medium transition-shadow"
        >
          <div>
            <span className="rounded-lg inline-flex p-3 bg-purple-50 text-purple-600 ring-4 ring-white">
              <BarChart3 className="h-6 w-6" />
            </span>
          </div>
          <div className="mt-4">
            <h3 className="text-lg font-medium text-gray-900">
              Analytics
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              View quiz performance and insights
            </p>
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-8">
        <div className="bg-white overflow-hidden shadow-soft rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Quizzes
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">0</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-soft rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Upload className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Files Uploaded
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">0</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-soft rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    This Month
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {user?.quiz_count_current_month || 0} / {user?.subscription_plan === 'free' ? '5' : '∞'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent activity placeholder */}
      <div className="bg-white shadow-soft rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Activity
          </h3>
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No quizzes yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first quiz.
            </p>
            <div className="mt-6">
              <Link
                to="/dashboard/quizzes/create"
                className="btn-primary"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Quiz
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
