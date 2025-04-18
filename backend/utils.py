import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def read_price_data(file_path):
    """Read and validate price data from Excel or CSV file.
    
    Assumes data format:
    - First row contains headers (will be skipped)
    - First column is timestamp in format 'YYYY/M/D HH:MM' (e.g., '2024/1/1 00:00')
    - Second column contains price data
    """
    try:
        # 读取文件
        print(f"开始读取文件: {file_path}")
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            print(f"文件读取失败: {str(e)}")
            raise ValueError(f"无法读取文件，请确保文件格式正确（Excel或CSV）。错误: {str(e)}")
            
        print(f"文件读取成功，原始列名: {df.columns.tolist()}")
        print(f"数据形状: {df.shape}")
        
        # 重命名列并跳过第一行
        try:
            df.columns = ['Timestamp', 'Price']
            df = df.iloc[1:]  # 跳过第一行（表头）
            df = df.reset_index(drop=True)  # 重置索引
        except Exception as e:
            print(f"重命名列或跳过表头失败: {str(e)}")
            raise ValueError("处理数据结构时出错，请确保文件格式正确")
        
        print("处理后的前5行数据:")
        print(df.head().to_string())
        
        # 确保价格列为数值类型
        try:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
            null_prices = df['Price'].isnull().sum()
            if null_prices > 0:
                print(f"警告: 发现{null_prices}个无效价格数据")
                print("无效价格数据所在行:")
                print(df[df['Price'].isnull()].head())
                raise ValueError("价格列包含无效数据")
        except Exception as e:
            print(f"价格数据转换失败: {str(e)}")
            raise ValueError("价格数据格式错误，请确保所有价格为数值类型")
            
        # 转换时间戳
        try:
            print("开始转换时间戳")
            print("时间戳示例:", df['Timestamp'].head().tolist())
            
            # 转换时间戳为datetime格式
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y/%m/%d %H:%M')
            print("时间戳转换成功")
            print("转换后的时间戳示例:", df['Timestamp'].head().tolist())
            
            # 获取数据的时间范围
            start_time = df['Timestamp'].min()
            end_time = df['Timestamp'].max()
            print(f"数据时间范围: {start_time} 到 {end_time}")
            
            # 按时间排序
            df = df.sort_values('Timestamp')
            
        except Exception as e:
            print(f"时间戳转换失败: {str(e)}")
            print("请确保时间戳格式为 'YYYY/M/D HH:MM'")
            raise ValueError("时间戳格式错误")
        
        return df
    
    except Exception as e:
        print(f"处理文件时出现错误: {str(e)}")
        raise ValueError(f"处理文件时出错: {str(e)}")

def find_optimal_windows(prices, window_size=24, exclude_ranges=None):
    """在一天内找到最优的充放电时间窗口。
    
    Args:
        prices: 一天的价格数据（DataFrame with Timestamp and Price columns）
        window_size: 时间窗口大小（默认24个间隔，即2小时）
        exclude_ranges: 要排除的时间范围列表，每个范围是(start_idx, end_idx)的元组
    
    Returns:
        tuple: (最低价时间窗口, 最高价时间窗口, 最低价, 最高价)
    """
    if len(prices) < window_size * 2:
        print(f"数据点不足，需要至少 {window_size * 2} 个点，当前只有 {len(prices)} 个点")
        return None, None, None, None
        
    min_price = float('inf')
    max_price = float('-inf')
    min_window = None
    max_window = None
    
    # 确保数据按时间排序
    prices = prices.sort_values('Timestamp').reset_index(drop=True)
    
    # 创建可用时间段的掩码
    valid_times = pd.Series(True, index=range(len(prices)))
    if exclude_ranges:
        for start_idx, end_idx in exclude_ranges:
            valid_times.iloc[start_idx:end_idx+1] = False
    
    # 遍历所有可能的2小时窗口，寻找最低价时段
    for i in range(len(prices) - window_size + 1):
        # 检查这个窗口是否与已排除的时间段重叠
        if not valid_times.iloc[i:i+window_size].all():
            continue
            
        window = prices.iloc[i:i+window_size]
        avg_price = window['Price'].mean()
        
        if avg_price < min_price:
            min_price = avg_price
            min_window = (i, i + window_size - 1)
    
    # 在充电时间窗口之后寻找放电时间窗口
    if min_window:
        for i in range(min_window[1] + 1, len(prices) - window_size + 1):
            # 检查这个窗口是否与已排除的时间段重叠
            if not valid_times.iloc[i:i+window_size].all():
                continue
                
            window = prices.iloc[i:i+window_size]
            avg_price = window['Price'].mean()
            
            if avg_price > max_price:
                max_price = avg_price
                max_window = (i, i + window_size - 1)
    
    return min_window, max_window, min_price, max_price

def find_two_charge_discharge_windows(df):
    """在一天内找到两组最优的充放电时间窗口。
    
    Args:
        df: 一天的价格数据
    
    Returns:
        list: 包含两组充放电窗口的列表
    """
    try:
        print(f"开始寻找两组充放电窗口，数据点数量: {len(df)}")
        windows = []
        window_size = 24  # 2小时 = 24个5分钟间隔
        
        # 确保数据按时间排序
        df = df.sort_values('Timestamp').reset_index(drop=True)
        
        # 第一组充放电窗口
        print("寻找第一组充放电窗口...")
        min_window1, max_window1, min_price1, max_price1 = find_optimal_windows(df, window_size)
        
        if all(x is not None for x in [min_window1, max_window1, min_price1, max_price1]):
            print(f"找到第一组窗口 - 充电时段: {min_window1}, 放电时段: {max_window1}")
            
            # 添加第一组窗口
            windows.append({
                'charge_start': df.iloc[min_window1[0]]['Timestamp'].strftime('%H:%M'),
                'charge_end': df.iloc[min_window1[1]]['Timestamp'].strftime('%H:%M'),
                'discharge_start': df.iloc[max_window1[0]]['Timestamp'].strftime('%H:%M'),
                'discharge_end': df.iloc[max_window1[1]]['Timestamp'].strftime('%H:%M'),
                'charge_price': round(min_price1, 2),
                'discharge_price': round(max_price1, 2),
                'profit': round((max_price1 - min_price1) * 1, 2)  # 1MWh
            })
            print("第一组窗口添加成功")
            
            # 移除已使用的时间段
            used_times = set(range(min_window1[0], min_window1[1] + 1)) | set(range(max_window1[0], max_window1[1] + 1))
            remaining_df = df[~df.index.isin(used_times)].reset_index(drop=True)
            
            # 第二组充放电窗口
            if len(remaining_df) >= window_size * 2:
                print("寻找第二组充放电窗口...")
                min_window2, max_window2, min_price2, max_price2 = find_optimal_windows(remaining_df, window_size)
                
                if all(x is not None for x in [min_window2, max_window2, min_price2, max_price2]):
                    print(f"找到第二组窗口 - 充电时段: {min_window2}, 放电时段: {max_window2}")
                    
                    windows.append({
                        'charge_start': remaining_df.iloc[min_window2[0]]['Timestamp'].strftime('%H:%M'),
                        'charge_end': remaining_df.iloc[min_window2[1]]['Timestamp'].strftime('%H:%M'),
                        'discharge_start': remaining_df.iloc[max_window2[0]]['Timestamp'].strftime('%H:%M'),
                        'discharge_end': remaining_df.iloc[max_window2[1]]['Timestamp'].strftime('%H:%M'),
                        'charge_price': round(min_price2, 2),
                        'discharge_price': round(max_price2, 2),
                        'profit': round((max_price2 - min_price2) * 1, 2)  # 1MWh
                    })
                    print("第二组窗口添加成功")
                else:
                    print("未找到合适的第二组充放电窗口")
            else:
                print(f"剩余数据点数量({len(remaining_df)})不足以进行第二次搜索(需要{window_size * 2}个点)")
        else:
            print("未找到合适的第一组充放电窗口")
        
        print(f"找到的充放电窗口总数: {len(windows)}")
        return windows
        
    except Exception as e:
        print(f"寻找充放电窗口时出错: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        return []

def calculate_daily_profit(df, strategy='one_charge_one_discharge'):
    """计算单日收益。
    
    Args:
        df: 当天的价格数据
        strategy: 'one_charge_one_discharge' 或 'two_charge_two_discharge'
    
    Returns:
        dict: 包含充放电时间和收益的字典
    """
    try:
        if strategy == 'one_charge_one_discharge':
            min_window, max_window, charge_price, discharge_price = find_optimal_windows(df)
            if all(x is not None for x in [min_window, max_window, charge_price, discharge_price]):
                profit = round((discharge_price - charge_price) * 1, 2)  # 1MWh
                return {
                    'charge_start': df.iloc[min_window[0]]['Timestamp'].strftime('%H:%M'),
                    'charge_end': df.iloc[min_window[1]]['Timestamp'].strftime('%H:%M'),
                    'discharge_start': df.iloc[max_window[0]]['Timestamp'].strftime('%H:%M'),
                    'discharge_end': df.iloc[max_window[1]]['Timestamp'].strftime('%H:%M'),
                    'charge_price': round(charge_price, 2),
                    'discharge_price': round(discharge_price, 2),
                    'profit': profit,
                    'price_diff': round(discharge_price - charge_price, 2)
                }
        
        elif strategy == 'two_charge_two_discharge':
            print(f"\n计算两次充放电收益 - 数据点数量: {len(df)}")
            
            # 第一次充放电
            min_window1, max_window1, charge_price1, discharge_price1 = find_optimal_windows(df)
            if not all(x is not None for x in [min_window1, max_window1, charge_price1, discharge_price1]):
                print("未找到第一组有效的充放电窗口")
                return None
                
            profit1 = round((discharge_price1 - charge_price1) * 1, 2)  # 第一次收益
            print(f"第一次充放电收益: ${profit1:.2f}")
            
            # 第二次充放电（排除第一次使用的时间段）
            exclude_ranges = [(min_window1[0], min_window1[1]), (max_window1[0], max_window1[1])]
            min_window2, max_window2, charge_price2, discharge_price2 = find_optimal_windows(df, exclude_ranges=exclude_ranges)
            
            if all(x is not None for x in [min_window2, max_window2, charge_price2, discharge_price2]):
                profit2 = round((discharge_price2 - charge_price2) * 1, 2)  # 第二次收益
                print(f"第二次充放电收益: ${profit2:.2f}")
                total_profit = round(profit1 + profit2, 2)
                
                # 返回格式与一次充放电相同，但包含两次操作的总收益
                return {
                    'charge_start': df.iloc[min_window1[0]]['Timestamp'].strftime('%H:%M'),
                    'charge_end': df.iloc[min_window1[1]]['Timestamp'].strftime('%H:%M'),
                    'discharge_start': df.iloc[max_window1[0]]['Timestamp'].strftime('%H:%M'),
                    'discharge_end': df.iloc[max_window1[1]]['Timestamp'].strftime('%H:%M'),
                    'charge_price': round(charge_price1, 2),
                    'discharge_price': round(discharge_price1, 2),
                    'second_charge_start': df.iloc[min_window2[0]]['Timestamp'].strftime('%H:%M'),
                    'second_charge_end': df.iloc[min_window2[1]]['Timestamp'].strftime('%H:%M'),
                    'second_discharge_start': df.iloc[max_window2[0]]['Timestamp'].strftime('%H:%M'),
                    'second_discharge_end': df.iloc[max_window2[1]]['Timestamp'].strftime('%H:%M'),
                    'second_charge_price': round(charge_price2, 2),
                    'second_discharge_price': round(discharge_price2, 2),
                    'profit': total_profit,
                    'price_diff': round(max(discharge_price1 - charge_price1, discharge_price2 - charge_price2), 2)
                }
            else:
                print("未找到第二组有效的充放电窗口，仅使用第一组结果")
                return {
                    'charge_start': df.iloc[min_window1[0]]['Timestamp'].strftime('%H:%M'),
                    'charge_end': df.iloc[min_window1[1]]['Timestamp'].strftime('%H:%M'),
                    'discharge_start': df.iloc[max_window1[0]]['Timestamp'].strftime('%H:%M'),
                    'discharge_end': df.iloc[max_window1[1]]['Timestamp'].strftime('%H:%M'),
                    'charge_price': round(charge_price1, 2),
                    'discharge_price': round(discharge_price1, 2),
                    'profit': profit1,
                    'price_diff': round(discharge_price1 - charge_price1, 2)
                }
        
        return None
        
    except Exception as e:
        print(f"计算收益时出错: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        return None

def calculate_monthly_profit(df, strategy='one_charge_one_discharge'):
    """计算整月收益。
    
    Args:
        df: 包含整月数据的DataFrame
        strategy: 充放电策略
    
    Returns:
        dict: 包含每日收益和总收益的字典
    """
    daily_profits = []
    total_profit = 0
    price_diffs = []
    dates = []
    
    # 按天分组处理数据
    print(f"开始处理每日数据，总共 {len(df['Timestamp'].dt.date.unique())} 天")
    
    for date, day_data in df.groupby(df['Timestamp'].dt.date):
        print(f"处理日期: {date}, 数据点数量: {len(day_data)}")
        
        # 确保日期数据按时间排序
        day_data = day_data.sort_values('Timestamp')
        
        result = calculate_daily_profit(day_data, strategy)
        if result:
            daily_result = {
                'date': date.strftime('%Y-%m-%d'),
                'profit': result['profit'],
                'price_diff': result['price_diff']
            }
            
            # 添加充放电时间信息
            for key in ['charge_start', 'charge_end', 'discharge_start', 'discharge_end',
                       'charge_price', 'discharge_price']:
                if key in result:
                    daily_result[key] = result[key]
            
            # 如果是两次充放电，添加第二次的时间信息
            if strategy == 'two_charge_two_discharge':
                for key in ['second_charge_start', 'second_charge_end', 'second_discharge_start',
                          'second_discharge_end', 'second_charge_price', 'second_discharge_price']:
                    if key in result:
                        daily_result[key] = result[key]
            
            daily_profits.append(daily_result)
            total_profit += result['profit']
            price_diffs.append(result['price_diff'])
            dates.append(date.strftime('%Y-%m-%d'))
            
            print(f"日期 {date} 的收益: ${result['profit']:.2f}")
        else:
            print(f"警告: 日期 {date} 没有找到有效的充放电时间窗口")
    
    print(f"计算完成，总收益: ${total_profit:.2f}")
    print(f"处理天数: {len(daily_profits)}")
    
    # 计算累计收益列表
    cumulative_profits = []
    current_total = 0
    for profit in [d['profit'] for d in daily_profits]:
        current_total += profit
        cumulative_profits.append(round(current_total, 2))
    
    return {
        'total_profit': round(total_profit, 2),
        'daily_profits': daily_profits,
        'total_days': len(daily_profits),
        'chart_data': {
            'dates': dates,
            'price_diffs': price_diffs,
            'daily_profits': [d['profit'] for d in daily_profits],
            'cumulative_profits': cumulative_profits
        }
    } 