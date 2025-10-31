'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X, Search, Star } from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Home', href: '/' },
  { name: 'Browse Tools', href: '/tools' },
  { name: 'Categories', href: '/categories' },
  { name: 'Creators', href: '/creators' },
  { name: 'About', href: '/about' },
]

const categoryDropdown = [
  { name: 'Development', href: '/categories/development', icon: '💻' },
  { name: 'Design', href: '/categories/design', icon: '🎨' },
  { name: 'AI & ML', href: '/categories/ai-ml', icon: '🤖' },
  { name: 'Productivity', href: '/categories/productivity', icon: '⚡' },
  { name: 'Marketing', href: '/categories/marketing', icon: '📢' },
  { name: 'Data & Analytics', href: '/categories/data-analytics', icon: '📊' },
]

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [categoriesDropdownOpen, setCategoriesDropdownOpen] = useState(false)
  const pathname = usePathname()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <nav className="container-responsive" aria-label="Global navigation">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <div className="flex lg:flex-1">
            <Link href="/" className="-m-1.5 p-1.5">
              <span className="sr-only">Tech Stack Directory</span>
              <div className="flex items-center space-x-2">
                <div className="bg-primary-600 rounded-lg p-2">
                  <Star className="h-6 w-6 text-white" fill="white" />
                </div>
                <div>
                  <div className="text-xl font-bold text-gray-900">
                    Tech Stack
                  </div>
                  <div className="text-sm text-gray-600">Directory</div>
                </div>
              </div>
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex lg:hidden">
            <button
              type="button"
              className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-700 hover:bg-gray-50"
              onClick={() => setMobileMenuOpen(true)}
            >
              <span className="sr-only">Open main menu</span>
              <Menu className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          {/* Desktop navigation */}
          <div className="hidden lg:flex lg:gap-x-8 lg:items-center">
            {navigation.map((item) => {
              if (item.name === 'Categories') {
                return (
                  <div
                    key={item.name}
                    className="relative group"
                  >
                    <Link
                      href={item.href}
                      className={clsx(
                        'flex items-center text-sm font-medium hover:text-primary-600 transition-colors px-3 py-2',
                        pathname === item.href
                          ? 'text-primary-600'
                          : 'text-gray-700'
                      )}
                      onMouseEnter={() => setCategoriesDropdownOpen(true)}
                    >
                      {item.name}
                    </Link>
                    <div
                      className="absolute left-0 z-10 mt-0 w-56 origin-top-left opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200"
                      onMouseEnter={() => setCategoriesDropdownOpen(true)}
                      onMouseLeave={() => setCategoriesDropdownOpen(false)}
                    >
                      <div className="rounded-md bg-white py-2 shadow-lg ring-1 ring-black ring-opacity-5">
                        {categoryDropdown.map((category) => (
                          <Link
                            key={category.name}
                            href={category.href}
                            className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          >
                            <span className="mr-3 text-lg">{category.icon}</span>
                            {category.name}
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              }

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'text-sm font-medium hover:text-primary-600 transition-colors px-3 py-2',
                    pathname === item.href
                      ? 'text-primary-600'
                      : 'text-gray-700'
                  )}
                >
                  {item.name}
                </Link>
              )
            })}
          </div>

          {/* Search button */}
          <div className="hidden lg:flex lg:flex-1 lg:justify-end">
            <Link
              href="/search"
              className="btn-primary flex items-center space-x-2"
            >
              <Search className="h-4 w-4" />
              <span>Search</span>
            </Link>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden">
            <div className="fixed inset-0 z-10 bg-black bg-opacity-25" />
            <div className="fixed inset-y-0 right-0 z-10 w-full overflow-y-auto bg-white px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-gray-900/10">
              <div className="flex items-center justify-between">
                <Link href="/" className="-m-1.5 p-1.5">
                  <span className="sr-only">Tech Stack Directory</span>
                  <div className="flex items-center space-x-2">
                    <div className="bg-primary-600 rounded-lg p-2">
                      <Star className="h-5 w-5 text-white" fill="white" />
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-900">
                        Tech Stack
                      </div>
                      <div className="text-xs text-gray-600">Directory</div>
                    </div>
                  </div>
                </Link>
                <button
                  type="button"
                  className="-m-2.5 rounded-md p-2.5 text-gray-700"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <span className="sr-only">Close menu</span>
                  <X className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>
              <div className="mt-6 flow-root">
                <div className="-my-6 divide-y divide-gray-500/10">
                  <div className="space-y-2 py-6">
                    {navigation.map((item) => (
                      <Link
                        key={item.name}
                        href={item.href}
                        className="-mx-3 block rounded-lg px-3 py-2 text-base font-medium text-gray-900 hover:bg-gray-50"
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        {item.name}
                      </Link>
                    ))}
                  </div>
                  <div className="py-6">
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-900 mb-2">
                        Categories
                      </h3>
                      {categoryDropdown.map((category) => (
                        <Link
                          key={category.name}
                          href={category.href}
                          className="flex items-center -mx-3 rounded-lg px-3 py-2 text-base text-gray-700 hover:bg-gray-50"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          <span className="mr-3">{category.icon}</span>
                          {category.name}
                        </Link>
                      ))}
                    </div>
                    <Link
                      href="/search"
                      className="btn-primary w-full flex items-center justify-center space-x-2"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Search className="h-4 w-4" />
                      <span>Search Tools</span>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  )
}