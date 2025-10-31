import Link from 'next/link'
import {
  Code,
  Palette,
  Brain,
  BarChart,
  Megaphone,
  Zap,
} from 'lucide-react'

const categories = [
  {
    name: 'Development',
    slug: 'development',
    description: 'IDEs, frameworks, version control, and developer tools',
    icon: Code,
    color: 'bg-green-500',
    hoverColor: 'hover:bg-green-600',
    textColor: 'text-green-600',
    count: 150,
    featured: ['VS Code', 'GitHub', 'Docker', 'Vercel']
  },
  {
    name: 'Design',
    slug: 'design',
    description: 'Design tools, prototyping, and creative software',
    icon: Palette,
    color: 'bg-purple-500',
    hoverColor: 'hover:bg-purple-600',
    textColor: 'text-purple-600',
    count: 85,
    featured: ['Figma', 'Adobe XD', 'Sketch', 'Canva']
  },
  {
    name: 'AI & ML',
    slug: 'ai-ml',
    description: 'AI tools, machine learning platforms, and automation',
    icon: Brain,
    color: 'bg-blue-500',
    hoverColor: 'hover:bg-blue-600',
    textColor: 'text-blue-600',
    count: 120,
    featured: ['ChatGPT', 'Midjourney', 'Claude', 'GitHub Copilot']
  },
  {
    name: 'Productivity',
    slug: 'productivity',
    description: 'Task management, note-taking, and workflow optimization',
    icon: Zap,
    color: 'bg-orange-500',
    hoverColor: 'hover:bg-orange-600',
    textColor: 'text-orange-600',
    count: 65,
    featured: ['Notion', 'Obsidian', 'Todoist', 'Slack']
  },
  {
    name: 'Marketing',
    slug: 'marketing',
    description: 'Email, social media, SEO, and marketing automation',
    icon: Megaphone,
    color: 'bg-pink-500',
    hoverColor: 'hover:bg-pink-600',
    textColor: 'text-pink-600',
    count: 75,
    featured: ['Mailchimp', 'Buffer', 'Ahrefs', 'HubSpot']
  },
  {
    name: 'Data & Analytics',
    slug: 'data-analytics',
    description: 'Analytics, visualization, and business intelligence',
    icon: BarChart,
    color: 'bg-indigo-500',
    hoverColor: 'hover:bg-indigo-600',
    textColor: 'text-indigo-600',
    count: 90,
    featured: ['Google Analytics', 'Tableau', 'Mixpanel', 'Amplitude']
  },
]

export function CategoryGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {categories.map((category) => {
        const IconComponent = category.icon

        return (
          <Link
            key={category.slug}
            href={`/categories/${category.slug}`}
            className="group relative bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 overflow-hidden"
          >
            {/* Category Card */}
            <div className="p-8">
              {/* Icon and Count */}
              <div className="flex items-start justify-between mb-6">
                <div className={`${category.color} ${category.hoverColor} p-4 rounded-2xl transition-colors duration-300`}>
                  <IconComponent className="h-8 w-8 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">{category.count}</div>
                  <div className="text-sm text-gray-500">tools</div>
                </div>
              </div>

              {/* Content */}
              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-900 group-hover:text-primary-600 transition-colors duration-200 mb-2">
                  {category.name}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {category.description}
                </p>
              </div>

              {/* Featured Tools */}
              <div className="mb-6">
                <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">
                  Popular Tools
                </div>
                <div className="flex flex-wrap gap-2">
                  {category.featured.slice(0, 3).map((tool, index) => (
                    <span
                      key={index}
                      className={`text-xs px-3 py-1 rounded-full bg-gray-100 ${category.textColor} font-medium`}
                    >
                      {tool}
                    </span>
                  ))}
                  {category.featured.length > 3 && (
                    <span className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-500 font-medium">
                      +{category.featured.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Call to Action */}
              <div className="flex items-center text-primary-600 font-medium group-hover:text-primary-700 transition-colors duration-200">
                <span className="mr-2">Explore {category.name}</span>
                <svg
                  className="w-4 h-4 transform group-hover:translate-x-1 transition-transform duration-200"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>

            {/* Hover Effect Gradient */}
            <div className={`absolute inset-x-0 bottom-0 h-1 ${category.color} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left`}></div>
          </Link>
        )
      })}
    </div>
  )
}
