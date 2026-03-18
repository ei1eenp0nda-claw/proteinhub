// 数据源配置与加载
// 切换数据源时只需修改 DATA_SOURCE.current

// 数据格式转换器
const formatConverters = {
  // high_quality 格式: { id, file, content }
  high_quality: (rawData) => {
    const notes = rawData.notes || rawData
    return notes.map((note, index) => {
      const content = note.content || ''
      // 从 markdown 提取标题
      const titleMatch = content.match(/^#\s+(.+)$/m)
      const title = titleMatch ? titleMatch[1].trim() : '学术笔记'
      // 提取预览（第一段非标题文字）
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
  
  // batch_d 格式（假设是原始论文数据，需要转换）
  batch_d: (rawData) => {
    // 如果是论文数组，需要生成笔记格式
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
  
  // batch_f 格式
  batch_f: (rawData) => {
    // 复用 batch_d 的逻辑（假设格式相同）
    return formatConverters.batch_d(rawData)
  }
}

export const DATA_SOURCE = {
  // 当前使用的数据源 - 修改这里切换
  current: 'high_quality', // 'high_quality' | 'batch_d' | 'batch_f' | 'all'
  
  // 数据源定义
  sources: {
    high_quality: {
      name: '高质量笔记库',
      file: '/notes-data.json',
      type: 'high_quality'
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
    },
    all: {
      name: '全部数据合并',
      file: '/all_notes.json',
      type: 'high_quality'
    }
  }
}

// 获取当前数据源配置
export const getCurrentSource = () => {
  return DATA_SOURCE.sources[DATA_SOURCE.current]
}

// 加载笔记数据（统一格式）
export const loadNotesData = async () => {
  const source = getCurrentSource()
  
  // 如果是合并模式，加载多个源
  if (DATA_SOURCE.current === 'all') {
    const allNotes = []
    for (const [key, src] of Object.entries(DATA_SOURCE.sources)) {
      if (key === 'all') continue
      try {
        const response = await fetch(src.file)
        const data = await response.json()
        const converter = formatConverters[src.type] || formatConverters.high_quality
        const notes = converter(data)
        allNotes.push(...notes)
      } catch (e) {
        console.warn(`加载 ${key} 失败:`, e)
      }
    }
    return allNotes
  }
  
  // 单数据源模式
  const response = await fetch(source.file)
  const rawData = await response.json()
  
  // 使用对应的数据转换器
  const converter = formatConverters[source.type] || formatConverters.high_quality
  return converter(rawData)
}