import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Search, 
  Database, 
  Dna, 
  ArrowRight, 
  CheckCircle2,
  Microscope,
  FileText,
  Users
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const features = [
    {
      icon: <Dna className="h-8 w-8 text-primary-600" />,
      title: '全面蛋白质数据',
      description: '收录海量蛋白质序列、结构及功能信息，支持多维度检索',
    },
    {
      icon: <Search className="h-8 w-8 text-primary-600" />,
      title: '智能搜索',
      description: '支持关键词、序列、物种等多种搜索方式，快速定位目标蛋白',
    },
    {
      icon: <Microscope className="h-8 w-8 text-primary-600" />,
      title: '详细信息展示',
      description: '提供完整蛋白质信息，包括序列、分子量、功能描述等',
    },
    {
      icon: <Database className="h-8 w-8 text-primary-600" />,
      title: '个人收藏管理',
      description: '收藏感兴趣的蛋白质，方便后续快速访问和研究',
    },
  ];

  const stats = [
    { label: '收录蛋白质', value: '50,000+' },
    { label: '覆盖物种', value: '2,000+' },
    { label: '注册用户', value: '10,000+' },
    { label: '日访问量', value: '50,000+' },
  ];

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-50 via-white to-primary-100 py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
              探索蛋白质世界的
              <span className="text-primary-600">无限可能</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              ProteinHub 是专业的蛋白质信息管理平台，为科研人员和生物信息学专家
              提供全面、准确、及时的蛋白质数据服务。
            </p>
            
            {/* Quick Search */}
            <div className="max-w-2xl mx-auto mb-8">
              <div className="flex items-center bg-white rounded-lg shadow-lg p-2">
                <Search className="h-6 w-6 text-gray-400 ml-3" />
                <input
                  type="text"
                  placeholder="搜索蛋白质名称、UniProt ID或物种..."
                  className="flex-grow px-4 py-2 outline-none"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      navigate(`/search?q=${encodeURIComponent((e.target as HTMLInputElement).value)}`);
                    }
                  }}
                />
                <button 
                  className="btn-primary"
                  onClick={() => {
                    const input = document.querySelector('input[type="text"]') as HTMLInputElement;
                    if (input?.value) {
                      navigate(`/search?q=${encodeURIComponent(input.value)}`);
                    }
                  }}
                >
                  搜索
                </button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/proteins" className="btn-primary text-lg px-8 py-3">
                浏览蛋白质
              </Link>
              {!isAuthenticated && (
                <Link to="/register" className="btn-secondary text-lg px-8 py-3">
                  免费注册
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              强大功能，助力科研
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              我们提供全面的蛋白质数据管理功能，满足科研人员日常工作需求
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card hover:shadow-lg transition-shadow">
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            {stats.map((stat, index) => (
              <div key={index}>
                <div className="text-4xl lg:text-5xl font-bold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-primary-200">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 lg:p-12 text-center">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
              准备好开始探索了吗？
            </h2>
            <p className="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
              立即注册 ProteinHub 账户，获取完整的蛋白质数据访问权限和个性化收藏功能。
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {!isAuthenticated ? (
                <>
                  <Link to="/register" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                    免费注册
                  </Link>
                  <Link to="/proteins" className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors">
                    先逛逛
                  </Link>
                </>
              ) : (
                <Link to="/proteins" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                  浏览蛋白质
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              为什么选择 ProteinHub
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              我们致力于为科研人员提供最优质的蛋白质数据服务
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-primary-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">数据准确可靠</h3>
              <p className="text-gray-600">所有数据均经过严格验证，确保准确性和可靠性</p>
            </div>

            <div className="text-center">
              <div className="bg-primary-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">信息完整全面</h3>
              <p className="text-gray-600">提供完整的蛋白质信息，包括序列、结构、功能等</p>
            </div>

            <div className="text-center">
              <div className="bg-primary-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">用户友好体验</h3>
              <p className="text-gray-600">简洁直观的界面设计，轻松上手使用</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
