# 多语言词汇学习系统

基于 **Python + Streamlit + SQLite + SM-2 间隔重复算法** 的 Web 背单词应用，
参考「不背单词」的新词学习与复习逻辑。

## 功能
- 多语言：英语 / 日语
- 词书：英语四级、英语六级、日语 JLPT N5、JLPT N2
- 新词学习：单词卡片（音标/假名、词性、释义、例句、同义词、派生词）+ TTS 发音
- 复习模式：SM-2 算法自动安排，认识/模糊/不认识三档反馈
- 选择题测试
- 学习统计：学习曲线、正确率图表
- 数据持久化：SQLite 本地数据库
- 音频本地缓存：edge-tts 生成一次，离线可再听

## 运行方法
```bash
# 1. 安装依赖（已装过可跳过）
pip install -r requirements.txt

# 2. 启动
streamlit run app.py
```
浏览器会自动打开 http://localhost:8501

## 目录结构
```
vocab_app/
├── app.py          # Streamlit 主程序
├── config.py       # 配置：词书、音色、API 密钥
├── db.py           # 数据库与词书导入
├── sm2.py          # SM-2 间隔重复算法
├── tts.py          # edge-tts 发音 + 音频缓存
├── translator.py   # 百度翻译 API（可选）
├── data/           # 词书 CSV
├── audio/          # 音频缓存
└── vocab.db        # 数据库（运行后自动生成）
```

## 关于百度翻译 API（可选）
1. 访问 https://fanyi-api.baidu.com/ 注册个人开发者（免费额度）
2. 拿到 APPID 和密钥
3. 打开 `config.py`，填入：
   ```python
   BAIDU_APPID = "你的APPID"
   BAIDU_KEY = "你的密钥"
   ```
不填也能正常使用，只是例句/同义词用内置词书数据。

## 词书扩充
直接编辑 `data/` 下的 CSV，字段：
`word,phonetic,pos,meaning,example,synonyms,derivatives`
删掉 `vocab.db` 后重启即可重新导入。
