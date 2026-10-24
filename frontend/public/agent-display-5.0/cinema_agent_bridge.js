/**
 * CinemaAgent Live Telemetry Bridge for agent-display-5.0
 * Preserves 100% of the original 5 themes (ops, spider, neural, factory, nebula)
 * while syncing live 9-Agent Fleet status, 3-Tier LLM bindings, Skills hits,
 * and invocation traces from /api/v1/agent-hub/telemetry/live.
 */
(function () {
  'use strict';

  const API_URLS = [
    '/api/v1/agent-hub/telemetry/live',
    'http://localhost:8000/api/v1/agent-hub/telemetry/live'
  ];

  let hudRoot = null;
  let isCollapsed = false;

  function createBridgeHUD() {
    if (document.getElementById('cinema-agent-live-bridge-hud')) return;

    const style = document.createElement('style');
    style.textContent = `
      #cinema-agent-live-bridge-hud {
        position: fixed;
        left: 18px;
        bottom: 18px;
        z-index: 99999;
        width: 410px;
        max-width: calc(100vw - 36px);
        background: rgba(10, 14, 24, 0.86);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 14px;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", sans-serif;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65);
        padding: 12px 14px;
        transition: all 0.25s ease;
      }
      #cinema-agent-live-bridge-hud.is-collapsed {
        width: 240px;
      }
      .cab-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
      }
      .cab-title {
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 12.5px;
        font-weight: 700;
        letter-spacing: 0.4px;
        color: #38bdf8;
      }
      .cab-pulse {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 10px #10b981;
      }
      .cab-toggle-btn {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #cbd5e1;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
        cursor: pointer;
      }
      .cab-kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        margin-bottom: 8px;
      }
      .cab-kpi-box {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 5px 6px;
        text-align: center;
      }
      .cab-kpi-val {
        font-size: 13px;
        font-weight: 700;
        color: #f8fafc;
      }
      .cab-kpi-lbl {
        font-size: 10px;
        color: #94a3b8;
      }
      .cab-agents-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 5px;
        margin-bottom: 8px;
      }
      .cab-agent-chip {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 7px;
        padding: 4px 6px;
        font-size: 10.5px;
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .cab-agent-chip.disabled {
        opacity: 0.55;
        border-color: rgba(239, 68, 68, 0.45);
      }
      .cab-agent-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        color: #f1f5f9;
      }
      .cab-agent-sub {
        font-size: 9.5px;
        color: #38bdf8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .cab-trace-bar {
        background: rgba(56, 189, 248, 0.09);
        border-left: 3px solid #38bdf8;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 10.5px;
        color: #cbd5e1;
        line-height: 1.35;
      }
    `;
    document.head.appendChild(style);

    hudRoot = document.createElement('div');
    hudRoot.id = 'cinema-agent-live-bridge-hud';
    hudRoot.innerHTML = `
      <div class="cab-header">
        <div class="cab-title">
          <span class="cab-pulse"></span>
          <span>CinemaAgent 九大智能体实时遥测桥</span>
        </div>
        <button class="cab-toggle-btn" id="cab-btn-collapse">收起</button>
      </div>
      <div id="cab-body-content">
        <div class="cab-kpi-row">
          <div class="cab-kpi-box"><div class="cab-kpi-val" id="cab-kpi-online">9/9</div><div class="cab-kpi-lbl">在线Agent</div></div>
          <div class="cab-kpi-box"><div class="cab-kpi-val" id="cab-kpi-calls">0</div><div class="cab-kpi-lbl">累计调度</div></div>
          <div class="cab-kpi-box"><div class="cab-kpi-val" id="cab-kpi-tokens">0</div><div class="cab-kpi-lbl">Token消耗</div></div>
          <div class="cab-kpi-box"><div class="cab-kpi-val" id="cab-kpi-skills">6</div><div class="cab-kpi-lbl">挂载Skills</div></div>
        </div>
        <div class="cab-agents-grid" id="cab-agents-grid"></div>
        <div class="cab-trace-bar" id="cab-latest-trace">正在同步 1~9 号领域专家智能体与全局黑板状态...</div>
      </div>
    `;
    document.body.appendChild(hudRoot);

    const btn = document.getElementById('cab-btn-collapse');
    btn.addEventListener('click', function () {
      isCollapsed = !isCollapsed;
      const body = document.getElementById('cab-body-content');
      if (isCollapsed) {
        hudRoot.classList.add('is-collapsed');
        body.style.display = 'none';
        btn.textContent = '展开';
      } else {
        hudRoot.classList.remove('is-collapsed');
        body.style.display = 'block';
        btn.textContent = '收起';
      }
    });
  }

  async function fetchLiveTelemetry() {
    for (const url of API_URLS) {
      try {
        const res = await fetch(url, { cache: 'no-store' });
        if (res.ok) {
          const json = await res.json();
          if (json && json.data) {
            renderTelemetry(json.data);
            return;
          }
        }
      } catch (e) {
        // try next fallback URL
      }
    }
  }

  function renderTelemetry(data) {
    createBridgeHUD();
    const sum = data.summary || {};
    const nodes = data.agent_nodes || [];
    const traces = data.recent_traces || [];

    const elOnline = document.getElementById('cab-kpi-online');
    const elCalls = document.getElementById('cab-kpi-calls');
    const elTokens = document.getElementById('cab-kpi-tokens');
    const elSkills = document.getElementById('cab-kpi-skills');
    const elGrid = document.getElementById('cab-agents-grid');
    const elTrace = document.getElementById('cab-latest-trace');

    if (elOnline) elOnline.textContent = `${sum.enabled_agents || 9}/${sum.total_agents || 9}`;
    if (elCalls) elCalls.textContent = String(sum.total_calls || 0);
    if (elTokens) elTokens.textContent = String(sum.total_tokens || 0);
    if (elSkills) elSkills.textContent = String(sum.total_skills || 6);

    if (elGrid && nodes.length) {
      elGrid.innerHTML = nodes.map(function (n) {
        const shortName = (n.name || '').replace(/^\d+号\s*·\s*/, '').slice(0, 8);
        const stateDot = n.is_enabled ? 'ON·' : 'OFF·';
        return `
          <div class="cab-agent-chip ${n.is_enabled ? '' : 'disabled'}" title="${n.name} | 模型: ${n.resolved_provider}:${n.resolved_model}">
            <div class="cab-agent-top">
              <span>#${n.agent_number} ${shortName}</span>
              <span>${stateDot}${n.calls || 0}</span>
            </div>
            <div class="cab-agent-sub">${n.model_bind_mode === 'CATEGORY_GROUP' ? '分类' : (n.model_bind_mode === 'AGENT_CUSTOM' ? '定制' : '统一')} · ${n.resolved_model}</div>
          </div>
        `;
      }).join('');
    }

    if (elTrace && traces.length > 0) {
      const latest = traces[0];
      const skillsTxt = (latest.matched_skills && latest.matched_skills.length)
        ? ` | 命中Skill: ${latest.matched_skills.join(',')}`
        : '';
      elTrace.textContent = `[最新链路 ${latest.trace_id}] ${latest.agent_name} (${latest.latency_ms}ms${skillsTxt}) -> ${latest.query_preview}`;
    }
  }

  // Listen for theme switch commands from parent Vue Admin console
  window.addEventListener('message', function (ev) {
    if (!ev.data || typeof ev.data !== 'object') return;
    if (ev.data.type === 'CINEMA_SWITCH_THEME' && ev.data.theme) {
      window.location.hash = '#' + ev.data.theme;
    } else if (ev.data.type === 'CINEMA_REFRESH_TELEMETRY') {
      fetchLiveTelemetry();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      createBridgeHUD();
      fetchLiveTelemetry();
      setInterval(fetchLiveTelemetry, 4000);
    });
  } else {
    createBridgeHUD();
    fetchLiveTelemetry();
    setInterval(fetchLiveTelemetry, 4000);
  }
})();
