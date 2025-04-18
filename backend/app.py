from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import pandas as pd
from utils import read_price_data, calculate_monthly_profit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='/static')

# 添加请求频率限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 强制HTTPS
Talisman(app, force_https=True, content_security_policy={
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
    'style-src': "'self' 'unsafe-inline'",
})

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")  # 限制上传频率
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 保存文件
            file.save(filepath)
            print(f"文件已保存到: {filepath}")
            
            try:
                # 读取和验证数据
                df = read_price_data(filepath)
                print("数据读取成功")
                
                # 获取策略
                strategy = request.form.get('strategy', 'one_charge_one_discharge')
                print(f"使用策略: {strategy}")
                
                # 计算收益
                results = calculate_monthly_profit(df, strategy)
                print(f"计算完成，总收益: {results['total_profit']}")
                
                # 返回完整的结果数据
                return jsonify({
                    'success': True,
                    'total_profit': results['total_profit'],
                    'daily_profits': results['daily_profits'],
                    'total_days': results['total_days'],
                    'chart_data': results['chart_data']
                })
                
            except Exception as e:
                print(f"处理文件时出错: {str(e)}")
                return jsonify({'error': f"处理文件时出错: {str(e)}"}), 400
            
            finally:
                # 清理上传的文件
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        print(f"文件已删除: {filepath}")
                except Exception as e:
                    print(f"删除文件时出错: {str(e)}")
        
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            return jsonify({'error': f"保存文件时出错: {str(e)}"}), 400
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件大小超过限制（最大16MB）'}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': '请求过于频繁，请稍后再试'}), 429

if __name__ == '__main__':
    # 在生产环境中，应该使用生产级别的WSGI服务器
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        app.run(debug=True, port=5002) 