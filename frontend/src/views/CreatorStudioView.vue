<template>
  <div class="creator-studio-container" id="creator-studio-page">
    <AdminHeader mode="creator" :active-tab="activeTab" @selectTab="handleSelectTab" @userChanged="handleUserChanged" />

    <main class="studio-main-body">
      <!-- Ambient Orbs -->
      <div class="studio-ambient-bg">
        <div class="studio-orb orb-a"></div>
        <div class="studio-orb orb-b"></div>
      </div>

      <!-- Header Title Section -->
      <div class="studio-top-bar">
        <div>
          <div class="studio-badge-pill">CREATOR CLOUD STUDIO</div>
          <h1 class="studio-page-title">创作者中心 & 夸克网盘工作台</h1>
          <p class="studio-subtext">通过夸克网盘原生驱动管理短剧资源、新建剧集文件夹并分片上传原画视频</p>
        </div>

        <div class="studio-top-actions" v-if="isCreator">
          <button class="secondary-pill-btn" @click="handleSyncQuarkDramas" id="btn-sync-quark-dramas" :disabled="isSyncingDramas">
            <el-icon v-if="isSyncingDramas" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Refresh /></el-icon>
            <span>{{ isSyncingDramas ? '正在扫描网盘...' : '一键映射网盘短剧' }}</span>
          </button>
          <button class="primary-pill-btn" @click="showNewFolderModal = true" id="btn-open-mkdir-modal">
            <span>+ 新建剧集文件夹</span>
          </button>
        </div>
      </div>

      <!-- Condition 1: Not a Creator yet -> Application Card -->
      <section v-if="!isCreator" class="apply-creator-card" id="creator-apply-box">
        <div class="apply-header-wrap">
          <div class="apply-icon-orb">
            <el-icon :size="24"><VideoCamera /></el-icon>
          </div>
          <div>
            <h2 class="apply-title">申请加入 CinemaAgent 创作者生态</h2>
            <p class="apply-desc">成为创作者后，您可直接接入夸克网盘短剧资源库，自由创建剧集文件夹并分发短剧视频。</p>
          </div>
        </div>

        <div class="apply-form-body">
          <div class="form-item-field">
            <label class="form-label">创作者别名 / UP主昵称</label>
            <input
              v-model="applyForm.creator_name"
              type="text"
              class="apple-text-input"
              placeholder="例如：短剧大爆炸、影视剪辑社"
              id="input-creator-name"
            />
          </div>

          <div class="form-item-field">
            <label class="form-label">创作方向 / 简介 (选填)</label>
            <input
              v-model="applyForm.bio"
              type="text"
              class="apple-text-input"
              placeholder="例如：专注都市爽剧、热血战神与甜宠短剧制作"
              id="input-creator-bio"
            />
          </div>

          <div class="apply-action-bar">
            <button
              class="submit-apply-btn"
              :disabled="applySubmitting"
              @click="submitApply"
              id="btn-submit-creator-apply"
            >
              {{ applySubmitting ? '申请提交中...' : '一键开通创作者权限' }}
            </button>
            <span v-if="applyMessage" class="apply-feedback-msg">{{ applyMessage }}</span>
          </div>
        </div>
      </section>

      <!-- Condition 2: Active Creator -> Studio Tabs -->
      <section v-else class="creator-workspace-area">
        <!-- Tab Switcher -->
        <div class="studio-tabs-row">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'disk' }"
            @click="activeTab = 'disk'"
            id="tab-pan-tree"
          >
            <el-icon><Folder /></el-icon>
            <span>夸克网盘云空间</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'upload' }"
            @click="activeTab = 'upload'"
            id="tab-video-upload"
          >
            <el-icon><Upload /></el-icon>
            <span>剧集视频上传</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'dramas' }"
            @click="activeTab = 'dramas'"
            id="tab-my-dramas"
          >
            <el-icon><Film /></el-icon>
            <span>我的剧集 ({{ myDramas.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'bi' }"
            @click="activeTab = 'bi'"
            id="tab-creator-bi"
          >
            <el-icon><DataAnalysis /></el-icon>
            <span>BI 创作数据看板</span>
          </button>
        </div>

        <!-- TAB 1: Cloud Disk Directory Tree Browser -->
        <div v-if="activeTab === 'disk'" class="tab-content-panel" id="panel-disk-tree">
          <div class="pan-breadcrumb-bar">
            <div class="breadcrumb-left">
              <span class="path-label">当前网盘路径：</span>
              <span class="current-path-text" id="current-cloud-path">{{ currentPath }}</span>
            </div>
            <div class="breadcrumb-right">
              <button
                class="secondary-pill-btn"
                :disabled="currentPath === '/kuake' || currentPath === '/'"
                @click="navigateUp"
                id="btn-navigate-up"
              >
                <el-icon><Top /></el-icon>
                <span>返回上级目录</span>
              </button>
              <button class="secondary-pill-btn" @click="fetchPanTree(currentPath)" id="btn-refresh-pan">
                <el-icon><Refresh /></el-icon>
                <span>刷新</span>
              </button>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="panLoading" class="pan-loading-box">
            <div class="spinner"></div>
            <span>正在连接夸克网盘获取目录树...</span>
          </div>

          <!-- Pan Items Grid -->
          <div v-else class="pan-items-grid">
            <!-- Folders -->
            <div
              v-for="folder in panFolders"
              :key="folder.path"
              class="pan-item-card folder-card"
              @click="enterFolder(folder.path)"
              :id="'folder-' + folder.name"
            >
              <div class="item-glyph-icon">
                <el-icon :size="28"><Folder /></el-icon>
              </div>
              <div class="item-meta-wrap">
                <div class="item-main-title">{{ folder.name }}</div>
                <div class="item-sub-meta">剧集文件夹 · 点击进入</div>
              </div>
            </div>

            <!-- Files -->
            <div
              v-for="file in panFiles"
              :key="file.path"
              class="pan-item-card file-card"
              :id="'file-' + file.name"
            >
              <div class="item-glyph-icon">
                <el-icon :size="28"><Film /></el-icon>
              </div>
              <div class="item-meta-wrap">
                <div class="item-main-title">{{ file.name }}</div>
                <div class="item-sub-meta">{{ formatBytes(file.size) }} · {{ formatDate(file.modified) }}</div>
              </div>
            </div>

            <!-- Empty Folder State -->
            <div v-if="panFolders.length === 0 && panFiles.length === 0" class="empty-pan-box">
              <div class="empty-pan-icon">
                <el-icon :size="48"><Folder /></el-icon>
              </div>
              <h4>此文件夹暂无短剧资源</h4>
              <p>您可以点击右上角“新建剧集文件夹”创建短剧目录，或切换到“剧集视频上传”存入视频文件。</p>
            </div>
          </div>
        </div>

        <!-- TAB 2: Drag and Drop Video Uploader -->
        <div v-if="activeTab === 'upload'" class="tab-content-panel" id="panel-video-upload">
          <div class="upload-builder-grid">
            <div class="upload-form-side">
              <h3 class="panel-section-title">剧集发布信息</h3>

              <div class="form-item-field">
                <label class="form-label">存放网盘目录</label>
                <input
                  v-model="uploadTargetFolder"
                  type="text"
                  class="apple-text-input"
                  placeholder="/kuake/红果项目资源目录"
                />
              </div>

              <div class="form-item-field">
                <label class="form-label">短剧专辑名称</label>
                <input
                  v-model="uploadDramaTitle"
                  type="text"
                  class="apple-text-input"
                  placeholder="例如：战神归来：龙王令"
                  id="input-drama-title"
                />
              </div>

              <div class="form-item-row">
                <div class="form-item-field half">
                  <label class="form-label">分集序号</label>
                  <input
                    v-model.number="uploadEpisodeNum"
                    type="number"
                    min="1"
                    class="apple-text-input"
                    id="input-episode-num"
                  />
                </div>
                <div class="form-item-field half">
                  <label class="form-label">分类频道</label>
                  <select v-model="uploadCategory" class="apple-text-input">
                    <option value="都市战神">都市战神</option>
                    <option value="悬疑逆袭">悬疑逆袭</option>
                    <option value="古装穿越">古装穿越</option>
                    <option value="豪门甜宠">豪门甜宠</option>
                    <option value="短剧精选">短剧精选</option>
                  </select>
                </div>
              </div>

              <div class="form-item-field">
                <label class="form-label">分集标题 (选填)</label>
                <input
                  v-model="uploadEpisodeTitle"
                  type="text"
                  class="apple-text-input"
                  placeholder="例如：第 1 集：龙王卸甲归来"
                />
              </div>
            </div>

            <!-- Dropzone Area -->
            <div class="upload-dropzone-side">
              <div
                class="file-drop-box"
                :class="{ dragging: isDragging, 'has-file': !!selectedFile }"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleFileDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInputRef"
                  type="file"
                  accept="video/mp4,video/x-matroska,video/quicktime"
                  style="display: none"
                  @change="handleFileSelect"
                  id="file-input-raw"
                />

                <div v-if="!selectedFile" class="dropzone-idle">
                  <div class="drop-icon">
                    <el-icon :size="48"><VideoPlay /></el-icon>
                  </div>
                  <h4>点击或拖拽短剧视频到此处</h4>
                  <p>支持 MP4, MKV 格式，通过夸克网盘极速直传并自动提取 FFmpeg 首帧封面</p>
                </div>

                <div v-else class="dropzone-file-selected">
                  <div class="file-success-icon">
                    <el-icon :size="28"><Check /></el-icon>
                  </div>
                  <div class="selected-name">{{ selectedFile.name }}</div>
                  <div class="selected-size">{{ formatBytes(selectedFile.size) }}</div>
                  <button class="remove-file-btn" @click.stop="selectedFile = null">重新选择</button>
                </div>
              </div>

              <!-- Upload Progress & Action -->
              <div class="upload-action-dock">
                <div v-if="uploadProgress > 0" class="progress-track-wrap">
                  <div class="progress-bar-fill" :style="{ width: uploadProgress + '%' }"></div>
                  <span class="progress-label">{{ uploadProgress }}% · {{ uploadStatusText }}</span>
                </div>

                <button
                  class="primary-pill-btn full-width"
                  :disabled="!selectedFile || isUploading"
                  @click="startUpload"
                  id="btn-start-upload"
                >
                  <el-icon v-if="isUploading" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><Promotion /></el-icon>
                  <span>{{ isUploading ? '正在上传并转存网盘中...' : '开始上传至夸克网盘并上架' }}</span>
                </button>

                <div v-if="uploadFeedback" class="upload-feedback-badge" :class="uploadFeedbackType">
                  {{ uploadFeedback }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 3: My Uploaded Dramas List -->
        <div v-if="activeTab === 'dramas'" class="tab-content-panel" id="panel-my-dramas">
          <div class="dramas-list-grid">
            <div
              v-for="drama in myDramas"
              :key="drama.id"
              class="my-drama-card"
            >
              <div class="drama-cover-box" :style="{ backgroundImage: `url(${drama.cover_url})` }">
                <span class="status-chip">{{ drama.status }}</span>
              </div>
              <div class="drama-info-box">
                <h4 class="drama-card-title">{{ drama.title }}</h4>
                <div class="drama-card-tags">
                  <span class="tag-pill">{{ drama.category }}</span>
                  <span class="tag-pill">全 {{ drama.episodes_count }} 集</span>
                  <span class="tag-pill">▶ {{ drama.play_count }} 次播放</span>
                </div>
                <p class="drama-card-desc">{{ drama.description }}</p>
                <div class="drama-card-footer">
                  <span class="time-label">{{ drama.created_at }}</span>
                  <div class="drama-actions-group">
                    <button class="secondary-pill-btn btn-xs" @click="manageEpisodes(drama)" :id="'btn-episodes-' + drama.id">分集编排</button>
                    <button class="secondary-pill-btn btn-xs" @click="openEditDramaModal(drama)" :id="'btn-edit-drama-' + drama.id">编辑</button>
                    <button class="secondary-pill-btn btn-xs" @click="toggleDramaStatus(drama)" :id="'btn-status-' + drama.id">
                      {{ drama.status === 'READY' || drama.status === 'PUBLISHED' ? '屏蔽' : '上架' }}
                    </button>
                    <button class="secondary-pill-btn btn-xs btn-danger-text" @click="handleDeleteDrama(drama)" :id="'btn-del-drama-' + drama.id">删除</button>
                    <button class="play-action-btn" @click="goToPlay(drama.id)">播放 →</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 4: Creator BI Analytics Dashboard -->
        <div v-if="activeTab === 'bi'" class="tab-content-panel" id="panel-creator-bi">
          <!-- Bento KPI Cards -->
          <div class="creator-kpi-grid">
            <div class="kpi-bento-card">
              <div class="kpi-header-row">
                <span class="kpi-label">全网累计播放</span>
                <span class="kpi-badge blue">真实流量</span>
              </div>
              <div class="kpi-value-num">{{ formatNumber(totalViews) }}</div>
              <div class="kpi-hint">涵盖旗下 {{ myDramas.length }} 部短剧累计有效播放</div>
            </div>

            <div class="kpi-bento-card">
              <div class="kpi-header-row">
                <span class="kpi-label">观众累计获赞</span>
                <span class="kpi-badge pink">高能共鸣</span>
              </div>
              <div class="kpi-value-num">{{ formatNumber(totalLikes) }}</div>
              <div class="kpi-hint">跨端短剧点赞与互动好评留存</div>
            </div>

            <div class="kpi-bento-card">
              <div class="kpi-header-row">
                <span class="kpi-label">短剧投币总收益</span>
                <span class="kpi-badge amber">经济闭环</span>
              </div>
              <div class="kpi-value-num text-amber">{{ totalCoins }} 币</div>
              <div class="kpi-hint">观众投币打赏分成，可转入钱包</div>
            </div>

            <div class="kpi-bento-card">
              <div class="kpi-header-row">
                <span class="kpi-label">创作综合热度</span>
                <span class="kpi-badge green">爆款健康</span>
              </div>
              <div class="kpi-value-num">{{ avgViralScore }} 分</div>
              <div class="kpi-hint">基于完播、看点与互动加权综合评估</div>
            </div>
          </div>

          <!-- Drama Commercialization & Heat Ranking Table -->
          <div class="creator-bi-table-card">
            <div class="card-title-row">
              <div class="title-wrap">
                <el-icon :size="18" class="title-icon"><TrendCharts /></el-icon>
                <h3 class="bi-card-title">短剧商业化表现与热度榜单</h3>
              </div>
              <span class="bi-card-badge">实时更新</span>
            </div>

            <div class="table-container">
              <table class="creator-bi-table">
                <thead>
                  <tr>
                    <th>短剧作品</th>
                    <th>题材分类</th>
                    <th>收录集数</th>
                    <th>播放量</th>
                    <th>获赞数</th>
                    <th>投币打赏</th>
                    <th>热度指数</th>
                    <th>运营状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in myDramas" :key="item.id">
                    <td class="font-bold">{{ item.title }}</td>
                    <td><span class="bi-tag-pill">{{ item.category }}</span></td>
                    <td>共 {{ item.total_episodes || item.episodes_count || 0 }} 集</td>
                    <td>{{ formatNumber(item.view_count || item.play_count || 0) }}</td>
                    <td>{{ formatNumber(item.like_count || 0) }}</td>
                    <td class="text-amber font-bold">{{ item.coin_count || 0 }} 币</td>
                    <td>
                      <div class="score-pill">{{ item.viral_score || 88 }}</div>
                    </td>
                    <td>
                      <span class="status-indicator-tag" :class="item.status === 'READY' || item.status === 'PUBLISHED' ? 'tag-pub' : 'tag-draft'">
                        {{ item.status === 'READY' || item.status === 'PUBLISHED' ? '上架公映' : '草稿归档' }}
                      </span>
                    </td>
                  </tr>
                  <tr v-if="myDramas.length === 0">
                    <td colspan="8" class="text-center py-6 text-sub">暂无短剧数据，请先映射网盘短剧</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Insight & Recommendation Cards -->
          <div class="creator-insights-grid">
            <div class="insight-card">
              <div class="insight-head">
                <el-icon class="insight-icon"><VideoPlay /></el-icon>
                <h4>黄金时段发布建议</h4>
              </div>
              <p>短剧受众在晚间 20:00 - 23:00 与午间 12:00 - 13:30 完播留存率最高，建议在此时段保持网盘新集推送与焦点画报更新。</p>
            </div>
            <div class="insight-card">
              <div class="insight-head">
                <el-icon class="insight-icon"><Star /></el-icon>
                <h4>高能看点留存提振</h4>
              </div>
              <p>在“我的剧集”中配置精准的高能看点秒数，前台播放器高能点打点可提升 42% 的完播转化并大幅提升观众投币打赏意愿。</p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Modal: Make Directory in Cloud Disk -->
    <div v-if="showNewFolderModal" class="modal-backdrop-scrim">
      <div class="modal-glass-card" id="modal-mkdir">
        <h3 class="modal-title">在夸克网盘新建剧集文件夹</h3>
        <p class="modal-subtext">目标目录：{{ currentPath }}</p>

        <div class="form-item-field">
          <label class="form-label">文件夹名称</label>
          <input
            v-model="newFolderName"
            type="text"
            class="apple-text-input"
            placeholder="例如：重生之狂傲仙尊"
            id="input-mkdir-name"
            @keyup.enter="confirmMkdir"
          />
        </div>

        <div class="modal-actions-row">
          <button class="secondary-pill-btn" @click="showNewFolderModal = false">取消</button>
          <button
            class="primary-pill-btn"
            :disabled="!newFolderName.trim() || mkdirLoading"
            @click="confirmMkdir"
            id="btn-confirm-mkdir"
          >
            {{ mkdirLoading ? '正在创建...' : '确认新建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Edit Drama Metadata -->
    <div v-if="showEditDramaModal" class="modal-backdrop-scrim">
      <div class="modal-glass-card" id="modal-edit-drama">
        <h3 class="modal-title">编辑短剧专辑信息</h3>
        <p class="modal-subtext">修改短剧标题、题材分类与封面展示</p>

        <div class="form-item-field">
          <label class="form-label">短剧名称</label>
          <input v-model="dramaForm.title" type="text" class="apple-text-input" id="input-edit-drama-title" />
        </div>

        <div class="form-item-field">
          <label class="form-label">题材分类</label>
          <select v-model="dramaForm.category" class="apple-text-input" id="select-edit-drama-category">
            <option value="都市战神">都市战神</option>
            <option value="悬疑逆袭">悬疑逆袭</option>
            <option value="古装穿越">古装穿越</option>
            <option value="豪门甜宠">豪门甜宠</option>
            <option value="短剧精选">短剧精选</option>
          </select>
        </div>

        <div class="form-item-field">
          <label class="form-label">封面图片 URL (JPG/PNG)</label>
          <input v-model="dramaForm.cover_url" type="text" class="apple-text-input" id="input-edit-drama-cover" />
        </div>

        <div class="form-item-field">
          <label class="form-label">剧情简介</label>
          <textarea v-model="dramaForm.description" class="apple-text-input" rows="3" id="input-edit-drama-desc"></textarea>
        </div>

        <div class="modal-actions-row">
          <button class="secondary-pill-btn" @click="showEditDramaModal = false">取消</button>
          <button class="primary-pill-btn" @click="confirmUpdateDrama" id="btn-save-drama-edit">保存短剧信息</button>
        </div>
      </div>
    </div>

    <!-- Modal: Episodes Management Drawer -->
    <div v-if="showEpisodesDrawer" class="modal-backdrop-scrim">
      <div class="modal-glass-card modal-wide" id="modal-manage-episodes">
        <div class="drawer-header-row">
          <div>
            <h3 class="modal-title">短剧分集编排与看点配置</h3>
            <p class="modal-subtext">《{{ selectedDrama?.title }}》· 共 {{ episodesList.length }} 集分集资产</p>
          </div>
          <button class="close-x-btn" @click="showEpisodesDrawer = false">✕</button>
        </div>

        <div v-if="episodesLoading" class="pan-loading-box">
          <div class="spinner"></div>
          <span>正在加载分集列表与时间轴看点...</span>
        </div>

        <div v-else class="episodes-manage-table-wrap">
          <table class="creator-table">
            <thead>
              <tr>
                <th style="width: 80px;">序号</th>
                <th>分集标题</th>
                <th>视频时长</th>
                <th>高能反转名场面 (秒)</th>
                <th style="width: 90px;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ep in episodesList" :key="ep.id" :id="'ep-row-' + ep.id">
                <td class="font-bold">第 {{ ep.episode_num }} 集</td>
                <td>
                  <input v-model="ep.title" class="table-inline-input" placeholder="分集标题" />
                </td>
                <td class="sub-text-col">{{ ep.duration_seconds ? ep.duration_seconds + 's' : '-' }}</td>
                <td>
                  <div class="climax-input-wrap">
                    <input 
                      v-model.number="ep.climax_seconds" 
                      type="number" 
                      step="0.5" 
                      min="0" 
                      class="table-inline-input mini" 
                      placeholder="如 35.5" 
                    />
                    <span class="sec-unit">秒</span>
                  </div>
                </td>
                <td>
                  <button class="secondary-pill-btn btn-xs" @click="saveEpisodeChanges(ep)" :id="'btn-save-ep-' + ep.id">保存</button>
                </td>
              </tr>
              <tr v-if="episodesList.length === 0">
                <td colspan="5" class="empty-table-cell">暂无分集数据</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="modal-actions-row">
          <button class="primary-pill-btn" @click="showEpisodesDrawer = false">完成分集编排</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AdminHeader from '../components/AdminHeader.vue'
import {
  Refresh,
  Folder,
  Upload,
  Film,
  Top,
  VideoCamera,
  Check,
  Promotion,
  Loading,
  VideoPlay,
  DataAnalysis,
  TrendCharts,
  Star
} from '@element-plus/icons-vue'
import { creatorApi, type CloudDiskItem, type CreatorDramaItem, type CreatorEpisodeItem } from '../api/creator'

import { authApi } from '../api/auth'

const router = useRouter()
const route = useRoute()

const user = ref<any>(null)
const loadUser = async () => {
  try {
    const raw = localStorage.getItem('user')
    if (raw) user.value = JSON.parse(raw)
  } catch {}

  const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token')
  if (token) {
    try {
      const res = await authApi.getMe()
      if (res?.data) {
        user.value = res.data
        localStorage.setItem('user', JSON.stringify(res.data))
      }
    } catch (e) {
      console.warn('Failed to refresh user:', e)
    }
  }
}

const handleUserChanged = (u: any) => {
  user.value = u
  if (isCreator.value) {
    fetchPanTree()
    fetchMyDramas()
  }
}

const isCreator = computed(() => {
  if (!user.value) return false
  return !!user.value.is_creator || user.value.role === 'CREATOR' || user.value.role === 'ADMIN'
})

// Application Form
const applyForm = ref({
  creator_name: '',
  bio: ''
})
const applySubmitting = ref(false)
const applyMessage = ref('')

const submitApply = async () => {
  if (!applyForm.value.creator_name.trim()) {
    applyForm.value.creator_name = user.value?.nickname || user.value?.username || '影视创作者'
  }
  applySubmitting.value = true
  applyMessage.value = ''
  try {
    const res: any = await creatorApi.apply(applyForm.value)
    if (res.code === 200) {
      applyMessage.value = '恭喜！您已成功开通创作者权限！'
      // Update stored user
      if (res.data) {
        user.value = { ...user.value, ...res.data, is_creator: true, role: 'CREATOR' }
        localStorage.setItem('user', JSON.stringify(user.value))
        loadUser()
      }
      setTimeout(() => {
        activeTab.value = 'disk'
        fetchPanTree()
      }, 800)
    } else {
      applyMessage.value = res.message || '申请失败，请稍后重试'
    }
  } catch (err: any) {
    applyMessage.value = err.response?.data?.detail || err.message || '申请失败'
  } finally {
    applySubmitting.value = false
  }
}

// Workspace state
const activeTab = ref<'disk' | 'upload' | 'dramas' | 'bi'>('disk')

// BI Analytics State
const totalViews = computed(() => myDramas.value.reduce((acc, d) => acc + (d.play_count || 0), 0))
const totalLikes = computed(() => myDramas.value.reduce((acc, d) => acc + (d.like_count || 0), 0))
const totalCoins = computed(() => myDramas.value.reduce((acc, d) => acc + (d.coin_count || 0), 0))
const avgViralScore = computed(() => {
  if (!myDramas.value.length) return 88
  const sum = myDramas.value.reduce((acc, d) => acc + (d.viral_score || 88), 0)
  return Math.round(sum / myDramas.value.length)
})

const handleSelectTab = (tab: string) => {
  if (['disk', 'upload', 'dramas', 'bi'].includes(tab)) {
    activeTab.value = tab as any
  }
}

// Cloud Disk Tree
const currentPath = ref('/kuake/红果项目资源目录')
const parentPath = ref('/kuake')
const panFolders = ref<CloudDiskItem[]>([])
const panFiles = ref<CloudDiskItem[]>([])
const panLoading = ref(false)

const fetchPanTree = async (path?: string) => {
  panLoading.value = true
  const target = path || currentPath.value
  try {
    const res = await creatorApi.getPanTree(target)
    if (res.code === 200 && res.data) {
      currentPath.value = res.data.current_path
      parentPath.value = res.data.parent_path
      panFolders.value = res.data.folders || []
      panFiles.value = res.data.files || []
      uploadTargetFolder.value = res.data.current_path
    }
  } catch (err) {
    console.error('Failed to list pan files:', err)
  } finally {
    panLoading.value = false
  }
}

const enterFolder = (folderPath: string) => {
  fetchPanTree(folderPath)
}

const navigateUp = () => {
  if (parentPath.value) {
    fetchPanTree(parentPath.value)
  }
}

// Mkdir Modal
const showNewFolderModal = ref(false)
const newFolderName = ref('')
const mkdirLoading = ref(false)

const confirmMkdir = async () => {
  if (!newFolderName.value.trim()) return
  mkdirLoading.value = true
  try {
    const res = await creatorApi.mkdir(newFolderName.value.trim(), currentPath.value)
    if (res.code === 200) {
      showNewFolderModal.value = false
      newFolderName.value = ''
      fetchPanTree(currentPath.value)
    }
  } catch (err: any) {
    alert(err.response?.data?.detail || '创建文件夹失败')
  } finally {
    mkdirLoading.value = false
  }
}

// Upload Form
const uploadTargetFolder = ref('/kuake/红果项目资源目录')
const uploadDramaTitle = ref('')
const uploadEpisodeTitle = ref('')
const uploadEpisodeNum = ref(1)
const uploadCategory = ref('短剧精选')
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatusText = ref('')
const uploadFeedback = ref('')
const uploadFeedbackType = ref<'success' | 'error'>('success')

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    if (!uploadDramaTitle.value) {
      uploadDramaTitle.value = selectedFile.value.name.replace(/\.[^/.]+$/, '')
    }
  }
}

const handleFileDrop = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer && e.dataTransfer.files.length > 0) {
    selectedFile.value = e.dataTransfer.files[0]
    if (!uploadDramaTitle.value) {
      uploadDramaTitle.value = selectedFile.value.name.replace(/\.[^/.]+$/, '')
    }
  }
}

const startUpload = async () => {
  if (!selectedFile.value) return
  isUploading.value = true
  uploadProgress.value = 15
  uploadStatusText.value = '正在上传分片数据...'
  uploadFeedback.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('target_folder', uploadTargetFolder.value)
  formData.append('drama_title', uploadDramaTitle.value)
  formData.append('episode_title', uploadEpisodeTitle.value)
  formData.append('episode_num', String(uploadEpisodeNum.value))
  formData.append('category', uploadCategory.value)

  try {
    uploadProgress.value = 55
    uploadStatusText.value = '提取 FFmpeg 首帧海报与转码元数据...'
    const res: any = await creatorApi.uploadVideo(formData)
    uploadProgress.value = 100
    uploadStatusText.value = '已存入夸克网盘并同步上架！'
    uploadFeedback.value = res.message || '上传成功！'
    uploadFeedbackType.value = 'success'
    selectedFile.value = null
    fetchMyDramas()
  } catch (err: any) {
    uploadFeedback.value = err.response?.data?.detail || err.message || '上传处理失败'
    uploadFeedbackType.value = 'error'
    uploadProgress.value = 0
  } finally {
    isUploading.value = false
  }
}

// My Dramas
const myDramas = ref<CreatorDramaItem[]>([])
const isSyncingDramas = ref(false)

const handleSyncQuarkDramas = async () => {
  isSyncingDramas.value = true
  try {
    const res: any = await creatorApi.syncDramas()
    alert(res.message || '夸克网盘短剧同步成功！')
    await fetchPanTree()
    await fetchMyDramas()
  } catch (err: any) {
    alert('同步失败: ' + (err.response?.data?.detail || err.message || '网络错误'))
  } finally {
    isSyncingDramas.value = false
  }
}

const fetchMyDramas = async () => {
  try {
    const res = await creatorApi.getMyDramas()
    if (res.code === 200 && res.data) {
      myDramas.value = res.data
    }
  } catch (err) {
    console.error('Failed to load dramas:', err)
  }
}

const goToPlay = (dramaId: string) => {
  router.push(`/video/${dramaId}`)
}

// Edit Drama State & Handlers
const showEditDramaModal = ref(false)
const editingDrama = ref<CreatorDramaItem | null>(null)
const dramaForm = ref({
  title: '',
  category: '短剧精选',
  description: '',
  cover_url: ''
})

const openEditDramaModal = (drama: CreatorDramaItem) => {
  editingDrama.value = drama
  dramaForm.value = {
    title: drama.title,
    category: drama.category || '短剧精选',
    description: drama.description || '',
    cover_url: drama.cover_url || ''
  }
  showEditDramaModal.value = true
}

const confirmUpdateDrama = async () => {
  if (!editingDrama.value || !dramaForm.value.title.trim()) return
  try {
    const res: any = await creatorApi.updateDrama(editingDrama.value.id, dramaForm.value)
    if (res.code === 200 && res.data) {
      editingDrama.value.title = res.data.title
      editingDrama.value.category = res.data.category
      editingDrama.value.description = res.data.description
      editingDrama.value.cover_url = res.data.cover_url
      showEditDramaModal.value = false
      alert(`短剧《${res.data.title}》信息已成功更新！`)
    }
  } catch (err: any) {
    alert('保存失败: ' + (err.response?.data?.detail || err.message))
  }
}

const toggleDramaStatus = async (drama: CreatorDramaItem) => {
  const target = (drama.status === 'READY' || drama.status === 'PUBLISHED') ? 'HIDDEN' : 'READY'
  try {
    const res: any = await creatorApi.updateDrama(drama.id, { status: target })
    if (res.code === 200) {
      drama.status = target
      alert(`短剧《${drama.title}》已${target === 'READY' ? '重新上架' : '屏蔽下线'}`)
    }
  } catch (err: any) {
    alert('状态更新失败: ' + (err.response?.data?.detail || err.message))
  }
}

const handleDeleteDrama = async (drama: CreatorDramaItem) => {
  if (!confirm(`确定要从平台删除短剧《${drama.title}》及其全部分集记录吗？`)) return
  try {
    await creatorApi.deleteDrama(drama.id)
    myDramas.value = myDramas.value.filter(d => d.id !== drama.id)
    alert(`短剧《${drama.title}》已成功删除！`)
  } catch (err: any) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// Episodes Drawer State & Handlers
const showEpisodesDrawer = ref(false)
const selectedDrama = ref<CreatorDramaItem | null>(null)
const episodesList = ref<CreatorEpisodeItem[]>([])
const episodesLoading = ref(false)

const manageEpisodes = async (drama: CreatorDramaItem) => {
  selectedDrama.value = drama
  showEpisodesDrawer.value = true
  episodesLoading.value = true
  try {
    const res: any = await creatorApi.getDramaEpisodes(drama.id)
    if (res.code === 200 && res.data) {
      episodesList.value = res.data.episodes || []
    }
  } catch (err: any) {
    alert('加载分集失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    episodesLoading.value = false
  }
}

const saveEpisodeChanges = async (ep: CreatorEpisodeItem) => {
  try {
    const res: any = await creatorApi.updateEpisode(ep.id, {
      title: ep.title,
      episode_num: ep.episode_num,
      climax_seconds: ep.climax_seconds ?? undefined
    })
    if (res.code === 200) {
      alert(`第 ${ep.episode_num} 集信息已成功保存！`)
    }
  } catch (err: any) {
    alert('保存分集失败: ' + (err.response?.data?.detail || err.message))
  }
}

// Utilities
const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (isoStr?: string) => {
  if (!isoStr) return '-'
  try {
    return new Date(isoStr).toLocaleDateString()
  } catch {
    return isoStr
  }
}

const formatNumber = (num?: number) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return String(num)
}

onMounted(async () => {
  await loadUser()
  if (route.query.tab && ['disk', 'upload', 'dramas', 'bi'].includes(String(route.query.tab))) {
    activeTab.value = String(route.query.tab) as any
  }
  if (isCreator.value) {
    fetchPanTree()
    fetchMyDramas()
  }
})
</script>

<style scoped>
.creator-studio-container {
  min-height: 100vh;
  background-color: #f5f5f7;
  color: #1d1d1f;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", sans-serif;
  position: relative;
  overflow-x: hidden;
}

.studio-main-body {
  max-width: 1680px;
  margin: 0 auto;
  padding: 32px 40px 80px;
  position: relative;
  z-index: 2;
}

/* Ambient Orbs */
.studio-ambient-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.studio-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(85px);
  opacity: 0.45;
}

.orb-a {
  width: 45vw;
  height: 45vw;
  top: -10vw;
  right: -5vw;
  background: radial-gradient(circle, rgba(162, 210, 255, 0.4) 0%, transparent 70%);
}

.orb-b {
  width: 40vw;
  height: 40vw;
  bottom: 0;
  left: -5vw;
  background: radial-gradient(circle, rgba(200, 180, 255, 0.35) 0%, transparent 70%);
}

/* Top Bar */
.studio-top-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 32px;
}

.studio-badge-pill {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  margin-bottom: 8px;
}

.studio-page-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #18191c;
  margin: 0 0 6px;
}

.studio-subtext {
  font-size: 14px;
  color: #6e6e73;
  margin: 0;
}

/* Common Buttons */
.primary-pill-btn {
  background: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 22px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.25);
  transition: all 0.25s ease;
}

.primary-pill-btn:hover:not(:disabled) {
  background: #0077ed;
  transform: translateY(-1px);
}

.primary-pill-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-pill-btn {
  background: #e5e5ea;
  color: #1d1d1f;
  border: none;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.secondary-pill-btn:hover:not(:disabled) {
  background: #d8d8de;
}

/* Apply Creator Card */
.apply-creator-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 28px;
  padding: 48px;
  max-width: 760px;
  margin: 40px auto;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.05);
}

.apply-header-wrap {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
}

.apply-icon-orb {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: linear-gradient(135deg, #0071e3, #8b5cf6);
  color: #ffffff;
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 113, 227, 0.3);
}

.apply-title {
  font-size: 24px;
  font-weight: 700;
  color: #18191c;
  margin: 0 0 6px;
}

.apply-desc {
  font-size: 14px;
  color: #6e6e73;
  margin: 0;
  line-height: 1.5;
}

.form-item-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #333336;
}

.apple-text-input {
  background: #f2f2f7;
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  color: #1d1d1f;
  transition: all 0.25s ease;
  outline: none;
}

.apple-text-input:focus {
  background: #ffffff;
  border-color: #0071e3;
  box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.15);
}

.submit-apply-btn {
  background: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 15px;
  font-weight: 600;
  padding: 12px 28px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 113, 227, 0.3);
  transition: all 0.25s ease;
}

.submit-apply-btn:hover {
  background: #0077ed;
  transform: translateY(-2px);
}

.apply-feedback-msg {
  font-size: 14px;
  color: #34c759;
  font-weight: 600;
  margin-left: 16px;
}

/* Tabs */
.studio-tabs-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.tab-btn {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  padding: 10px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: #555558;
  cursor: pointer;
  transition: all 0.25s ease;
}

.tab-btn.active {
  background: #0071e3;
  color: #ffffff;
  border-color: #0071e3;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
}

/* Tab Panels */
.tab-content-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 28px;
  padding: 32px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
}

/* Breadcrumb */
.pan-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.path-label {
  font-size: 13px;
  color: #86868b;
}

.current-path-text {
  font-size: 14px;
  font-weight: 600;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
}

.breadcrumb-right {
  display: flex;
  gap: 10px;
}

/* Pan Items Grid */
.pan-items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.pan-item-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.85);
  transition: all 0.25s ease;
  cursor: pointer;
}

.pan-item-card:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
}

.item-glyph-icon {
  font-size: 28px;
}

.item-main-title {
  font-size: 14px;
  font-weight: 600;
  color: #18191c;
  word-break: break-all;
}

.item-sub-meta {
  font-size: 12px;
  color: #86868b;
  margin-top: 2px;
}

.empty-pan-box {
  grid-column: 1 / -1;
  text-align: center;
  padding: 48px 24px;
  color: #86868b;
}

.empty-pan-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* Upload Tab Grid */
.upload-builder-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
}

.panel-section-title {
  font-size: 18px;
  font-weight: 700;
  color: #18191c;
  margin: 0 0 20px;
}

.form-item-row {
  display: flex;
  gap: 16px;
}

.form-item-row .half {
  flex: 1;
}

/* Dropzone */
.file-drop-box {
  border: 2px dashed rgba(0, 113, 227, 0.3);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.5);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-drop-box:hover,
.file-drop-box.dragging {
  border-color: #0071e3;
  background: rgba(0, 113, 227, 0.04);
}

.drop-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.dropzone-idle h4 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
}

.dropzone-idle p {
  margin: 0;
  font-size: 13px;
  color: #86868b;
}

.file-success-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.selected-name {
  font-size: 15px;
  font-weight: 600;
  color: #18191c;
}

.selected-size {
  font-size: 13px;
  color: #86868b;
  margin-top: 4px;
}

.remove-file-btn {
  margin-top: 14px;
  background: #e5e5ea;
  border: none;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 999px;
  cursor: pointer;
}

.upload-action-dock {
  margin-top: 24px;
}

.full-width {
  width: 100%;
  padding: 14px;
  font-size: 15px;
}

.progress-track-wrap {
  background: #e5e5ea;
  border-radius: 999px;
  height: 24px;
  position: relative;
  overflow: hidden;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-bar-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: #0071e3;
  transition: width 0.3s ease;
}

.progress-label {
  position: relative;
  z-index: 2;
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
}

.upload-feedback-badge {
  margin-top: 14px;
  padding: 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.upload-feedback-badge.success {
  background: rgba(52, 199, 89, 0.12);
  color: #34c759;
}

.upload-feedback-badge.error {
  background: rgba(255, 59, 48, 0.12);
  color: #ff3b30;
}

/* Dramas Grid */
.dramas-list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.my-drama-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.drama-cover-box {
  height: 160px;
  background-size: cover;
  background-position: center;
  position: relative;
  padding: 12px;
}

.status-chip {
  background: rgba(52, 199, 89, 0.85);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 6px;
}

.drama-info-box {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.drama-card-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 8px;
  color: #18191c;
}

.drama-card-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.tag-pill {
  font-size: 11px;
  background: #f2f2f7;
  padding: 2px 8px;
  border-radius: 6px;
  color: #6e6e73;
}

.drama-card-desc {
  font-size: 13px;
  color: #6e6e73;
  line-height: 1.5;
  margin: 0 0 14px;
  flex: 1;
}

.drama-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding-top: 10px;
}

.time-label {
  font-size: 12px;
  color: #a1a1a6;
}

.play-action-btn {
  background: transparent;
  border: none;
  color: #0071e3;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

/* Modal */
.modal-backdrop-scrim {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(28px);
  border-radius: 24px;
  padding: 32px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.15);
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 6px;
  color: #18191c;
}

.modal-subtext {
  font-size: 13px;
  color: #6e6e73;
  margin: 0 0 20px;
}

.modal-actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

/* Drama Actions & Episodes Drawer */
.drama-actions-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-xs {
  padding: 4px 10px;
  font-size: 11px;
}

.btn-danger-text {
  color: #FF3B30 !important;
}

.btn-danger-text:hover {
  background: rgba(255, 59, 48, 0.1) !important;
}

.modal-wide {
  max-width: 780px !important;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.drawer-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.close-x-btn {
  background: rgba(0, 0, 0, 0.06);
  border: none;
  font-size: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6e6e73;
}

.close-x-btn:hover {
  background: rgba(0, 0, 0, 0.12);
}

.episodes-manage-table-wrap {
  overflow-y: auto;
  max-height: 52vh;
  margin: 12px 0;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.creator-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.creator-table th {
  background: #F5F5F7;
  padding: 10px 14px;
  text-align: left;
  color: #6e6e73;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 2;
}

.creator-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  color: #18191c;
}

.table-inline-input {
  width: 100%;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: #FFFFFF;
  font-size: 13px;
  outline: none;
}

.table-inline-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

.table-inline-input.mini {
  width: 80px;
}

.climax-input-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sec-unit {
  font-size: 12px;
  color: #8E8E93;
}

/* ========================================================================== */
/* Creator Studio BI Dashboard & Bento Cards                                  */
/* ========================================================================== */
.creator-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-bento-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 18px;
  padding: 20px 22px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-bento-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.kpi-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kpi-label {
  font-size: 13px;
  color: #6e6e73;
  font-weight: 500;
}

.kpi-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.kpi-badge.blue { background: rgba(0, 113, 227, 0.1); color: #0071e3; }
.kpi-badge.pink { background: rgba(255, 45, 85, 0.1); color: #ff2d55; }
.kpi-badge.amber { background: rgba(245, 158, 11, 0.15); color: #d97706; }
.kpi-badge.green { background: rgba(52, 199, 89, 0.12); color: #28cd41; }

.kpi-value-num {
  font-size: 28px;
  font-weight: 800;
  color: #1d1d1f;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}

.kpi-value-num.text-amber {
  color: #d97706;
}

.kpi-hint {
  font-size: 11px;
  color: #86868b;
}

.creator-bi-table-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #0071e3;
}

.bi-card-title {
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0;
}

.bi-card-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  border-radius: 999px;
}

.table-container {
  overflow-x: auto;
}

.creator-bi-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.creator-bi-table th {
  background: #f5f5f7;
  color: #6e6e73;
  font-weight: 600;
  padding: 12px 14px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.creator-bi-table td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  color: #1d1d1f;
}

.bi-tag-pill {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  font-weight: 600;
}

.score-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(52, 199, 89, 0.1);
  color: #28cd41;
  font-weight: 700;
  font-size: 11px;
}

.status-indicator-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.status-indicator-tag.tag-pub {
  background: rgba(52, 199, 89, 0.12);
  color: #28cd41;
}

.status-indicator-tag.tag-draft {
  background: rgba(142, 142, 147, 0.12);
  color: #8e8e93;
}

.creator-insights-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.insight-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 18px;
  padding: 20px 24px;
}

.insight-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.insight-icon {
  color: #0071e3;
  font-size: 16px;
}

.insight-head h4 {
  font-size: 14px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0;
}

.insight-card p {
  font-size: 12px;
  color: #6e6e73;
  line-height: 1.6;
  margin: 0;
}

/* ========================================================================== */
/* Dark Mode Overrides for Creator Studio (Apple HIG)                         */
/* ========================================================================== */
[data-theme="dark"] .creator-studio-container {
  background-color: #121214 !important;
  color: #f5f5f7 !important;
}

[data-theme="dark"] .studio-page-title,
[data-theme="dark"] .bi-card-title,
[data-theme="dark"] .kpi-value-num,
[data-theme="dark"] .insight-head h4,
[data-theme="dark"] .panel-section-title,
[data-theme="dark"] .drama-card-title {
  color: #f5f5f7 !important;
}

[data-theme="dark"] .studio-subtext,
[data-theme="dark"] .kpi-label,
[data-theme="dark"] .kpi-hint,
[data-theme="dark"] .insight-card p,
[data-theme="dark"] .form-label,
[data-theme="dark"] .drama-card-desc,
[data-theme="dark"] .time-label {
  color: #86868b !important;
}

[data-theme="dark"] .kpi-bento-card,
[data-theme="dark"] .creator-bi-table-card,
[data-theme="dark"] .insight-card,
[data-theme="dark"] .tab-content-panel,
[data-theme="dark"] .my-drama-card,
[data-theme="dark"] .pan-item-card,
[data-theme="dark"] .upload-builder-grid,
[data-theme="dark"] .modal-glass-card {
  background: rgba(22, 22, 26, 0.85) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] .creator-bi-table th,
[data-theme="dark"] .creator-table th {
  background: rgba(255, 255, 255, 0.04) !important;
  color: #86868b !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}

[data-theme="dark"] .creator-bi-table td,
[data-theme="dark"] .creator-table td {
  color: #f5f5f7 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

[data-theme="dark"] .tab-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #86868b !important;
}

[data-theme="dark"] .tab-btn.active {
  background: #0071e3 !important;
  color: #ffffff !important;
}

[data-theme="dark"] .apple-text-input,
[data-theme="dark"] .table-inline-input {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #f5f5f7 !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
}

[data-theme="dark"] .apple-text-input:focus,
[data-theme="dark"] .table-inline-input:focus {
  border-color: #0071e3 !important;
  background: rgba(255, 255, 255, 0.12) !important;
}
</style>
