"""图表生成模块 - 使用PIL生成股票走势图"""
import io
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict


def generate_stock_chart(stock_name: str, price_data: List[Dict], width: int = 800, height: int = 500) -> bytes:
    """
    生成股票走势图
    
    Args:
        stock_name: 股票名称
        price_data: 价格数据列表，每个元素包含 'timestamp' 和 'price'
        width: 图片宽度
        height: 图片高度
    
    Returns:
        图片字节数据
    """
    if not price_data:
        # 生成空数据提示图
        return generate_empty_chart(stock_name, width, height)
    
    # 创建图片
    img = Image.new('RGB', (width, height), color=(30, 30, 30))  # 深色背景
    draw = ImageDraw.Draw(img)
    
    # 边距
    margin_left = 80
    margin_right = 40
    margin_top = 60
    margin_bottom = 80
    
    # 绘图区域
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    
    # 获取价格范围
    prices = [d['price'] for d in price_data]
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price if max_price != min_price else 1
    
    # 添加一些边距到价格范围
    price_padding = price_range * 0.1
    min_price -= price_padding
    max_price += price_padding
    price_range = max_price - min_price
    
    # 绘制标题 - 使用支持中文的字体
    try:
        # 优先使用支持中文的 Noto Sans CJK
        title_font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc", 28)
        price_font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 16)
        label_font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 12)
    except:
        try:
            # 备用：使用 DejaVu 字体（不支持中文，但英文显示更好）
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            # 如果都找不到，使用默认字体
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
    
    # 标题
    title = f"📈 {stock_name} 价格走势"
    draw.text((width // 2 - 150, 15), title, fill=(255, 255, 255), font=title_font)
    
    # 统计信息
    current_price = prices[-1]
    start_price = prices[0]
    change = current_price - start_price
    change_pct = (change / start_price * 100) if start_price > 0 else 0
    
    # 根据涨跌选择颜色
    if change >= 0:
        color = (0, 255, 100)  # 绿色（涨）
    else:
        color = (255, 80, 80)  # 红色（跌）
    
    # 绘制统计信息
    stats_text = f"当前: {current_price:.2f} | 最高: {max(prices):.2f} | 最低: {min(prices):.2f} | 涨跌: {change:+.2f} ({change_pct:+.2f}%)"
    draw.text((margin_left, 50), stats_text, fill=(200, 200, 200), font=price_font)
    
    # 绘制网格线
    grid_color = (60, 60, 60)
    for i in range(6):
        y = margin_top + (chart_height * i // 5)
        draw.line([(margin_left, y), (margin_left + chart_width, y)], fill=grid_color, width=1)
    
    # 绘制Y轴价格标签
    for i in range(6):
        price_val = max_price - (price_range * i / 5)
        y = margin_top + (chart_height * i // 5)
        price_text = f"{price_val:.1f}"
        draw.text((10, y - 8), price_text, fill=(150, 150, 150), font=label_font)
    
    # 绘制价格走势线
    if len(price_data) > 1:
        points = []
        for i, data in enumerate(price_data):
            x = margin_left + (chart_width * i // (len(price_data) - 1))
            y = margin_top + chart_height - ((data['price'] - min_price) / price_range * chart_height)
            points.append((x, int(y)))
        
        # 绘制线条
        if len(points) > 1:
            draw.line(points, fill=color, width=3)
        
        # 绘制数据点
        for i, (x, y) in enumerate(points):
            if i % max(1, len(points) // 10) == 0:  # 只显示部分点，避免太密集
                draw.ellipse([(x-4, y-4), (x+4, y+4)], fill=color, outline=(255, 255, 255), width=2)
    
    # 绘制X轴时间标签（只显示首尾）
    if len(price_data) > 0:
        first_time = price_data[0]['timestamp'].split()[1] if ' ' in price_data[0]['timestamp'] else price_data[0]['timestamp'][-5:]
        last_time = price_data[-1]['timestamp'].split()[1] if ' ' in price_data[-1]['timestamp'] else price_data[-1]['timestamp'][-5:]
        
        draw.text((margin_left, height - 60), first_time, fill=(150, 150, 150), font=label_font)
        draw.text((width - margin_right - 50, height - 60), last_time, fill=(150, 150, 150), font=label_font)
    
    # 绘制边框
    draw.rectangle([(margin_left, margin_top), (margin_left + chart_width, margin_top + chart_height)], 
                   outline=(100, 100, 100), width=2)
    
    # 保存为字节
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def generate_empty_chart(stock_name: str, width: int = 800, height: int = 500) -> bytes:
    """生成空数据提示图"""
    img = Image.new('RGB', (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    # 使用支持中文的字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc", 32)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()

    text = f"📈 {stock_name}\n暂无价格数据"
    draw.text((width // 2 - 150, height // 2 - 40), text, fill=(200, 200, 200), font=font)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
