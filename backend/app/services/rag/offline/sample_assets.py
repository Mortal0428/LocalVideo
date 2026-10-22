"""
CinemaAgent 开箱即用内置示范剧本与 SRT 字幕资产包 (Sample Assets & Seeder)
内置《千金归来：逆袭之巅》标准多集分镜剧本、高保真 SRT 时间轴字幕与人物图谱设定集。
一键灌库即可完成离线知识工程切片、向量索引与 Neo4j 图数据库三元组构建。
"""

import os
import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.rag_corpus import RAGCorpus, RAGChunk
from app.services.rag.offline.chunker import chunker
from app.services.rag.offline.embedder import embedder
from app.services.rag.offline.graph_extractor import graph_extractor

logger = logging.getLogger(__name__)

PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "preset_corpus")

SAMPLE_DRAMA_ID = "drama-qianjin-001"
SAMPLE_DRAMA_TITLE = "《千金归来：逆袭之巅》"

SAMPLE_SRT_EPISODE_1 = """1
00:00:05,000 --> 00:00:09,500
[京海市中心医院 VIP 检验科，深夜暴雨倾盆]

2
00:00:15,000 --> 00:00:22,000
主治医生颤抖递上报告：苏董事长，这份加急 DNA 报告证实，苏婉儿与您并无生物学亲子关系！

3
00:00:35,000 --> 00:00:43,000
苏正国拍案震怒：什么？！当年在红星妇幼保健院，当真是有人故意调换了我的亲生骨肉？！

4
00:01:05,000 --> 00:01:14,000
特助林峰上前低语：查到了！真正的苏家大小姐苏倾城，如今正在林氏百货当底层收银员，受尽欺凌！

5
00:01:25,000 --> 00:01:35,000
[镜头切换：豪门会所暗处] 苏婉儿面目狰狞：就算她是真千金又如何？顾夜白的心上人永远只能是我！

6
00:01:50,000 --> 00:02:00,000
苏婉儿密谋指使黑衣人：无论用什么手段，绝不能让苏倾城活着回到京海苏家大院！

7
00:02:15,000 --> 00:02:26,000
顾夜白冷眸如冰当众现身：苏婉儿，你冒领救命玉佩欺瞒顾家整整三年，今日婚约彻底作废！

8
00:02:35,000 --> 00:02:46,000
顾夜白当众亮出至尊黑金卡护住苏倾城：二十年前在冰河救我的是苏倾城，动我未婚妻者，逐出京海！
"""

SAMPLE_SRT_EPISODE_2 = """1
00:00:08,000 --> 00:00:16,000
[苏氏集团七十周年寿宴大厅，宾客云集名流汇聚]

2
00:00:25,000 --> 00:00:35,000
苏婉儿身着高定礼服洋洋得意：爷爷，这是我特意从缅甸拍卖回来的帝王绿翡翠寿桃，价值三千万！

3
00:00:50,000 --> 00:01:02,000
鉴宝泰斗当场拆穿：荒谬！此乃注胶染色危地马拉假翡翠，成本不足千元，简直是以假乱真大不敬！

4
00:01:20,000 --> 00:01:32,000
大门轰然推开！苏倾城一袭素雅白裙踏光而来：爷爷，这是孙女为您寻回的百亿海外能源战略合作书！

5
00:01:45,000 --> 00:01:58,000
顾夜白率领京海黑衣卫随行保驾：顾氏集团追加千亿投资，只为赠予苏倾城作为回归贺礼！

6
00:02:20,000 --> 00:02:32,000
苏正国老泪纵横握住苏倾城双手：好孩子，眉眼间全是亡妻的影子，你才是我苏正国的亲生女儿！
"""

SAMPLE_SCRIPT_MAIN = """
【剧名】《千金归来：逆袭之巅》
【类型】豪门反转 / 真假千金 / 甜宠打脸 / 商战短剧
【核心角色人物谱】
1. 苏倾城：女主角，苏家货真价实的亲生千金。自幼被保姆林凤霞蓄意抱走调换，在底层艰辛长大，性格冷静隐忍、医商双绝。二十年前暴风雪夜曾在冰河中冒死救下少年顾夜白。
2. 顾夜白：男主角，京海第一豪门顾氏集团现任掌门人。性格清冷桀骜、权倾京海，对救命恩人矢志不渝，手握至尊黑金卡与军工商业帝国。
3. 苏婉儿：反面女二号，假千金。母亲是当年涉事护工林凤霞。心胸狭隘、贪图富贵，窃取苏倾城的暖玉信物冒充顾夜白未婚妻，多次雇凶企图暗害苏倾城。
4. 苏正国：苏氏集团董事长，苏倾城生父。性格严厉但极重亲情，得知真相后果断清除苏婉儿与其党羽。
5. 林凤霞：假千金生母，当年狸猫换太子惨剧的始作俑者，最终在第三集被警方与顾氏情报网缉拿归案。

【主线关键剧情节点与反转】
- 第一集：市中心医院加急 DNA 报告出炉，揭穿苏婉儿非亲生事实；顾夜白识破信物作假，当众退婚苏婉儿，誓死守护真千金苏倾城。
- 第二集：苏家七十周年大寿现场，苏婉儿假翡翠寿桃被当场打脸，苏倾城携百亿海外订单霸气归来，苏正国认女相拥。
- 第三集：顾氏集团与苏氏强强联合，林凤霞落网招供全部调换细节，顾夜白于外滩之巅十里红妆向苏倾城浪漫求婚。
"""

SAMPLE_ENTITIES = [
    {"label": "Character", "name": "苏倾城", "properties": {"role": "女主角", "identity": "苏家真千金", "ability": "医商双绝"}},
    {"label": "Character", "name": "顾夜白", "properties": {"role": "男主角", "identity": "顾氏财阀掌门人", "status": "京海商界霸主"}},
    {"label": "Character", "name": "苏婉儿", "properties": {"role": "反派假千金", "identity": "假冒千金", "traits": "心狠手辣"}},
    {"label": "Character", "name": "苏正国", "properties": {"role": "父亲", "identity": "苏氏集团董事长"}},
    {"label": "Character", "name": "林凤霞", "properties": {"role": "罪魁祸首", "identity": "当年涉案护工"}},
    {"label": "Item", "name": "暖玉信物", "properties": {"type": "认亲信物", "significance": "顾夜白少年信物"}},
    {"label": "Item", "name": "至尊黑金卡", "properties": {"type": "财阀信物", "authority": "动用千亿资金权力"}},
    {"label": "Item", "name": "加急DNA报告", "properties": {"type": "证据文书", "evidence": "非亲生生物学证明"}},
    {"label": "Faction", "name": "顾氏集团", "properties": {"type": "第一财阀", "city": "京海"}},
    {"label": "Faction", "name": "苏氏集团", "properties": {"type": "老牌豪门", "industry": "能源与百货"}}
]

SAMPLE_RELATIONS = [
    {"source": "苏倾城", "relation": "亲生父女", "target": "苏正国", "evidence": "加急DNA报告确认为亲生血脉"},
    {"source": "苏倾城", "relation": "深情守护", "target": "顾夜白", "evidence": "顾夜白视苏倾城为唯一一生挚爱"},
    {"source": "顾夜白", "relation": "求婚订婚", "target": "苏倾城", "evidence": "顾夜白在外滩之巅求婚苏倾城"},
    {"source": "苏婉儿", "relation": "宿命仇敌", "target": "苏倾城", "evidence": "苏婉儿多次雇凶谋害苏倾城"},
    {"source": "苏婉儿", "relation": "收养抱错", "target": "苏正国", "evidence": "被冒名顶替当了二十年苏家千金"},
    {"source": "苏婉儿", "relation": "血缘父母", "target": "林凤霞", "evidence": "林凤霞为苏婉儿亲生母亲"},
    {"source": "顾夜白", "relation": "背叛退婚", "target": "苏婉儿", "evidence": "当众揭穿苏婉儿作伪退婚"},
    {"source": "顾夜白", "relation": "掌控执掌", "target": "顾氏集团", "evidence": "顾夜白为顾氏集团最高掌门人"},
    {"source": "顾夜白", "relation": "持有道具", "target": "至尊黑金卡", "evidence": "手持至尊黑金卡震慑全场"},
    {"source": "苏正国", "relation": "掌控执掌", "target": "苏氏集团", "evidence": "苏正国为苏氏集团董事长"}
]


def seed_sample_assets(db: Session, force: bool = False) -> Dict[str, Any]:
    """
    一键灌入示范资产包：
    1. 写入知识库文档 (剧本大纲、第1集SRT、第2集SRT)
    2. 多策略切片并计算向量，持久化写入 rag_chunks
    3. SPO 实体三元组写入 Neo4j 与嵌入式图存储
    """
    existing = db.query(RAGCorpus).filter(RAGCorpus.drama_id == SAMPLE_DRAMA_ID).first()
    if existing and not force:
        logger.info("示范资产已存在，跳过重复灌库")
        total_chunks = db.query(RAGChunk).filter(RAGChunk.drama_id == SAMPLE_DRAMA_ID).count()
        return {
            "status": "already_exists",
            "drama_id": SAMPLE_DRAMA_ID,
            "title": SAMPLE_DRAMA_TITLE,
            "total_chunks": total_chunks
        }

    if existing and force:
        # 清除旧切片与文档
        db.query(RAGChunk).filter(RAGChunk.drama_id == SAMPLE_DRAMA_ID).delete()
        db.query(RAGCorpus).filter(RAGCorpus.drama_id == SAMPLE_DRAMA_ID).delete()
        db.commit()

    corpora_to_create = [
        {
            "title": f"{SAMPLE_DRAMA_TITLE} - 官方完整主线剧本与人物档案",
            "doc_type": "script",
            "content": SAMPLE_SCRIPT_MAIN,
            "episode_num": 1,
            "strategy": "parent_child"
        },
        {
            "title": f"{SAMPLE_DRAMA_TITLE} - 第1集 精准时间轴字幕 (DNA反转与当众退婚)",
            "doc_type": "srt_subtitle",
            "content": SAMPLE_SRT_EPISODE_1,
            "episode_num": 1,
            "strategy": "sentence_window"
        },
        {
            "title": f"{SAMPLE_DRAMA_TITLE} - 第2集 精准时间轴字幕 (寿宴当众打脸与亲女相认)",
            "doc_type": "srt_subtitle",
            "content": SAMPLE_SRT_EPISODE_2,
            "episode_num": 2,
            "strategy": "sentence_window"
        }
    ]

    # 加载行业指南与平台规则预制资产
    guide_path = os.path.join(PRESET_DIR, "drama_production_guide.md")
    if os.path.exists(guide_path):
        try:
            with open(guide_path, "r", encoding="utf-8") as gf:
                corpora_to_create.append({
                    "title": "行业规范 - 微短剧工业化制作与编剧节奏实战指南",
                    "doc_type": "guide",
                    "content": gf.read(),
                    "episode_num": 0,
                    "strategy": "fixed"
                })
        except Exception as e:
            logger.warning(f"读取短剧制作指南异常: {e}")

    policy_path = os.path.join(PRESET_DIR, "platform_policy_rules.md")
    if os.path.exists(policy_path):
        try:
            with open(policy_path, "r", encoding="utf-8") as pf:
                corpora_to_create.append({
                    "title": "平台规则 - 平台短剧创作者生态规则与分账激励制度",
                    "doc_type": "policy",
                    "content": pf.read(),
                    "episode_num": 0,
                    "strategy": "fixed"
                })
        except Exception as e:
            logger.warning(f"读取平台规则异常: {e}")

    total_chunks_saved = 0
    all_chunks_for_graph = []

    for c_info in corpora_to_create:
        corpus = RAGCorpus(
            drama_id=SAMPLE_DRAMA_ID,
            title=c_info["title"],
            doc_type=c_info["doc_type"],
            content=c_info["content"],
            metadata_json=json.dumps({"drama_title": SAMPLE_DRAMA_TITLE, "episode_num": c_info["episode_num"]}, ensure_ascii=False)
        )
        db.add(corpus)
        db.commit()
        db.refresh(corpus)

        # 执行切片
        docs = chunker.chunk(
            text=c_info["content"],
            strategy=c_info["strategy"],
            episode_num=c_info["episode_num"],
            drama_id=SAMPLE_DRAMA_ID
        )

        for idx, doc in enumerate(docs):
            vec = embedder.embed_text(doc.text)
            chunk_rec = RAGChunk(
                corpus_id=corpus.id,
                drama_id=SAMPLE_DRAMA_ID,
                episode_num=doc.episode_num,
                start_sec=doc.start_sec,
                end_sec=doc.end_sec,
                chunk_index=idx,
                chunk_strategy=doc.chunk_strategy,
                content=doc.text,
                parent_content=doc.parent_text,
                embedding_json=json.dumps(vec),
                token_count=len(doc.text)
            )
            db.add(chunk_rec)
            total_chunks_saved += 1
            all_chunks_for_graph.append(doc.text)

        corpus.chunk_count = len(docs)
        db.commit()

    # 3. 抽取并写入 Neo4j 图数据库
    combined_script_text = "\n".join([SAMPLE_SCRIPT_MAIN, SAMPLE_SRT_EPISODE_1, SAMPLE_SRT_EPISODE_2])
    entities_to_seed = list(SAMPLE_ENTITIES)
    relations_to_seed = list(SAMPLE_RELATIONS)

    graph_json_path = os.path.join(PRESET_DIR, "character_graph_qinjin.json")
    if os.path.exists(graph_json_path):
        try:
            with open(graph_json_path, "r", encoding="utf-8") as jf:
                gdata = json.load(jf)
                extra_entities = gdata.get("entities", [])
                extra_relations = gdata.get("relationships", [])
                entities_to_seed.extend(extra_entities)
                relations_to_seed.extend(extra_relations)
        except Exception as e:
            logger.warning(f"读取角色图谱 JSON 异常: {e}")

    extracted_triples = graph_extractor.extract_and_store(
        text=combined_script_text,
        drama_id=SAMPLE_DRAMA_ID,
        custom_entities=entities_to_seed,
        custom_relations=relations_to_seed
    )

    logger.info(f"示范资产包成功全量初始化！已入库 {len(corpora_to_create)} 篇文档，{total_chunks_saved} 条切片，{len(extracted_triples)} 条图谱三元组。")

    return {
        "status": "success",
        "drama_id": SAMPLE_DRAMA_ID,
        "title": SAMPLE_DRAMA_TITLE,
        "corpora_created": len(corpora_to_create),
        "total_chunks": total_chunks_saved,
        "graph_triples": len(extracted_triples)
    }
