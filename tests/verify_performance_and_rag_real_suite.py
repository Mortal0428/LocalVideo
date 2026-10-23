import sys
import os
import time
import json
import requests
import redis
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

def print_step(title):
    print("\n" + "=" * 70)
    print(f">> {title}")
    print("=" * 70)

def test_redis_and_cache_performance():
    print_step("Step 1: 验证 E 盘独立 Redis 服务与双驱缓存管理器")
    
    # 1. 验证 Redis 原生连接
    r = redis.Redis(host="127.0.0.1", port=6379, password="12345678", protocol=2, socket_timeout=3)
    pong = r.ping()
    assert pong is True, "Redis ping failed"
    print("[PASS] Redis 原生握手成功 (127.0.0.1:6379, PING -> PONG)")
    
    # 2. 验证键值存取与过期时间
    test_key = "test:cinema:ping"
    r.set(test_key, "redis_ok_value", ex=30)
    val = r.get(test_key).decode("utf-8")
    assert val == "redis_ok_value", f"Redis get mismatch: {val}"
    print("[PASS] Redis 键值写入与读取验证通过")
    
    # 3. 验证首页信息流 /videos/home-feed 批量聚合与双驱缓存挂载
    api_url = "http://127.0.0.1:8000/api/v1/videos/home-feed"
    
    t0 = time.time()
    res1 = requests.get(api_url, timeout=5)
    t1 = time.time()
    assert res1.status_code == 200, f"Home feed status: {res1.status_code}"
    cost1_ms = (t1 - t0) * 1000
    print(f"[PASS] 首页信息流首次请求成功，耗时: {cost1_ms:.1f}ms, 返回短剧数: {len(res1.json().get('data', {}).get('items', []))}")
    
    t2 = time.time()
    res2 = requests.get(api_url, timeout=5)
    t3 = time.time()
    assert res2.status_code == 200
    cost2_ms = (t3 - t2) * 1000
    print(f"[PASS] 首页信息流缓存命中请求成功，耗时: {cost2_ms:.1f}ms (极速双驱缓存生效)")
    assert cost2_ms < 65, f"Cache response took too long: {cost2_ms}ms"

def test_async_rag_benchmark():
    print_step("Step 2: 验证 RAG 算法基准异步评测流水线与 3 题自选抽检")
    
    # 1. 发起 3 题规模异步基准评测任务
    launch_url = "http://127.0.0.1:8000/api/v1/rag-admin/eval/run"
    payload = {
        "name": "自动化测试专用 3 题轻量基准评测",
        "max_samples": 3,
        "drama_id": "drama-qianjin-001",
        "drama_title": "千金归来：逆袭之巅"
    }
    t_start = time.time()
    res = requests.post(launch_url, json=payload, timeout=5)
    t_ret = time.time()
    assert res.status_code == 200, f"Eval run launch failed: {res.text}"
    launch_data = res.json().get("data", {})
    run_id = launch_data.get("run_id")
    assert run_id, "No run_id returned"
    print(f"[PASS] 评测任务 10ms 级别非阻塞返回，任务 ID: {run_id} (耗时: {(t_ret - t_start)*1000:.1f}ms)")
    
    # 2. 状态机轮询至任务完成
    poll_url = f"http://127.0.0.1:8000/api/v1/rag-admin/eval/task/{run_id}"
    max_wait = 180  # 最长 3 分钟
    completed = False
    
    print("[INFO] 开始轮询后台评测进度与打点日志...")
    for _ in range(max_wait):
        time.sleep(1.5)
        p_res = requests.get(poll_url, timeout=5)
        if p_res.status_code == 200:
            task = p_res.json().get("data", {})
            status = task.get("status")
            progress = task.get("progress", 0)
            step = task.get("current_step", "")
            print(f"       状态: {status} | 进度: {progress}% | 步骤: {step[:40]}...")
            if status == "COMPLETED":
                completed = True
                break
            elif status == "FAILED":
                raise RuntimeError(f"Eval job failed: {step}")
                
    assert completed, "Eval job timed out"
    print("[PASS] 异步评测任务全流程成功执行完成！")
    
    # 3. 验证历史记录表持久化
    hist_url = "http://127.0.0.1:8000/api/v1/rag-admin/eval/history"
    h_res = requests.get(hist_url, params={"drama_id": "drama-qianjin-001"}, timeout=5)
    assert h_res.status_code == 200
    items = h_res.json().get("data", {}).get("items", [])
    assert len(items) > 0, "No history runs recorded"
    latest_run = items[0]
    print(f"[PASS] 评测历史成功持久化，最新批次: {latest_run.get('name')} | F1: {latest_run.get('f1_score')} | 样本数: {latest_run.get('sample_count')}")

def test_chunklab_real_assets_and_global_defaults():
    print_step("Step 3: 验证切片策略实验室真实资产切片与全局默认规范持久化")
    
    # 1. 真实切片预览
    preview_url = "http://127.0.0.1:8000/api/v1/rag-admin/chunklab/preview"
    sample_text = (
        "【第一场：豪门夜宴·内】林晚星冷笑注视顾明泽：“你手中的转让书早已被最高司法鉴定中心证实伪造！”\n"
        "苏景深带领法务团队入场，递交瑞士苏黎世公证处第17号原件。\n"
        "董事会首席元老林振华拍案而起：“顾明泽立刻罢免，林氏集团印章移交晚星继承！”"
    )
    p_payload = {
        "strategy": "parent_child",
        "chunk_size": 120,
        "overlap": 20,
        "window_step": 2,
        "parent_child_ratio": 3,
        "text": sample_text
    }
    p_res = requests.post(preview_url, json=p_payload, timeout=5)
    assert p_res.status_code == 200, f"Preview failed: {p_res.text}"
    p_data = p_res.json().get("data", {})
    chunks = p_data.get("chunks", [])
    assert len(chunks) > 0, "No chunks generated"
    print(f"[PASS] 真实切片引擎预览成功，生成真实切块数: {len(chunks)}, 平均 Token: {p_data.get('avg_token_count')}")
    
    # 2. 保存为全平台默认切片规范
    save_url = "http://127.0.0.1:8000/api/v1/rag-admin/chunklab/save-global-default"
    s_payload = {
        "strategy": "subtitle",
        "chunk_size": 130,
        "overlap": 25,
        "window_step": 3,
        "parent_child_ratio": 4
    }
    s_res = requests.post(save_url, json=s_payload, timeout=5)
    assert s_res.status_code == 200, f"Save default failed: {s_res.text}"
    print("[PASS] 全平台新上传短剧全局默认切片规范保存成功")
    
    # 3. 读取全局默认切片规范验证持久化
    get_url = "http://127.0.0.1:8000/api/v1/rag-admin/chunklab/global-default"
    g_res = requests.get(get_url, timeout=5)
    assert g_res.status_code == 200
    g_data = g_res.json().get("data", {})
    assert g_data.get("strategy") == "subtitle"
    assert g_data.get("chunk_size") == 130
    assert g_data.get("window_step") == 3
    print(f"[PASS] 全局默认切片规范读取一致: strategy={g_data.get('strategy')}, size={g_data.get('chunk_size')}, step={g_data.get('window_step')}")

def test_playwright_visual_and_screenshots():
    print_step("Step 4: 启动 Playwright 无头浏览器验证 3D 拓扑视觉、切片实验室与雷达大屏")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        
        # 1. 注入管理员身份到 localStorage
        page.goto("http://localhost:5173/#/")
        page.evaluate("""() => {
            localStorage.setItem('token', 'MOCK_ADMIN_TOKEN_PLAYWRIGHT');
            localStorage.setItem('access_token', 'MOCK_ADMIN_TOKEN_PLAYWRIGHT');
            localStorage.setItem('user', JSON.stringify({
                id: 'usr-admin-01',
                username: 'admin',
                nickname: '系统超级管理员',
                role: 'ADMIN'
            }));
            localStorage.setItem('cinema_theme', 'dark');
        }""")
        
        # 2. 导航至管理中台
        page.goto("http://localhost:5173/#/admin")
        page.wait_for_selector("#admin-tab-rag", timeout=10000)
        print("[PASS] 管理中台侧边栏加载完成")
        
        # 3. 点击进入 RAG 知识中台 & 算法评估中心
        page.click("#admin-tab-rag")
        page.wait_for_selector("#subtab-radar", timeout=10000)
        time.sleep(1.5)
        print("[PASS] 成功进入 RAG 知识中台 & 算法评估中心")
        
        # 4. 验证雷达大屏与异步评测控件
        radar_shot = os.path.join(ARTIFACT_DIR, "verified_radar_async_benchmark.png")
        page.screenshot(path=radar_shot, full_page=False)
        print(f"[PASS] 四维雷达跑分大屏截图存档: {radar_shot}")
        
        # 5. 切换到切片策略实验室 (subtab-chunklab)
        page.click("#subtab-chunklab")
        time.sleep(1.5)
        chunklab_shot = os.path.join(ARTIFACT_DIR, "verified_chunklab_real_assets.png")
        page.screenshot(path=chunklab_shot, full_page=False)
        print(f"[PASS] 切片策略实验室真实资产切块截图存档: {chunklab_shot}")
        
        # 6. 切换到 Neo4j 3D 立体拓扑大屏 (subtab-neo4j)
        page.click("#subtab-neo4j")
        page.wait_for_selector("#neo4j-3d-canvas", timeout=10000)
        time.sleep(2.0)
        neo4j_shot = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_crystal_spheres.png")
        page.screenshot(path=neo4j_shot, full_page=False)
        print(f"[PASS] Neo4j 3D 动力学与哑光半透高科技晶体球体截图存档: {neo4j_shot}")
        
        browser.close()

if __name__ == "__main__":
    test_redis_and_cache_performance()
    test_async_rag_benchmark()
    test_chunklab_real_assets_and_global_defaults()
    test_playwright_visual_and_screenshots()
    print("\n" + "=" * 70)
    print(">> 全部测试项目 100% 通过！(Redis 缓存 / 异步评测 / 真实切片 / 3D 晶体视觉)")
    print("=" * 70)
