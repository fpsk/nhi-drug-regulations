import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from backend.indexer import NHIIndexer
from backend.parser import NHIRegulationParser
from backend.atc_engine import ATCEngine

app = Flask(__name__, static_folder="../public", static_url_path="")
app.config['UPLOAD_FOLDER'] = '../uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

indexer = NHIIndexer(data_dir="okf_data")
parser = NHIRegulationParser(output_dir="okf_data")
atc_engine = ATCEngine()

@app.route('/')
def index():
    return send_from_directory('../public', 'index.html')

@app.route('/mobile')
@app.route('/mobile.html')
def mobile_index():
    return send_from_directory('../public', 'mobile.html')

@app.route('/api/version', methods=['GET'])
def api_version():
    return jsonify({
        "status": "success",
        "app_name": "Taiwan NHI Drug Regulations Query Engine",
        "version": "2026.06.30-v2",
        "latest_features": "Forteo / Teriparatide / H05AA02 relevance boosting + Neo4j Graph Export",
        "total_regulations": len(indexer.regulations),
        "who_atc_items": len(atc_engine.who_db),
        "atc_db_items": len(atc_engine.atc_db)
    })

@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '')
    chapter = request.args.get('chapter', None)
    lab = request.args.get('lab', None)
    limit_param = request.args.get('limit', '6')
    offset_param = request.args.get('offset', '0')
    
    try:
        limit = int(limit_param)
    except ValueError:
        limit = 6
        
    try:
        offset = int(offset_param)
    except ValueError:
        offset = 0

    results = indexer.search(query, chapter_filter=chapter, lab_filter=lab)
    total_count = len(results)
    
    if query.strip() and total_count > limit:
        display_results = results[offset : offset + limit]
        has_more = (offset + limit) < total_count
        is_limited = True
    else:
        display_results = results[offset : offset + limit] if query.strip() else results[:50]
        has_more = False if not query.strip() else (offset + limit) < total_count
        is_limited = False

    return jsonify({
        "status": "success",
        "total_count": total_count,
        "count": len(display_results),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "is_limited": is_limited,
        "results": display_results
    })

@app.route('/api/chapters', methods=['GET'])
def api_chapters():
    chapters = set([r["chapter"] for r in indexer.regulations])
    return jsonify({
        "status": "success",
        "chapters": sorted(list(chapters)),
        "total_regulations": len(indexer.regulations)
    })

@app.route('/api/atc/expand', methods=['GET'])
def api_atc_expand():
    query = request.args.get('q', '')
    expansions = atc_engine.expand_query(query)
    return jsonify({
        "status": "success",
        "expansions": expansions
    })

@app.route('/api/upload', methods=['POST'])
def api_upload():
    # Admin password security check
    password = request.form.get('password', '')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'nhi2026')
    if password != admin_password:
        return jsonify({"status": "error", "message": "管理員密碼錯誤！無法更新法規文件 (Invalid Password)"}), 401

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "未選擇上傳檔案"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "檔名空白"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == '.docx':
            recs = parser.parse_docx(filepath)
        elif ext == '.pdf':
            recs = parser.parse_pdf(filepath)
        else:
            return jsonify({"status": "error", "message": "格式不符。僅支援 .docx 與 .pdf 檔案"}), 400
            
        generated_files = parser.save_to_okf_yaml(recs)
        indexer.load_and_index()
        
        return jsonify({
            "status": "success",
            "message": f"成功解構並更新給付規定知識庫 (來自 {filename})",
            "records_count": len(recs),
            "generated_files": [os.path.basename(f) for f in generated_files]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting NHI Regulation Web Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
