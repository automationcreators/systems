import {
  Users,
  MapPin,
  Star,
  TrendingUp,
} from 'lucide-react'

const stats = [
  {
    label: 'Active Tools',
    value: '500+',
    description: 'Verified tools across categories',
    icon: MapPin,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  {
    label: 'Tech Stacks',
    value: '200+',
    description: 'Curated technology combinations',
    icon: Star,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    label: 'Creators',
    value: '1,000+',
    description: 'Developers, designers, and builders',
    icon: Users,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  {
    label: 'Monthly Growth',
    value: '+25%',
    description: 'New tech stacks added each month',
    icon: TrendingUp,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
  },
]

export function StatsSection() {
  return (
    <section className="py-16 bg-primary-600 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>

      <div className="container-responsive relative">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Trusted by Developers & Creators
          </h2>
          <p className="text-xl text-primary-100 max-w-2xl mx-auto">
            Join thousands who have discovered the perfect tools and tech stacks for their projects
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, index) => {
            const IconComponent = stat.icon

            return (
              <div key={index} className="text-center">
                <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className={`${stat.bgColor} w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4`}>
                    <IconComponent className={`h-8 w-8 ${stat.color}`} />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    {stat.value}
                  </div>
                  <div className="text-lg font-semibold text-gray-900 mb-1">
                    {stat.label}
                  </div>
                  <div className="text-sm text-gray-600">
                    {stat.description}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Additional Info */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-white mb-2">AI-Powered Discovery</div>
              <p className="text-primary-100 text-sm">
                We automatically discover and verify tech stacks from social media content using advanced AI.
              </p>
            </div>
            <div>
              <div className="text-2xl font-bold text-white mb-2">Real Creator Insights</div>
              <p className="text-primary-100 text-sm">
                See what tools and stacks successful creators actually use in their daily workflows.
              </p>
            </div>
            <div>
              <div className="text-2xl font-bold text-white mb-2">Always Free</div>
              <p className="text-primary-100 text-sm">
                Our directory is completely free. Discover tools and tech stacks without any hidden costs.
              </p>
            </div>
          </div>
        </div>

        {/* Achievement Badges */}
        <div className="mt-12 flex flex-wrap justify-center gap-6">
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center">
            <Star className="h-5 w-5 text-yellow-300 mr-2" />
            <span className="text-white font-medium text-sm">Top Tech Stack Directory</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center">
            <Users className="h-5 w-5 text-white mr-2" />
            <span className="text-white font-medium text-sm">Creator Trusted</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center">
            <TrendingUp className="h-5 w-5 text-white mr-2" />
            <span className="text-white font-medium text-sm">Growing Daily</span>
          </div>
        </div>
      </div>
    </section>
  )
}
