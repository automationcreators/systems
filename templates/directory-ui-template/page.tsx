import { HeroSection } from '@/components/home/HeroSection'
import { CategoryGrid } from '@/components/home/CategoryGrid'
import { StatsSection } from '@/components/home/StatsSection'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section with Search */}
      <HeroSection />

      {/* Main Categories */}
      <section className="py-16 bg-white">
        <div className="container-responsive">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Browse Tools by Category
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Discover the perfect tools for your workflow across development, design, AI, and more
            </p>
          </div>
          <CategoryGrid />
        </div>
      </section>

      {/* Statistics */}
      <StatsSection />

      {/* CTA Section */}
      <section className="py-16 bg-gray-50">
        <div className="container-responsive text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to Share Your Tech Stack?
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
            Join thousands of creators who have shared their favorite tools and workflows.
            Help others discover great software and connect with the community.
          </p>
          <a
            href="/submit"
            className="btn-primary btn-lg"
          >
            Submit Your Stack
          </a>
        </div>
      </section>
    </div>
  )
}
