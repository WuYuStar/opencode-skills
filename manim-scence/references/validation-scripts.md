# Manim Composer - 验证脚本

## Python布局验证脚本

### 完整验证脚本

```python
def check_card_overlap(cards):
    """
    检查卡片是否重叠
    
    Args:
        cards: 列表，每个元素是字典，包含：
            - name: 卡片名称
            - width: 宽度
            - height: 高度  
            - center: (x, y) 中心坐标
    
    Returns:
        (is_valid, message)
    """
    min_spacing = 0.2
    
    for i, card1 in enumerate(cards):
        for card2 in cards[i+1:]:
            # 计算边界
            c1_left = card1['center'][0] - card1['width']/2
            c1_right = card1['center'][0] + card1['width']/2
            c1_bottom = card1['center'][1] - card1['height']/2
            c1_top = card1['center'][1] + card1['height']/2
            
            c2_left = card2['center'][0] - card2['width']/2
            c2_right = card2['center'][0] + card2['width']/2
            c2_bottom = card2['center'][1] - card2['height']/2
            c2_top = card2['center'][1] + card2['height']/2
            
            # 计算间距
            horizontal_gap = min(
                c2_left - c1_right,  # card2在右边
                c1_left - c2_right   # card1在右边（负值表示重叠）
            )
            
            vertical_gap = min(
                c2_bottom - c1_top,   # card2在上边
                c1_bottom - c2_top    # card1在上边（负值表示重叠）
            )
            
            # 检查重叠（考虑间距要求）
            if horizontal_gap < min_spacing or vertical_gap < min_spacing:
                return False, f"卡片 '{card1['name']}' 和 '{card2['name']}' 重叠或间距不足"
    
    return True, "所有卡片间距符合要求"


def check_canvas_coverage(cards):
    """
    检查卡片是否铺满画布
    
    Returns:
        (is_valid, coverage_info)
    """
    canvas_width = 14
    canvas_height = 8
    
    # 计算总宽度和总高度（简化版：假设水平或垂直排列）
    # 实际情况可能需要更复杂的计算
    
    total_width = sum(c['width'] for c in cards)
    total_height = sum(c['height'] for c in cards)
    
    width_ratio = total_width / canvas_width
    height_ratio = total_height / canvas_height
    
    coverage_info = {
        'total_width': total_width,
        'total_height': total_height,
        'width_ratio': width_ratio,
        'height_ratio': height_ratio,
        'canvas_width': canvas_width,
        'canvas_height': canvas_height
    }
    
    # 允许 ±0.5 的误差
    is_valid = (0.7 <= width_ratio <= 1.1) and (0.7 <= height_ratio <= 1.1)
    
    return is_valid, coverage_info


def validate_layout(cards):
    """
    完整验证布局
    """
    print("=" * 50)
    print("卡片布局验证报告")
    print("=" * 50)
    
    # 检查重叠
    overlap_ok, overlap_msg = check_card_overlap(cards)
    print(f"\n1. 重叠检查: {'✓ PASS' if overlap_ok else '✗ FAIL'}")
    print(f"   {overlap_msg}")
    
    # 检查画布覆盖
    coverage_ok, coverage_info = check_canvas_coverage(cards)
    print(f"\n2. 画布覆盖检查: {'✓ PASS' if coverage_ok else '✗ FAIL'}")
    print(f"   画布尺寸: {coverage_info['canvas_width']} × {coverage_info['canvas_height']}")
    print(f"   卡片总面积: {coverage_info['total_width']:.1f} × {coverage_info['total_height']:.1f}")
    print(f"   宽度占比: {coverage_info['width_ratio']:.1%}")
    print(f"   高度占比: {coverage_info['height_ratio']:.1%}")
    
    # 检查单个卡片
    print(f"\n3. 单卡片检查:")
    for card in cards:
        print(f"   {card['name']}: {card['width']}×{card['height']} @ ({card['center'][0]}, {card['center'][1]})")
    
    print(f"\n{'=' * 50}")
    all_ok = overlap_ok and coverage_ok
    print(f"总体验证: {'✓ 通过' if all_ok else '✗ 未通过'}")
    print(f"{'=' * 50}")
    
    return all_ok


# 使用示例
if __name__ == "__main__":
    # 左右分屏布局示例
    cards_two_panel = [
        {'name': 'GraphCard', 'width': 6.5, 'height': 7.0, 'center': (-3.5, 0)},
        {'name': 'TextCard', 'width': 6.5, 'height': 7.0, 'center': (3.5, 0)},
    ]
    
    # 网格布局示例
    cards_grid = [
        {'name': 'Card1', 'width': 6.5, 'height': 3.3, 'center': (-3.5, 1.85)},
        {'name': 'Card2', 'width': 6.5, 'height': 3.3, 'center': (3.5, 1.85)},
        {'name': 'Card3', 'width': 6.5, 'height': 3.3, 'center': (-3.5, -1.85)},
        {'name': 'Card4', 'width': 6.5, 'height': 3.3, 'center': (3.5, -1.85)},
    ]
    
    print("示例1: 左右分屏布局")
    validate_layout(cards_two_panel)
    
    print("\n\n示例2: 网格布局")
    validate_layout(cards_grid)
```

---

## 手动验证检查表

### 快速验证步骤

**对于每个场景的布局：**

1. **列出所有卡片**：
   ```
   卡片1: 宽=___, 高=___, 中心=(___, ___)
   卡片2: 宽=___, 高=___, 中心=(___, ___)
   ...
   ```

2. **计算边界**（对每个卡片）：
   ```
   卡片1:
   - 左边界: center_x - width/2 = ___
   - 右边界: center_x + width/2 = ___
   - 下边界: center_y - height/2 = ___
   - 上边界: center_y + height/2 = ___
   ```

3. **检查每对卡片的间距**：
   ```
   卡片1 vs 卡片2:
   - 水平间距: min(卡片2左-卡片1右, 卡片1左-卡片2右) = ___
   - 垂直间距: min(卡片2下-卡片1上, 卡片1下-卡片2上) = ___
   - 结果: ___ ≥ 0.2 ?
   ```

4. **验证画布覆盖**：
   ```
   所有卡片宽度之和: ___ (目标: ≈14)
   所有卡片高度之和: ___ (目标: ≈8)
   ```

---

### 常见错误及修正

**错误1：间距计算为负数（重叠）**
```
问题: 卡片A右边界=2.0, 卡片B左边界=1.8
     间距 = 1.8 - 2.0 = -0.2 (重叠0.2单位)

修正:
- 方案A: 卡片A中心左移0.3单位
- 方案B: 卡片B中心右移0.3单位
- 方案C: 减小卡片宽度0.4单位
```

**错误2：未填满画布**
```
问题: 两个卡片总宽度=10，画布宽度=14
     两侧留白过大

修正:
- 增加卡片宽度
- 或添加第3个卡片
- 或调整位置使分布更均匀
```

**错误3：超出画布边界**
```
问题: 卡片中心=6.5, 宽度=2, 右边界=7.5 > 7

修正:
- 中心左移至6.0或更小
- 或减小卡片宽度
```

---

## Manim调试代码片段

### 添加调试边框

```python
# 在创建卡片时添加透明边框
from manim import *

def create_card_with_debug_border(width, height, center, color=BLUE):
    """创建带调试边框的卡片"""
    card = Rectangle(
        width=width, 
        height=height,
        stroke_color=color, 
        stroke_opacity=0.3,  # 半透明边框
        stroke_width=2,
        fill_color=BLACK, 
        fill_opacity=0.8
    ).move_to((center[0], center[1], 0))
    
    # 添加中心点标记
    center_dot = Dot(
        point=(center[0], center[1], 0),
        color=color,
        radius=0.05
    )
    
    return VGroup(card, center_dot)

# 使用示例
graph_card = create_card_with_debug_border(6.5, 7.0, (-3.5, 0), BLUE)
text_card = create_card_with_debug_border(6.5, 7.0, (3.5, 0), GREEN)

self.play(Create(graph_card), Create(text_card))
```

### 显示边界信息

```python
def show_boundary_info(cards, scene):
    """在场景中显示边界信息（用于调试）"""
    for card in cards:
        left = card['center'][0] - card['width']/2
        right = card['center'][0] + card['width']/2
        bottom = card['center'][1] - card['height']/2
        top = card['center'][1] + card['height']/2
        
        # 在卡片角落显示边界值
        label = Text(
            f"L:{left:.1f}\nR:{right:.1f}\nB:{bottom:.1f}\nT:{top:.1f}",
            font_size=12,
            color=YELLOW
        ).move_to((card['center'][0], card['center'][1], 0))
        
        scene.add(label)
```
