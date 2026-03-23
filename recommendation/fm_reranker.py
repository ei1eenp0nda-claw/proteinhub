"""
FM精排层 - Factorization Machine for ProteinHub

核心功能:
- 二阶特征交叉 (FM)
- 一阶线性组合 (LR)
- 轻量级，可插拔到现有推荐流程
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
import numpy as np


class FactorizationMachine(nn.Module):
    """
    FM模型: 自动学习特征间的二阶交叉
    
    公式: y = w0 + Σwi*xi + ΣΣ<v_i, v_j>*x_i*x_j
    
    其中:
    - 第一项: 全局偏置
    - 第二项: 一阶线性组合 (LR部分)
    - 第三项: 二阶交叉 (FM核心)
    
    计算优化: 
    ΣΣ<v_i, v_j>*x_i*x_j = 0.5 * (sum_square - square_sum)
    """
    
    def __init__(self, field_dims: List[int], embed_dim: int = 16):
        """
        Args:
            field_dims: 每个特征域的维度 [user_dim, item_dim, family_dim, ...]
            embed_dim: 隐向量维度
        """
        super().__init__()
        
        self.field_dims = field_dims
        self.num_fields = len(field_dims)
        self.embed_dim = embed_dim
        
        # 一阶权重 (每个特征一个权重)
        self.fm_first_order = nn.Linear(sum(field_dims), 1)
        
        # 二阶隐向量 (每个特征一个隐向量)
        # 用Embedding方便处理变长特征
        self.fm_embedding = nn.ModuleList([
            nn.Embedding(dim, embed_dim) for dim in field_dims
        ])
        
        # 偏置项
        self.bias = nn.Parameter(torch.zeros(1))
        
        # 初始化
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        nn.init.normal_(self.fm_first_order.weight, std=0.01)
        nn.init.zeros_(self.fm_first_order.bias)
        
        for emb in self.fm_embedding:
            nn.init.xavier_uniform_(emb.weight)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: [batch_size, num_fields] - 每个特征是index
           
        Returns:
            scores: [batch_size] - 预测分数
        """
        # ===== 一阶部分 =====
        # 将index转为one-hot并拼接
        x_onehot = self._index_to_onehot(x)  # [batch, sum(field_dims)]
        fm_first = self.fm_first_order(x_onehot)  # [batch, 1]
        
        # ===== 二阶部分 =====
        # 获取每个field的embedding
        embeddings = []
        for i, emb_layer in enumerate(self.fm_embedding):
            field_emb = emb_layer(x[:, i])  # [batch, embed_dim]
            embeddings.append(field_emb)
        
        # stack: [batch, num_fields, embed_dim]
        embeddings = torch.stack(embeddings, dim=1)
        
        # 计算 sum_square 和 square_sum
        square_of_sum = torch.sum(embeddings, dim=1) ** 2  # [batch, embed_dim]
        sum_of_square = torch.sum(embeddings ** 2, dim=1)   # [batch, embed_dim]
        
        # FM二阶项
        fm_second = 0.5 * torch.sum(square_of_sum - sum_of_square, dim=1, keepdim=True)
        
        # 总和
        output = self.bias + fm_first + fm_second
        
        return output.squeeze(-1)  # [batch]
    
    def _index_to_onehot(self, x: torch.Tensor) -> torch.Tensor:
        """将特征index转为one-hot并拼接"""
        batch_size = x.size(0)
        onehots = []
        
        offset = 0
        for i, dim in enumerate(self.field_dims):
            # one-hot编码
            onehot = F.one_hot(x[:, i], num_classes=dim).float()
            onehots.append(onehot)
            offset += dim
        
        return torch.cat(onehots, dim=1)


class DeepFM(nn.Module):
    """
    DeepFM: FM + Deep Neural Network
    
    - FM部分: 学习低阶特征交叉
    - Deep部分: 学习高阶非线性交叉
    
    适用于ProteinHub的精排阶段
    """
    
    def __init__(self, field_dims: List[int], embed_dim: int = 16,
                 mlp_dims: List[int] = [128, 64, 32], dropout: float = 0.3):
        """
        Args:
            field_dims: 各特征域维度
            embed_dim: FM嵌入维度
            mlp_dims: Deep部分隐藏层维度
            dropout: Dropout率
        """
        super().__init__()
        
        self.field_dims = field_dims
        self.num_fields = len(field_dims)
        self.embed_dim = embed_dim
        
        # FM部分
        self.fm = FactorizationMachine(field_dims, embed_dim)
        
        # Deep部分
        self.embeddings = nn.ModuleList([
            nn.Embedding(dim, embed_dim) for dim in field_dims
        ])
        
        # MLP
        input_dim = len(field_dims) * embed_dim
        layers = []
        for dim in mlp_dims:
            layers.extend([
                nn.Linear(input_dim, dim),
                nn.BatchNorm1d(dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            input_dim = dim
        layers.append(nn.Linear(input_dim, 1))
        
        self.mlp = nn.Sequential(*layers)
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化"""
        for emb in self.embeddings:
            nn.init.xavier_uniform_(emb.weight)
        
        for layer in self.mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_normal_(layer.weight)
                nn.init.zeros_(layer.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, num_fields]
            
        Returns:
            scores: [batch_size]
        """
        # FM输出
        fm_output = self.fm(x).unsqueeze(-1)  # [batch, 1]
        
        # Deep部分
        embeddings = []
        for i, emb_layer in enumerate(self.embeddings):
            embeddings.append(emb_layer(x[:, i]))
        
        # 拼接所有embedding
        deep_input = torch.cat(embeddings, dim=1)  # [batch, num_fields * embed_dim]
        
        # MLP
        deep_output = self.mlp(deep_input)  # [batch, 1]
        
        # 组合 (sigmoid输出概率)
        output = torch.sigmoid(fm_output + deep_output)
        
        return output.squeeze(-1)


class ProteinReranker:
    """
    ProteinHub精排器
    
    输入候选集，使用DeepFM进行精细排序
    """
    
    def __init__(self, field_dims: List[int], embed_dim: int = 16,
                 device: str = 'cpu'):
        self.device = device
        self.model = DeepFM(field_dims, embed_dim).to(device)
        self.is_trained = False
    
    def fit(self, train_data: torch.Tensor, train_labels: torch.Tensor,
            epochs: int = 100, lr: float = 0.001, batch_size: int = 256):
        """
        训练精排模型
        
        Args:
            train_data: [N, num_fields] 训练特征
            train_labels: [N] 标签 (0/1 或连续值)
        """
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCELoss()
        
        dataset = torch.utils.data.TensorDataset(train_data, train_labels)
        dataloader = torch.utils.data.DataLoader(
            dataset, batch_size=batch_size, shuffle=True
        )
        
        print(f"🔄 训练DeepFM精排模型...")
        for epoch in range(epochs):
            total_loss = 0
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                
                predictions = self.model(batch_x)
                loss = criterion(predictions, batch_y)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 20 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
        self.is_trained = True
        print("✅ DeepFM训练完成")
    
    def rerank(self, candidates: torch.Tensor, top_k: int = 10) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        对候选集进行重排序
        
        Args:
            candidates: [N, num_fields] 候选特征
            top_k: 返回Top-K
            
        Returns:
            top_indices: [top_k] 排序后的索引
            top_scores: [top_k] 分数
        """
        if not self.is_trained:
            raise RuntimeError("模型未训练")
        
        self.model.eval()
        with torch.no_grad():
            candidates = candidates.to(self.device)
            scores = self.model(candidates)
            
            # 排序
            top_scores, top_indices = torch.topk(scores, min(top_k, len(scores)))
        
        return top_indices.cpu(), top_scores.cpu()
    
    def save(self, path: str):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'field_dims': self.model.field_dims,
            'embed_dim': self.model.embed_dim
        }, path)
    
    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True


# ==================== 单元测试 ====================

def test_fm():
    """测试FactorizationMachine"""
    print("\n" + "="*50)
    print("测试1: FactorizationMachine")
    print("="*50)
    
    # 模拟特征: user(100), item(200), family(20)
    field_dims = [100, 200, 20]
    batch_size = 32
    
    model = FactorizationMachine(field_dims, embed_dim=16)
    
    # 模拟输入 (feature indices)
    x = torch.randint(0, 100, (batch_size, 1))  # user
    x = torch.cat([x, torch.randint(0, 200, (batch_size, 1))], dim=1)  # item
    x = torch.cat([x, torch.randint(0, 20, (batch_size, 1))], dim=1)   # family
    
    # 前向
    output = model(x)
    
    print(f"✅ FM测试通过")
    print(f"  输入: {x.shape}")
    print(f"  输出: {output.shape}")
    print(f"  输出范围: [{output.min():.3f}, {output.max():.3f}]")
    
    assert output.shape == (batch_size,), f"输出形状错误: {output.shape}"
    assert not torch.isnan(output).any(), "输出包含NaN"
    
    return True


def test_deepfm():
    """测试DeepFM"""
    print("\n" + "="*50)
    print("测试2: DeepFM")
    print("="*50)
    
    field_dims = [100, 200, 20, 50]  # user, item, family, function
    batch_size = 64
    
    model = DeepFM(field_dims, embed_dim=16, mlp_dims=[128, 64])
    
    # 模拟输入
    x = torch.stack([
        torch.randint(0, dim, (batch_size,))
        for dim in field_dims
    ], dim=1)
    
    # 前向
    output = model(x)
    
    print(f"✅ DeepFM测试通过")
    print(f"  输入: {x.shape}")
    print(f"  输出: {output.shape}")
    print(f"  输出范围: [{output.min():.3f}, {output.max():.3f}]")
    
    # 检查输出范围 (sigmoid后应在0-1)
    assert output.min() >= 0 and output.max() <= 1, "输出不在[0,1]范围内"
    
    return True


def test_reranker():
    """测试ProteinReranker完整流程"""
    print("\n" + "="*50)
    print("测试3: ProteinReranker完整流程")
    print("="*50)
    
    field_dims = [100, 200, 20]
    
    # 创建reranker
    reranker = ProteinReranker(field_dims, embed_dim=16)
    
    # 生成训练数据
    n_samples = 1000
    train_x = torch.stack([
        torch.randint(0, dim, (n_samples,))
        for dim in field_dims
    ], dim=1)
    
    # 模拟标签 (0/1)
    train_y = torch.rand(n_samples)
    train_y = (train_y > 0.5).float()
    
    # 训练
    reranker.fit(train_x, train_y, epochs=50, batch_size=128)
    
    # 生成候选集
    n_candidates = 100
    candidates = torch.stack([
        torch.randint(0, dim, (n_candidates,))
        for dim in field_dims
    ], dim=1)
    
    # 重排序
    top_indices, top_scores = reranker.rerank(candidates, top_k=10)
    
    print(f"✅ Reranker测试通过")
    print(f"  候选集: {candidates.shape}")
    print(f"  Top-K索引: {top_indices.shape}")
    print(f"  Top-K分数: {top_scores.shape}")
    print(f"  Top-3分数: {top_scores[:3].tolist()}")
    
    assert len(top_indices) == 10, "Top-K数量错误"
    assert len(top_scores) == 10, "分数数量错误"
    
    return True


def test_save_load():
    """测试模型保存加载"""
    print("\n" + "="*50)
    print("测试4: 模型保存/加载")
    print("="*50)
    
    import tempfile
    import os
    
    field_dims = [50, 100, 20]
    
    # 创建并训练模型
    reranker1 = ProteinReranker(field_dims, embed_dim=8)
    
    train_x = torch.stack([
        torch.randint(0, dim, (500,))
        for dim in field_dims
    ], dim=1)
    train_y = torch.rand(500)
    
    reranker1.fit(train_x, train_y, epochs=20, batch_size=64)
    
    # 测试前向
    test_x = torch.stack([
        torch.randint(0, dim, (10,))
        for dim in field_dims
    ], dim=1)
    
    reranker1.model.eval()
    with torch.no_grad():
        output1 = reranker1.model(test_x)
    
    # 保存
    with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
        temp_path = f.name
    
    reranker1.save(temp_path)
    
    # 加载到新模型
    reranker2 = ProteinReranker(field_dims, embed_dim=8)
    reranker2.load(temp_path)
    
    reranker2.model.eval()
    with torch.no_grad():
        output2 = reranker2.model(test_x)
    
    # 清理
    os.unlink(temp_path)
    
    # 比较输出
    diff = torch.abs(output1 - output2).max()
    
    print(f"✅ 保存/加载测试通过")
    print(f"  输出差异: {diff:.6f}")
    
    assert diff < 1e-6, f"保存加载后输出不一致: {diff}"
    
    return True


if __name__ == '__main__':
    print("="*60)
    print("FM精排层 - 单元测试")
    print("="*60)
    
    torch.manual_seed(42)
    np.random.seed(42)
    
    try:
        test_fm()
        test_deepfm()
        test_reranker()
        test_save_load()
        
        print("\n" + "="*60)
        print("✅ 所有单元测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise