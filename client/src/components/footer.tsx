import { HeartIcon } from '@heroicons/react/24/outline';

// components/Footer.tsx
export default function Footer() {
    return (
        
      <footer className="px-5 py-5">
        <div className="mx-auto border-t border-gray-200">
          <div className="xl:grid xl:grid-cols-6">
            <div className="space-y-6 xl:col-span-2 mt-10">
              <a href='/' className="text-3xl font-bold text-indigo-600">Parallax</a>
              <p className="text-gray-500 text-sm">
                Making the world a better place through dialog.
              </p>
              
            </div>
  
            <div className="mt-12 grid grid-cols-1 gap-8 xl:col-span-4 text-center">
              <div className="md:grid md:grid-cols-4 md:gap-8">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">Legal</h3>
                  <ul role="list" className="mt-4 space-y-4 text-sm text-gray-500">
                    <li><a href="/privacypolicy">Privacy policy</a></li>
                    <li><a href="/cookiepolicy">License</a></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
  
          <div className=" mt-5 pt-8">
            <p className="text-sm text-gray-400 text-center">
              &copy; 2024 Parallax, Inc. All rights reserved.
            </p>

            <p className="text-sm text-gray-400 text-center">
              Made with from <span className="text-indigo-600">♥</span> <a href="/" className="text-bold text-gray-600 underline">Simone Bitti</a>
            </p>
          </div>
        </div>
      </footer>
    );
  }
  