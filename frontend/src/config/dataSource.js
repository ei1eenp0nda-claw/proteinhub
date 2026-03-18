// 数据源配置与加载
// 切换数据源时只需修改 DATA_SOURCE

// ============ 配置区 ============
export const DATA_SOURCE = {
  // 数据源模式: 'json' | 'api' | 'batch_d' | 'batch_f'
  // 'json' - 读取 public/notes-data.json (预构建)
  // 'api'  - 调用后端 API 实时读取 md 文件
  // 'batch_d' - Batch D 论文数据
  // 'batch_f' - Batch F 论文数据
  current: 'api',
  
  sources: {
    json: {
      name: '静态 JSON (预构建)',
      file: '/notes-data.json',
      type: 'high_quality'
    },
    api: {
      name: '后端 API (动态读取 md)',
      baseUrl: '/api',
      type: 'api'
    },
    batch_d: {
      name: 'Batch D 论文集',
      file: '/batch_d_papers.json',
      type: 'batch_d'
    },
    batch_f: {
      name: 'Batch F 论文集',
      file: '/batch_f_papers.json',
      type: 'batch_f'
    }
  }
}
// =================================

// 数据格式转换器
const formatConverters = {
  // 静态 JSON 格式
  high_quality: (rawData) => {
    const notes = rawData.notes || rawData
    return notes.map((note, index) => {
      const content = note.content || ''
      const titleMatch = content.match(/^#\s+(.+)$/m)
      const title = titleMatch ? titleMatch[1].trim() : (note.title || '学术笔记')
      
      const lines = content.split('\n').filter(l => l.trim())
      let preview = ''
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('#') && trimmed.length > 20) {
          preview = trimmed.substring(0, 100) + (trimmed.length > 100 ? '...' : '')
          break
        }
      }
      
      return {
        id: note.id || `note_${index}`,
        title: title,
        preview: preview,
        content: content,
        author: note.author || 'ProteinHub',
        authorAvatar: note.authorAvatar || '',
        likes: note.likes || Math.floor(Math.random() * 500) + 10,
        comments: note.comments || Math.floor(Math.random() * 100) + 1,
        favorites: note.favorites || Math.floor(Math.random() * 200) + 5,
        isLiked: false,
        isFavorited: false,
        tags: note.tags || ['科研', '生物'],
        createdAt: note.createdAt || new Date().toISOString()
      }
    })
  },
  
  // API 模式 - 数据已经是格式化好的
  api: (data) => {
    // API 返回的数据已经格式化
    if (Array.isArray(data)) {
      return data.map(note => ({
        ...note,
        id: note.id || note.filename,
        title: note.title || '学术笔记',
        content: note.content || '',
        likes: note.likes || Math.floor(Math.random() * 500) + 10,
        comments: note.comments || Math.floor(Math.random() * 100) + 1,
        favorites: note.favorites || Math.floor(Math.random() * 200) + 5,
        isLiked: false,
        isFavorited: false,
      }))
    }
    return data.notes || []
  },
  
  // 原始论文数据格式
  batch_d: (rawData) => {
    const papers = Array.isArray(rawData) ? rawData : (rawData.papers || [])
    return papers.map((paper, index) => ({
      id: paper.paperId || `batch_d_${index}`,
      title: paper.title || '学术论文',
      preview: paper.abstract ? paper.abstract.substring(0, 100) + '...' : '',
      content: `# ${paper.title}\n\n## 摘要\n\n${paper.abstract || '暂无摘要'}\n\n## 作者\n\n${(paper.authors || []).map(a => a.name).join(', ')}\n\n## 期刊信息\n\n- 期刊: ${paper.venue || 'N/A'}\n- 年份: ${paper.year || 'N/A'}\n- 引用: ${paper.citationCount || 0}次\n- DOI: ${paper.externalIds?.DOI || 'N/A'}`,
      author: 'ProteinHub',
      authorAvatar: '',
      likes: Math.floor(Math.random() * 200) + 10,
      comments: Math.floor(Math.random() * 50) + 1,
      favorites: Math.floor(Math.random() * 100) + 5,
      isLiked: false,
      isFavorited: false,
      tags: paper.fieldsOfStudy || ['科研'],
      createdAt: new Date().toISOString()
    }))
  },
  
  batch_f: (rawData) => {
    return formatConverters.batch_d(rawData)
  }
}

// 获取当前数据源配置
export const getCurrentSource = () => {
  return DATA_SOURCE.sources[DATA_SOURCE.current]
}

// 加载笔记列表（支持分页）
export const loadNotesData = async (page = 1, perPage = 10) => {
  const source = getCurrentSource()
  
  // API 模式
  if (DATA_SOURCE.current === 'api') {
    const response = await fetch(`${source.baseUrl}/notes/list?page=${page}&per_page=${perPage}`)
    const data = await response.json()
    const converter = formatConverters.api
    return {
      notes: converter(data),
      total: data.total,
      hasMore: data.has_more
    }
  }
  
  // 静态 JSON 模式
  const response = await fetch(source.file)
  const rawData = await response.json()
  const converter = formatConverters[source.type] || formatConverters.high_quality
  const allNotes = converter(rawData)
  
  // 手动分页
  const start = (page - 1) * perPage
  const end = start + perPage
  return {
    notes: allNotes.slice(start, end),
    total: allNotes.length,
    hasMore: end < allNotes.length
  }
}

// 加载单篇笔记详情
export const loadNoteDetail = async (noteId) => {
  const source = getCurrentSource()
  
  // API 模式
  if (DATA_SOURCE.current === 'api') {
    const response = await fetch(`${source.baseUrl}/notes/${noteId}`)
    if (!response.ok) return null
    const data = await response.json()
    
    const content = data.content
    const titleMatch = content.match(/^#\s+(.+)$/m)
    
    return {
      id: noteId,
      title: titleMatch ? titleMatch[1].trim() : '学术笔记',
      content: content,
      author: 'ProteinHub',
      authorAvatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
      publishTime: new Date().toLocaleString('zh-CN'),
      tags: ['科研', '生物'],
      likes: Math.floor(Math.random() * 500) + 10,
      favorites: Math.floor(Math.random() * 200) + 5,
      comments: Math.floor(Math.random() * 100) + 1,
      isLiked: false,
      isFavorited: false
    }
  }
  
  // 静态 JSON 模式 - 加载全部后查找
  const { notes } = await loadNotesData(1, 10000) // 加载足够多的数量
  let targetNote = notes.find(n => n.id === noteId)
  
  // 降级：通过索引匹配
  if (!targetNote && noteId.startsWith('note_')) {
    const index = parseInt(noteId.replace('note_', ''))
    if (!isNaN(index) && index >= 0 && index < notes.length) {
      targetNote = notes[index]
    }
  }
  
  return targetNote
}

// 搜索笔记
export const searchNotes = async (query) => {
  const source = getCurrentSource()
  
  // API 模式
  if (DATA_SOURCE.current === 'api') {
    const response = await fetch(`${source.baseUrl}/notes/search?q=${encodeURIComponent(query)}`)
    const data = await response.json()
    return data.results || []
  }
  
  // 静态 JSON 模式 - 前端搜索
  const { notes } = await loadNotesData(1, 10000)
  const queryLower = query.toLowerCase()
  return notes.filter(note => 
    note.title.toLowerCase().includes(queryLower) ||
    note.content.toLowerCase().includes(queryLower) ||
    note.preview.toLowerCase().includes(queryLower)
  )
}