'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  MapPin,
  Star,
  Users,
} from 'lucide-react'

const quickSearchOptions = [
  { label: 'AI Tools', value: 'ai', category: 'ai-ml' },
  { label: 'Design Tools', value: 'design', category: 'design' },
  { label: 'Dev Tools', value: 'development', category: 'development' },
  { label: 'Productivity', value: 'productivity', category: 'productivity' },
  { label: 'Marketing Tools', value: 'marketing', category: 'marketing' },
  { label: 'Analytics', value: 'analytics', category: 'data-analytics' },
]

export function HeroSection() {
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()

    const params = new URLSearchParams()
    if (searchQuery) params.set('q', searchQuery)

    router.push(`/search?${params.toString()}`)
  }

  const handleQuickSearch = (option: typeof quickSearchOptions[0]) => {
    const params = new URLSearchParams()
    params.set('q', option.value)

    router.push(`/search?${params.toString()}`)
  }

  return (
    <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 min-h-[600px] flex items-center">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[url('/pattern.svg')] opacity-10"></div>

      {/* Background Image Overlay */}
      <div className="absolute inset-0 bg-black/20"></div>

      <div className="relative container-responsive py-20">
        <div className="text-center max-w-4xl mx-auto">
          {/* Main Heading */}
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 text-balance">
            Discover the{' '}
            <span className="text-yellow-400">Best Tech Stacks</span>
            {' '}Used by Top Creators
          </h1>

          {/* Subheading */}
          <p className="text-xl md:text-2xl text-primary-100 mb-8 text-pretty max-w-3xl mx-auto">
            Explore tools, tech stacks, and workflows from developers, designers,
            and creators across social media.
          </p>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="bg-white rounded-2xl p-6 shadow-2xl mb-8">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search Input */}
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search for tools, tech stacks, or creators..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Search Button */}
              <button
                type="submit"
                className="bg-primary-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-primary-700 transition-colors duration-200 shadow-lg hover:shadow-xl"
              >
                Search
              </button>
            </div>
          </form>

          {/* Quick Search Options */}
          <div className="mb-12">
            <p className="text-primary-100 mb-4 text-lg">Popular searches:</p>
            <div className="flex flex-wrap gap-3 justify-center">
              {quickSearchOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleQuickSearch(option)}
                  className="bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-full font-medium transition-colors duration-200 backdrop-blur-sm border border-white/20"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Users className="h-8 w-8 text-yellow-400 mr-2" />
                <span className="text-3xl font-bold text-white">1000+</span>
              </div>
              <p className="text-primary-100">Creators</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <MapPin className="h-8 w-8 text-yellow-400 mr-2" />
                <span className="text-3xl font-bold text-white">500+</span>
              </div>
              <p className="text-primary-100">Tools</p>
            </div>
            <div className="text-center col-span-2 md:col-span-1">
              <div className="flex items-center justify-center mb-2">
                <Star className="h-8 w-8 text-yellow-400 mr-2" />
                <span className="text-3xl font-bold text-white">200+</span>
              </div>
              <p className="text-primary-100">Tech Stacks</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
