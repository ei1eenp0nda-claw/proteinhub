import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Heart, 
  Share2, 
  Copy, 
  Check,
  Loader2,
  AlertCircle,
  Dna,
  Scale,
  Calendar,
  Tag
} from 'lucide-react';
import { Protein, Favorite } from '../types';
import { proteinService } from '../services/proteinService';
import { useAuth } from '../contexts/AuthContext';

const ProteinDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [protein, setProtein] = useState<Protein | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteId, setFavoriteId] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchProtein(parseInt(id));
      if (isAuthenticated) {
        checkFavoriteStatus();
      }
    }
  }, [id, isAuthenticated]);

  const fetchProtein = async (proteinId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await proteinService.getProteinById(proteinId);
      setProtein(data);
    } catch (err) {
      setError('获取蛋白质详情失败');
      console.error('Error fetching protein:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkFavoriteStatus = async () => {
    try {
      const favorites = await proteinService.getFavorites();
      const favorite = favorites.find(f => f.protein_id === parseInt(id!));
      if (favorite) {
        setIsFavorite(true);
        setFavoriteId(favorite.id);
      }
    } catch (err) {
      console.error('Error checking favorite status:', err);
    }
  };

  const toggleFavorite = async () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: `/proteins/${id}` } });
      return;
    }

    try {
      setFavoriteLoading(true);
      if (isFavorite && favoriteId) {
        await proteinService.removeFavorite(favoriteId);
        setIsFavorite(false);
        setFavoriteId(null);
      } else {
        const favorite = await proteinService.addFavorite(parseInt(id!));
        setIsFavorite(true);
        setFavoriteId(favorite.id);
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
    } finally {
      setFavoriteLoading(false);
    }
  };

  const copySequence = () => {
    if (protein?.sequence) {
      navigator.clipboard.writeText(protein.sequence);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary-600" />
      </div>
    );
  }

  if (error || !protein) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-red-800 mb-2">
              {error || '蛋白质未找到'}
            </h2>
            <p className="text-red-600 mb-4">
              请检查URL是否正确，或返回蛋白质列表
            </p>
            <Link to="/proteins" className="btn-primary inline-block">
              返回列表
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb & Actions */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <nav className="flex items-center text-sm text-gray-500 mb-4 md:mb-0">
            <Link to="/" className="hover:text-primary-600">首页</Link>
            <span className="mx-2">/</span>
            <Link to="/proteins" className="hover:text-primary-600">蛋白质</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">{protein.name}</span>
          </nav>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleFavorite}
              disabled={favoriteLoading}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                isFavorite
                  ? 'bg-red-50 text-red-600 hover:bg-red-100'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {favoriteLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
              )}
              <span className="ml-2">{isFavorite ? '已收藏' : '收藏'}</span>
            </button>
            
            <button
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                alert('链接已复制到剪贴板');
              }}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Share2 className="h-5 w-5" />
              <span className="ml-2 hidden sm:inline">分享</span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info Card */}
            <div className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{protein.name}</h1>
                  {protein.uniprot_id && (
                    <p className="text-gray-500 mt-1">
                      UniProt ID: {protein.uniprot_id}
                    </p>
                  )}
                </div>
                <div className="bg-primary-100 p-3 rounded-full">
                  <Dna className="h-8 w-8 text-primary-600" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center text-gray-500 mb-1">
                    <Scale className="h-4 w-4 mr-1" />
                    分子量
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatMolecularWeight(protein.molecular_weight)}
                  </p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center text-gray-500 mb-1">
                    <Tag className="h-4 w-4 mr-1" />
                    物种
                  </div>
                  <p className="text-lg font-semibold text-gray-900 truncate">
                    {protein.species}
                  </p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center text-gray-500 mb-1">
                    <Calendar className="h-4 w-4 mr-1" />
                    创建时间
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatDate(protein.created_at)}
                  </p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center text-gray-500 mb-1">
                    <Dna className="h-4 w-4 mr-1" />
                    序列长度
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {protein.sequence.length} aa
                  </p>
                </div>
              </div>
            </div>

            {/* Function Description */}
            {protein.function_description && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">功能描述</h2>
                <p className="text-gray-700 leading-relaxed">
                  {protein.function_description}
                </p>
              </div>
            )}

            {/* Sequence */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">氨基酸序列</h2>
                <button
                  onClick={copySequence}
                  className="flex items-center px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      已复制
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      复制
                    </>
                  )}
                </button>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-mono text-sm text-gray-700 break-all leading-relaxed">
                  {protein.sequence}
                </p>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                序列长度: {protein.sequence.length} 氨基酸
              </p>
            </div>
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快速操作</h3>
              <div className="space-y-3">
                <button
                  onClick={toggleFavorite}
                  disabled={favoriteLoading}
                  className={`w-full flex items-center justify-center px-4 py-2 rounded-lg transition-colors ${
                    isFavorite
                      ? 'bg-red-50 text-red-600 hover:bg-red-100'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {favoriteLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      <Heart className={`h-5 w-5 mr-2 ${isFavorite ? 'fill-current' : ''}`} />
                      {isFavorite ? '已收藏' : '收藏'}
                    </>
                  )}
                </button>
                
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href);
                    alert('链接已复制');
                  }}
                  className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Share2 className="h-5 w-5 mr-2" />
                  分享
                </button>
                
                <button
                  onClick={copySequence}
                  className="w-full flex items-center justify-center px-4 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="h-5 w-5 mr-2" />
                      已复制
                    </>
                  ) : (
                    <>
                      <Copy className="h-5 w-5 mr-2" />
                      复制序列
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Related Info */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">相关信息</h3>
              <div className="space-y-3 text-sm">
                {protein?.uniprot_id && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">UniProt ID:</span>
                    <a 
                      href={`https://www.uniprot.org/uniprotkb/${protein.uniprot_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:underline"
                    >
                      {protein.uniprot_id}
                    </a>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">创建时间:</span>
                  <span className="text-gray-900">{formatDate(protein!.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最后更新:</span>
                  <span className="text-gray-900">{formatDate(protein!.updated_at)}</span>
                </div>
              </div>
            </div>

            {/* External Links */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">外部资源</h3>
              <div className="space-y-2">
                {protein?.uniprot_id && (
                  <a
                    href={`https://www.uniprot.org/uniprotkb/${protein.uniprot_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center text-primary-600 hover:text-primary-700"
                  >
                    <Database className="h-4 w-4 mr-2" />
                    UniProt 数据库
                    <ArrowLeft className="h-4 w-4 ml-1 rotate-180" />
                  </a>
                )}
                <a
                  href={`https://www.ncbi.nlm.nih.gov/protein/?term=${encodeURIComponent(protein?.name || '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-primary-600 hover:text-primary-700"
                >
                  <Database className="h-4 w-4 mr-2" />
                  NCBI Protein
                  <ArrowLeft className="h-4 w-4 ml-1 rotate-180" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProteinDetailPage;
