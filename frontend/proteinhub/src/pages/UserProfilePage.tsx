import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  User, 
  Mail, 
  Calendar, 
  Heart, 
  Dna, 
  Trash2, 
  Loader2,
  AlertCircle,
  ChevronRight,
  LogOut
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { proteinService } from '../services/proteinService';
import { Favorite } from '../types';

const UserProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();
  
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: '/profile' } } });
      return;
    }
    fetchFavorites();
  }, [isAuthenticated]);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await proteinService.getFavorites();
      setFavorites(data);
    } catch (err) {
      setError('获取收藏列表失败');
      console.error('Error fetching favorites:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (favoriteId: number) => {
    try {
      setRemovingId(favoriteId);
      await proteinService.removeFavorite(favoriteId);
      setFavorites(prev => prev.filter(f => f.id !== favoriteId));
    } catch (err) {
      console.error('Error removing favorite:', err);
      alert('删除收藏失败');
    } finally {
      setRemovingId(null);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <User className="h-8 w-8 mr-3 text-primary-600" />
            个人中心
          </h1>
          <p className="mt-2 text-gray-600">
            管理您的账户信息和收藏的蛋白质
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - User Info */}
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="card">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-primary-100 rounded-full mb-4">
                  <User className="h-10 w-10 text-primary-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">{user?.username}</h2>
                {user?.full_name && (
                  <p className="text-gray-600">{user.full_name}</p>
                )}
                <p className="text-gray-500 text-sm mt-1">{user?.email}</p>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-primary-600">
                      {favorites.length}
                    </div>
                    <div className="text-sm text-gray-600">收藏</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary-600">
                      {user?.created_at ? formatDate(user.created_at) : '-'}
                    </div>
                    <div className="text-sm text-gray-600">加入时间</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Links */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快速链接</h3>
              <nav className="space-y-2">
                <Link
                  to="/proteins"
                  className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <Dna className="h-5 w-5 mr-3 text-primary-600" />
                  浏览蛋白质
                  <ChevronRight className="h-4 w-4 ml-auto" />
                </Link>
                <Link
                  to="/search"
                  className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <Heart className="h-5 w-5 mr-3 text-primary-600" />
                  搜索蛋白质
                  <ChevronRight className="h-4 w-4 ml-auto" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <LogOut className="h-5 w-5 mr-3" />
                  退出登录
                </button>
              </nav>
            </div>
          </div>

          {/* Right Column - Favorites */}
          <div className="lg:col-span-2">
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                    <Heart className="h-5 w-5 mr-2 text-red-500" />
                    我的收藏
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    您收藏了 {favorites.length} 个蛋白质
                  </p>
                </div>
                <Link to="/proteins" className="btn-secondary text-sm">
                  浏览更多
                </Link>
              </div>

              {loading ? (
                <div className="flex justify-center items-center py-12">
                  <Loader2 className="h-10 w-10 animate-spin text-primary-600" />
                </div>
              ) : error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                  <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                  <p className="text-red-700">{error}</p>
                  <button
                    onClick={fetchFavorites}
                    className="mt-2 text-sm text-red-600 hover:text-red-700"
                  >
                    重试
                  </button>
                </div>
              ) : favorites.length === 0 ? (
                <div className="text-center py-12">
                  <Heart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    暂无收藏
                  </h3>
                  <p className="text-gray-600 mb-4">
                    浏览蛋白质数据库，收藏您感兴趣的蛋白质
                  </p>
                  <Link to="/proteins" className="btn-primary">
                    开始浏览
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {favorites.map((favorite) => (
                    <div
                      key={favorite.id}
                      className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                    >
                      <Link
                        to={`/proteins/${favorite.protein_id}`}
                        className="flex-grow flex items-center"
                      >
                        <div className="flex-shrink-0 h-12 w-12 bg-primary-100 rounded-full flex items-center justify-center">
                          <Dna className="h-6 w-6 text-primary-600" />
                        </div>
                        <div className="ml-4">
                          <h3 className="text-lg font-medium text-gray-900">
                            {favorite.protein?.name || `蛋白质 #${favorite.protein_id}`}
                          </h3>
                          {favorite.protein?.species && (
                            <p className="text-sm text-gray-600">
                              {favorite.protein.species}
                              {favorite.protein.molecular_weight && (
                                <span className="ml-2">
                                  • {(favorite.protein.molecular_weight / 1000).toFixed(1)} kDa
                                </span>
                              )}
                            </p>
                          )}
                        </div>
                      </Link>
                      
                      <button
                        onClick={() => handleRemoveFavorite(favorite.id)}
                        disabled={removingId === favorite.id}
                        className="ml-4 p-2 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                        title="移除收藏"
                      >
                        {removingId === favorite.id ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <Trash2 className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
