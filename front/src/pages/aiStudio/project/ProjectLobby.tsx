import React, { useEffect, useMemo, useState } from 'react'
import {
  Card,
  Input,
  Button,
  Progress,
  Statistic,
  Row,
  Col,
  Modal,
  Form,
  Select,
  InputNumber,
  Switch,
  message,
  Space,
  Segmented,
  Tag,
  Tooltip,
  Popconfirm,
  Upload,
} from 'antd'
import {
  EditOutlined,
  DeleteOutlined,
  EnterOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  BarsOutlined,
  DeploymentUnitOutlined,
  UploadOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { chapters as mockChapters, projects as mockProjects, type Project } from '../../../mocks/data'
import { StudioChaptersService, StudioProjectsService } from '../../../services/generated'
import type { ChapterRead, ProjectRead, ProjectStyle } from '../../../services/generated'
import {
  ProjectVisualStyleAndStyleFields,
  type ProjectVisualStyleChoice,
} from './ProjectVisualStyleAndStyleFields'
import { useProjectStyleOptions } from './useProjectStyleOptions'
import { getChapterPreparationState } from './ProjectWorkbench/chapterPreparation'
import { ensureHasShotsBeforeShooting } from './ProjectWorkbench/ensureHasShotsBeforeShooting'
import { getChapterShotsPath, getChapterStudioPath, getProjectFilmCorePath } from './ProjectWorkbench/routes'
import { loadProjectFlowStatsForChapters, type ProjectFlowStats } from './ProjectWorkbench/projectFlowStats'
import { createTextToDrama } from '../../../services/industrialFilm'

type ViewMode = 'grid' | 'compact' | 'large'
type FilterTab = 'all' | 'editRaw' | 'extractShots' | 'prepareShots' | 'generating' | 'ready'
type SortKey = 'updatedAt' | 'name' | 'createdAt' | 'chapters'
type CreationMode = 'text_to_drama' | 'blank'
type ChapterPreparationInput = Parameters<typeof getChapterPreparationState>[0]
type ProjectStageSummary = {
  key: ReturnType<typeof getChapterPreparationState>['key'] | 'create_first_chapter'
  stageText: string
  stageColor: string
  nextActionLabel: string
  nextActionHint: string
  chapterId?: string
  storyboardCount?: number
}
type ProjectFlowStatsMap = Record<string, ProjectFlowStats>
type ProjectView = Project & {
  visualStyle?: ProjectVisualStyleChoice
  defaultVideoRatio?: string | null
}

const ProjectLobby: React.FC = () => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<ProjectView[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filterTab, setFilterTab] = useState<FilterTab>('all')
  const [sortKey, setSortKey] = useState<SortKey>('updatedAt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [multiSelectMode, setMultiSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [creatingProject, setCreatingProject] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<ProjectView | null>(null)
  const [projectStageMap, setProjectStageMap] = useState<Record<string, ProjectStageSummary>>({})
  const [projectFlowStatsMap, setProjectFlowStatsMap] = useState<ProjectFlowStatsMap>({})
  const {
    options: projectStyleOptions,
    videoRatioOptions,
    defaultVideoRatio,
  } = useProjectStyleOptions()
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const creationMode = (Form.useWatch('creation_mode', form) as CreationMode | undefined) ?? 'text_to_drama'

  const useMock = import.meta.env.VITE_USE_MOCK === 'true'

  const toUIProject = (p: ProjectRead): ProjectView => {
    const stats = (p.stats ?? {}) as Record<string, unknown>
    const getNum = (key: string) => {
      const v = stats[key]
      return typeof v === 'number' && Number.isFinite(v) ? v : 0
    }

    const updatedAt =
      (typeof stats.updated_at === 'string' && stats.updated_at) ||
      (typeof stats.updatedAt === 'string' && stats.updatedAt) ||
      new Date().toISOString()

    return {
      id: p.id,
      name: p.name,
      description: p.description ?? '',
      style: (p.style as Project['style']) ?? '现实主义',
      seed: p.seed ?? 0,
      unifyStyle: p.unify_style ?? true,
      progress: p.progress ?? 0,
      stats: {
        chapters: getNum('chapters'),
        roles: getNum('roles'),
        scenes: getNum('scenes'),
        props: getNum('props'),
      },
      updatedAt,
      visualStyle: (p.visual_style as ProjectVisualStyleChoice | undefined) ?? '现实',
      defaultVideoRatio: p.default_video_ratio ?? null,
    }
  }

  const newProjectId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
    return `p_${Date.now()}_${Math.random().toString(16).slice(2)}`
  }

  const load = async () => {
    setLoading(true)
    try {
      if (useMock) {
        setProjects(mockProjects)
      } else {
        const res = await StudioProjectsService.listProjectsApiV1StudioProjectsGet({
          page: 1,
          pageSize: 10,
        })
        const items = res.data?.items ?? []
        setProjects(items.map(toUIProject))
      }
    } catch {
      setProjects(useMock ? mockProjects : [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const getProjectStatus = (p: ProjectView): 'draft' | 'inProgress' | 'completed' => {
    if (p.progress >= 90) return 'completed'
    if (p.progress <= 5) return 'draft'
    return 'inProgress'
  }

  useEffect(() => {
    const list = Array.isArray(projects) ? projects : []
    if (!list.length) {
      setProjectStageMap({})
      setProjectFlowStatsMap({})
      return
    }

    const summarizeProjectChapters = (chapters: ChapterPreparationInput[]): ProjectStageSummary => {
      const chaptersByIndex = [...chapters].sort((a, b) => a.index - b.index)
      if (!chaptersByIndex.length) {
        return {
          key: 'create_first_chapter',
          stageText: '待创建章节',
          stageColor: 'default',
          nextActionLabel: '创建第一章',
          nextActionHint: '项目还没有章节，建议先创建第一章',
        }
      }
      const findByState = (key: ReturnType<typeof getChapterPreparationState>['key']) =>
        chaptersByIndex.find((chapter) => getChapterPreparationState(chapter).key === key)
      const chapter =
        findByState('edit_raw') ??
        findByState('extract_shots') ??
        findByState('prepare_shots') ??
        findByState('shoot') ??
        chaptersByIndex[0]
      const state = getChapterPreparationState(chapter)
      return {
        key: state.key,
        stageText: state.text,
        stageColor: state.color,
        nextActionLabel: state.primaryAction,
        nextActionHint: `第${chapter.index}章 · ${state.hint}`,
        chapterId: chapter.id,
        storyboardCount: chapter.storyboardCount,
      }
    }

    const loadSummaries = async () => {
      try {
        if (useMock) {
          const chapterGroups = Object.fromEntries(
            list.map((project) => [
              project.id,
              mockChapters
                .filter((chapter) => chapter.projectId === project.id)
                .map((chapter) => ({
                  id: chapter.id,
                  projectId: chapter.projectId,
                  index: chapter.index,
                  title: chapter.title,
                  summary: chapter.summary ?? '',
                  rawText: chapter.summary ?? '',
                  storyboardCount: chapter.storyboardCount,
                  status: chapter.status,
                  updatedAt: chapter.updatedAt,
                })),
            ]),
          )
          setProjectStageMap(
            Object.fromEntries(
              Object.entries(chapterGroups).map(([projectId, chapters]) => [
                projectId,
                summarizeProjectChapters(chapters),
              ]),
            ),
          )
          const flowStatsEntries = await Promise.all(
            Object.entries(chapterGroups).map(async ([projectId, chapters]) => [
              projectId,
              await loadProjectFlowStatsForChapters(chapters),
            ] as const),
          )
          setProjectFlowStatsMap(Object.fromEntries(flowStatsEntries))
          return
        }

        const chapterResponses = await Promise.all(
          list.map(async (project) => {
            const res = await StudioChaptersService.listChaptersApiV1StudioChaptersGet({
              projectId: project.id,
              page: 1,
              pageSize: 100,
            })
            const items: ChapterRead[] = res.data?.items ?? []
            return [
              project.id,
              summarizeProjectChapters(
                items.map((chapter) => ({
                  id: chapter.id,
                  projectId: chapter.project_id,
                  index: chapter.index,
                  title: chapter.title,
                  summary: chapter.summary ?? '',
                  rawText: chapter.raw_text ?? '',
                  storyboardCount: chapter.shot_count ?? chapter.storyboard_count ?? 0,
                  status: chapter.status ?? 'draft',
                  updatedAt: new Date().toISOString(),
                })),
              ),
              items.map((chapter) => ({
                id: chapter.id,
                projectId: chapter.project_id,
                index: chapter.index,
                title: chapter.title,
                summary: chapter.summary ?? '',
                rawText: chapter.raw_text ?? '',
                storyboardCount: chapter.shot_count ?? chapter.storyboard_count ?? 0,
                status: chapter.status ?? 'draft',
                updatedAt: new Date().toISOString(),
              })),
            ] as const
          }),
        )
        setProjectStageMap(
          Object.fromEntries(chapterResponses.map(([projectId, summary]) => [projectId, summary])),
        )
        const flowStatsEntries = await Promise.all(
          chapterResponses.map(async ([projectId, _summary, chapters]) => [
            projectId,
            await loadProjectFlowStatsForChapters(chapters),
          ] as const),
        )
        setProjectFlowStatsMap(Object.fromEntries(flowStatsEntries))
      } catch {
        setProjectStageMap({})
        setProjectFlowStatsMap({})
      }
    }

    void loadSummaries()
  }, [projects, useMock])

  const filteredSorted = useMemo(() => {
    const list = Array.isArray(projects) ? projects : []
    const keyword = search.trim().toLowerCase()

    let next = list.filter((p) => {
      if (keyword) {
        const inText =
          p.name.toLowerCase().includes(keyword) ||
          p.description.toLowerCase().includes(keyword)
        if (!inText) return false
      }

      if (filterTab === 'all') return true
      const stage = projectStageMap[p.id]
      const flowStats = projectFlowStatsMap[p.id]
      if (filterTab === 'editRaw') return stage?.key === 'edit_raw' || stage?.key === 'create_first_chapter'
      if (filterTab === 'extractShots') return stage?.key === 'extract_shots'
      if (filterTab === 'prepareShots') return stage?.key === 'prepare_shots'
      if (filterTab === 'generating') return (flowStats?.generatingShots ?? 0) > 0
      if (filterTab === 'ready') return (flowStats?.readyShots ?? 0) > 0
      return true
    })

    next.sort((a, b) => {
      let av: string | number = ''
      let bv: string | number = ''
      if (sortKey === 'name') {
        av = a.name
        bv = b.name
      } else if (sortKey === 'chapters') {
        av = a.stats.chapters
        bv = b.stats.chapters
      } else if (sortKey === 'createdAt') {
        av = a.id
        bv = b.id
      } else {
        av = a.updatedAt
        bv = b.updatedAt
      }

      if (typeof av === 'number' && typeof bv === 'number') {
        return sortOrder === 'asc' ? av - bv : bv - av
      }
      const res = String(av).localeCompare(String(bv))
      return sortOrder === 'asc' ? res : -res
    })

    return next
  }, [projects, search, filterTab, sortKey, sortOrder, projectStageMap, projectFlowStatsMap])

  const handleSelectProject = (id: string) => {
    setSelectedProjectId(id)
  }

  const handleToggleSelect = (id: string, checked: boolean) => {
    setSelectedIds((prev) =>
      checked ? Array.from(new Set([...prev, id])) : prev.filter((x) => x !== id)
    )
  }

  const handleBatchDelete = async () => {
    if (!selectedIds.length) return
    try {
      await Promise.all(
        selectedIds.map((id) =>
          StudioProjectsService.deleteProjectApiV1StudioProjectsProjectIdDelete({ projectId: id }),
        ),
      )
      setProjects((prev) =>
        Array.isArray(prev) ? prev.filter((p) => !selectedIds.includes(p.id)) : prev
      )
      setSelectedIds([])
      message.success('已批量删除选中项目')
    } catch {
      message.error('批量删除失败')
    }
  }

  const handleOpenCreate = () => {
    form.resetFields()
    const defaultVisual = (projectStyleOptions.visualStyles[0]?.value ?? '动漫') as ProjectVisualStyleChoice
    const defaultStyle =
      projectStyleOptions.defaultStyleByVisual?.[defaultVisual] ??
      projectStyleOptions.stylesByVisual[defaultVisual]?.[0]?.value ??
      '国漫'
    form.setFieldsValue({
      creation_mode: 'text_to_drama',
      visual_style: defaultVisual,
      style: defaultStyle,
      seed: Math.floor(Math.random() * 99999),
      unifyStyle: true,
      episode_count: 3,
      shots_per_episode: 6,
      default_video_ratio: defaultVideoRatio ?? '9:16',
      automation_mode: 'automatic',
      reference_harvest_enabled: true,
    })
    setCreateModalOpen(true)
  }

  /**
   * 将本地小说文本文件读取到统一创建表单；文件本身不上传服务器。
   */
  const handleNovelFileBeforeUpload = (file: File) => {
    const fileName = file.name.toLowerCase()
    if (!fileName.endsWith('.txt') && !fileName.endsWith('.md')) {
      message.error('仅支持 .txt / .md 小说文本文件')
      return Upload.LIST_IGNORE
    }
    void file
      .text()
      .then((text) => {
        form.setFieldsValue({
          creation_mode: 'text_to_drama',
          source_text: text,
          project_name: form.getFieldValue('project_name') || file.name.replace(/\.(txt|md)$/i, ''),
        })
        message.success('小说文件已读取')
      })
      .catch(() => {
        message.error('读取小说文件失败')
      })
    return false
  }

  const handleCreateSubmit = async (values: {
    creation_mode?: CreationMode
    name?: string
    project_name?: string
    description?: string
    source_text?: string
    style: string
    visual_style: ProjectVisualStyleChoice
    seed?: number
    unifyStyle?: boolean
    default_video_ratio?: string
    episode_count?: number
    shots_per_episode?: number
    automation_mode?: 'automatic' | 'manual'
    reference_harvest_enabled?: boolean
  }) => {
    const selectedMode = values.creation_mode ?? 'text_to_drama'
    const sourceText = values.source_text?.trim() ?? ''
    setCreatingProject(true)
    try {
      if (selectedMode === 'text_to_drama') {
        if (!sourceText) {
          message.error('请输入一句话、梗概、正文，或先上传小说文件')
          return
        }
        const data = await createTextToDrama({
          source_text: sourceText,
          project_name: values.project_name || null,
          style: values.style as ProjectStyle,
          visual_style: values.visual_style as any,
          episode_count: values.episode_count ?? 3,
          shots_per_episode: values.shots_per_episode ?? 6,
          default_video_ratio: values.default_video_ratio || '9:16',
          automation_mode: values.automation_mode ?? 'automatic',
          reference_harvest_enabled: values.reference_harvest_enabled ?? true,
        })
        message.success(
          `已创建 ${data.chapters.length} 集、${data.created_shot_count} 个镜头、${data.created_character_count} 个角色资产`,
        )
        setCreateModalOpen(false)
        await load()
        navigate(data.next_url)
        return
      }

      const createdId = newProjectId()
      const projectName = values.name?.trim() || values.project_name?.trim()
      if (!projectName) {
        message.error('请输入项目名称')
        return
      }
      const res = await StudioProjectsService.createProjectApiV1StudioProjectsPost({
        requestBody: {
          id: createdId,
          name: projectName,
          description: values.description ?? '',
          style: values.style as ProjectStyle,
          visual_style: values.visual_style as any,
          seed: values.seed ?? Math.floor(Math.random() * 99999),
          unify_style: values.unifyStyle ?? true,
          default_video_ratio: values.default_video_ratio || null,
          progress: 0,
        },
      })
      const created = res.data
      if (!created) throw new Error('empty project')
      const ui = toUIProject(created)
      message.success('项目创建成功')
      setCreateModalOpen(false)
      setProjects((prev) => (Array.isArray(prev) ? [...prev, ui] : [ui]))
      navigate(`/projects/${ui.id}?tab=chapters`)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建失败'
      message.error(msg)
    } finally {
      setCreatingProject(false)
    }
  }

  const handleOpenEdit = (e: React.MouseEvent, p: ProjectView) => {
    e.stopPropagation()
    setEditingProject(p)
    editForm.setFieldsValue({
      name: p.name,
      description: p.description,
      style: p.style,
      visual_style: p.visualStyle ?? '现实',
      seed: p.seed,
      unifyStyle: p.unifyStyle,
      default_video_ratio: p.defaultVideoRatio ?? undefined,
    })
    setEditModalOpen(true)
  }

  const handleEditSubmit = async (values: {
    name: string
    description?: string
    style: string
    visual_style: ProjectVisualStyleChoice
    seed: number
    unifyStyle: boolean
    default_video_ratio?: string
  }) => {
    if (!editingProject) return
    try {
      const res = await StudioProjectsService.updateProjectApiV1StudioProjectsProjectIdPatch({
        projectId: editingProject.id,
        requestBody: {
          name: values.name,
          description: values.description ?? '',
          style: values.style as ProjectStyle,
          visual_style: values.visual_style as any,
          seed: values.seed,
          unify_style: values.unifyStyle,
          default_video_ratio: values.default_video_ratio || null,
        },
      })
      const updated = res.data
      if (!updated) throw new Error('empty project')
      const ui = toUIProject(updated)
      message.success('项目已更新')
      setEditModalOpen(false)
      setEditingProject(null)
      setProjects((prev) =>
        Array.isArray(prev) ? prev.map((x) => (x.id === ui.id ? ui : x)) : prev
      )
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (projectId: string) => {
    try {
      await StudioProjectsService.deleteProjectApiV1StudioProjectsProjectIdDelete({ projectId })
      message.success('已删除')
      setProjects((prev) => (Array.isArray(prev) ? prev.filter((p) => p.id !== projectId) : []))
    } catch {
      message.error('删除失败')
    }
  }

  const renderStatusTag = (p: ProjectView) => {
    const status = getProjectStatus(p)
    if (status === 'completed') return <Tag color="green" className="mr-0 text-[11px] leading-4">已完成</Tag>
    if (status === 'draft') return <Tag color="default" className="mr-0 text-[11px] leading-4">草稿</Tag>
    return <Tag color="orange" className="mr-0 text-[11px] leading-4">进行中</Tag>
  }

  const handlePrimaryAction = (project: ProjectView, stageSummary?: ProjectStageSummary) => {
    if (!stageSummary) {
      navigate(`/projects/${project.id}`)
      return
    }
    if (stageSummary.key === 'create_first_chapter') {
      navigate(`/projects/${project.id}?tab=chapters&create=1`)
      return
    }
    if (!stageSummary.chapterId) {
      navigate(`/projects/${project.id}`)
      return
    }
    if (stageSummary.key === 'edit_raw') {
      navigate(`/projects/${project.id}?tab=chapters&edit=${stageSummary.chapterId}`)
      return
    }
    if (stageSummary.key === 'extract_shots') {
      navigate(getChapterShotsPath(project.id, stageSummary.chapterId))
      return
    }
    if (stageSummary.key === 'prepare_shots') {
      navigate(getChapterStudioPath(project.id, stageSummary.chapterId))
      return
    }
    void ensureHasShotsBeforeShooting({
      projectId: project.id,
      chapterId: stageSummary.chapterId,
      storyboardCount: stageSummary.storyboardCount,
      navigate,
    })
  }

  /**
   * 根据项目 ID 生成稳定的浅色渐变背景，避免深色背景。
   */
  const getLightGradientByProjectId = (id: string): string => {
    const gradients = [
      'from-sky-100 via-sky-50 to-white',
      'from-emerald-100 via-emerald-50 to-white',
      'from-indigo-100 via-indigo-50 to-white',
      'from-amber-100 via-amber-50 to-white',
      'from-rose-100 via-rose-50 to-white',
      'from-violet-100 via-violet-50 to-white',
      'from-teal-100 via-teal-50 to-white',
    ]

    let hash = 0
    for (let i = 0; i < id.length; i += 1) {
      hash = (hash * 31 + id.charCodeAt(i)) >>> 0
    }

    const index = hash % gradients.length
    return gradients[index]
  }

  const selectedProject = filteredSorted.find((p) => p.id === selectedProjectId) ?? filteredSorted[0]

  /**
   * 打开项目级 Film Core；空项目工作区会先进入项目创建，避免入口灰掉后无法发现。
   */
  const handleOpenFilmCoreEntry = () => {
    if (selectedProject) {
      navigate(getProjectFilmCorePath(selectedProject.id))
      return
    }

    // 重要状态变化：没有项目时先拉起创建弹窗，创建成功后会进入项目工作台。
    handleOpenCreate()
    message.info('先创建项目，随后可在项目工作台查看 Film Core')
  }

  const renderCard = (p: ProjectView) => {
    const status = getProjectStatus(p)
    const stageSummary = projectStageMap[p.id]
    const flowStats = projectFlowStatsMap[p.id]
    const isCompact = viewMode === 'compact'
    const isLarge = viewMode === 'large'
    const mainActionLabel = stageSummary?.nextActionLabel ?? (status === 'completed' ? '继续剪辑' : p.progress > 0 ? '继续拍摄' : '进入项目')

    const isSelected = selectedProject && selectedProject.id === p.id
    const isChecked = selectedIds.includes(p.id)

    return (
      <Card
        key={p.id}
        hoverable
        loading={loading}
        size="small"
        className={`h-full cursor-pointer transition-all duration-200 ${
          isSelected ? 'ring-2 ring-indigo-500 ring-offset-1' : 'hover:shadow-lg'
        }`}
        bodyStyle={{ padding: '10px' }}
        onClick={() => {
          handleSelectProject(p.id)
          if (!multiSelectMode) {
            navigate(`/projects/${p.id}`)
          }
        }}
        onMouseEnter={() => handleSelectProject(p.id)}
      >
        <div
          className={`relative mb-1.5 rounded bg-gradient-to-r ${getLightGradientByProjectId(
            p.id,
          )} text-gray-900 p-2 overflow-hidden`}
        >
          <div className="flex justify-between items-start gap-2">
            <div className="min-w-0">
              <div className="text-xs text-gray-500 mb-0.5">{p.style}</div>
              <div className={`${isCompact ? 'text-sm' : 'text-base'} font-semibold truncate text-gray-900`}>
                {p.name}
              </div>
              <div className="text-[10px] text-gray-500 truncate">
                {p.updatedAt}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              {renderStatusTag(p)}
              {multiSelectMode && (
                <input
                  type="checkbox"
                  className="cursor-pointer"
                  checked={isChecked}
                  onChange={(e) => {
                    e.stopPropagation()
                    handleToggleSelect(p.id, e.target.checked)
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
              )}
            </div>
          </div>
        </div>

        {!isCompact && (
          <p className={`text-gray-600 text-xs mb-1.5 ${isLarge ? 'line-clamp-2 min-h-[2rem]' : 'line-clamp-1 min-h-0'}`}>
            {p.description}
          </p>
        )}

        <div className={`mb-1.5 rounded border border-gray-100 bg-gray-50 ${isCompact ? 'px-2 py-1' : 'px-2 py-1.5'}`}>
          <div className="flex items-center justify-between gap-2">
            <span className="text-[11px] text-gray-500">当前阶段</span>
            <Tag color={stageSummary?.stageColor ?? 'default'} className="mr-0 text-[11px] leading-4">
              {stageSummary?.stageText ?? '待推进'}
            </Tag>
          </div>
          <div className={`mt-1 text-[11px] text-gray-600 ${isLarge ? 'line-clamp-2 min-h-[2rem]' : 'line-clamp-1 min-h-0'}`}>
            {stageSummary?.nextActionHint ?? '进入项目工作台后继续推进主流程'}
          </div>
          {isCompact ? (
            <div className="mt-1 text-[11px] text-gray-500 truncate">
              下一步：{stageSummary?.nextActionLabel ?? '进入项目'}
            </div>
          ) : (
            <div className="mt-1.5 flex flex-wrap gap-1">
              <Tag bordered={false} color="gold" className="mr-0 text-[11px]">
                待确认 {flowStats?.pendingConfirmShots ?? 0}
              </Tag>
              <Tag bordered={false} color="green" className="mr-0 text-[11px]">
                已就绪 {flowStats?.readyShots ?? 0}
              </Tag>
              <Tag bordered={false} color="processing" className="mr-0 text-[11px]">
                生成中 {flowStats?.generatingShots ?? 0}
              </Tag>
            </div>
          )}
        </div>

        {!isCompact && (
          <div className="mb-1.5">
            <div className="flex justify-between text-[11px] mb-0.5 text-gray-500">
              <span>进度</span>
              <span>{p.progress}%</span>
            </div>
            <Progress
              percent={p.progress}
              size="small"
              showInfo={false}
              strokeColor={{ from: '#6366f1', to: '#a855f7' }}
            />
          </div>
        )}

        {isLarge ? (
          <Row gutter={6} className="mb-1.5">
            <Col span={6}>
              <Statistic title={<span className="text-[11px]">章节</span>} value={p.stats.chapters} valueStyle={{ fontSize: '13px' }} />
            </Col>
            <Col span={6}>
              <Statistic title={<span className="text-[11px]">角色</span>} value={p.stats.roles} valueStyle={{ fontSize: '13px' }} />
            </Col>
            <Col span={6}>
              <Statistic title={<span className="text-[11px]">场景</span>} value={p.stats.scenes} valueStyle={{ fontSize: '13px' }} />
            </Col>
            <Col span={6}>
              <Statistic title={<span className="text-[11px]">道具</span>} value={p.stats.props} valueStyle={{ fontSize: '13px' }} />
            </Col>
          </Row>
        ) : (
          <div className="mb-1.5 text-[11px] text-gray-500 truncate">
            章 {p.stats.chapters} · 角 {p.stats.roles} · 场 {p.stats.scenes} · 道 {p.stats.props}
          </div>
        )}

        <div className={`mt-1 border-t border-gray-100 flex items-center justify-between gap-1 ${isCompact ? 'pt-1' : 'pt-1.5'}`}>
          <span className="text-[11px] text-gray-500 truncate">{p.updatedAt}</span>
          <Space size="small" onClick={(e) => e.stopPropagation()}>
            <Button
              type="primary"
              size="small"
              icon={<EnterOutlined />}
              onClick={() => handlePrimaryAction(p, stageSummary)}
              className="text-[11px]"
            >
              {isCompact ? '进入' : mainActionLabel}
            </Button>
            {!isCompact && (
              <>
                <Button
                  type="text"
                  size="small"
                  icon={<DeploymentUnitOutlined />}
                  onClick={() => navigate(getProjectFilmCorePath(p.id))}
                  className="text-[11px]"
                >
                  Film Core
                </Button>
                <Button
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={(e) => handleOpenEdit(e, p)}
                  className="text-[11px]"
                />
                <Popconfirm
                  title="确定删除该项目？"
                  description="删除后无法恢复，相关章节与素材将不再关联。"
                  onConfirm={() => handleDelete(p.id)}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} className="text-[11px]" />
                </Popconfirm>
              </>
            )}
          </Space>
        </div>
      </Card>
    )
  }

  return (
    <div className="min-h-0 flex-1 flex flex-col overflow-hidden">
      <div className="flex-shrink-0 space-y-2 pb-2">
      <div className="sticky top-0 z-10 pb-1.5 bg-gradient-to-b from-[rgba(249,250,251,0.96)] to-[rgba(249,250,251,0.9)] backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Space wrap size="small" className="flex-1 min-w-[240px]">
            <Input.Search
              placeholder="搜索项目名称或描述"
              allowClear
              size="small"
              className="w-64 max-w-full"
              onSearch={setSearch}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Space size="small" wrap>
              <Button
                type={filterTab === 'all' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('all')}
              >
                全部
              </Button>
              <Button
                type={filterTab === 'editRaw' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('editRaw')}
              >
                待补原文
              </Button>
              <Button
                type={filterTab === 'extractShots' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('extractShots')}
              >
                待提取分镜
              </Button>
              <Button
                type={filterTab === 'prepareShots' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('prepareShots')}
              >
                待准备镜头
              </Button>
              <Button
                type={filterTab === 'generating' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('generating')}
              >
                生成中
              </Button>
              <Button
                type={filterTab === 'ready' ? 'primary' : 'text'}
                size="small"
                className="text-[11px]"
                onClick={() => setFilterTab('ready')}
              >
                可继续推进
              </Button>
            </Space>
          </Space>

            <Space size="small" wrap>
            <Space size="small">
              <span className="text-xs text-gray-500">排序</span>
              <Select
                size="small"
                value={sortKey}
                style={{ width: 128 }}
                onChange={(value: SortKey) => setSortKey(value)}
                options={[
                  { label: '最近更新', value: 'updatedAt' },
                  { label: '名称 A-Z', value: 'name' },
                  { label: '章节数量', value: 'chapters' },
                ]}
              />
              <Button
                size="small"
                type="text"
                className="text-[11px]"
                onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </Button>
            </Space>

            <Space size="small">
              <span className="text-xs text-gray-500">视图</span>
              <Button
                size="small"
                type={viewMode === 'grid' ? 'primary' : 'text'}
                icon={<AppstoreOutlined />}
                onClick={() => setViewMode('grid')}
              />
              <Button
                size="small"
                type={viewMode === 'compact' ? 'primary' : 'text'}
                icon={<BarsOutlined />}
                onClick={() => setViewMode('compact')}
              />
              <Button
                size="small"
                type={viewMode === 'large' ? 'primary' : 'text'}
                icon={<UnorderedListOutlined />}
                onClick={() => setViewMode('large')}
              />
            </Space>

            <Space size="small">
              <Button
                size="small"
                type={multiSelectMode ? 'primary' : 'text'}
                className="text-[11px]"
                onClick={() => {
                  setMultiSelectMode((prev) => !prev)
                  setSelectedIds([])
                }}
              >
                批量
              </Button>
              {multiSelectMode && (
                <Popconfirm
                  title="批量删除项目"
                  description="确定删除选中的所有项目？该操作不可恢复。"
                  onConfirm={handleBatchDelete}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  disabled={!selectedIds.length}
                >
                  <Button size="small" danger disabled={!selectedIds.length} className="text-[11px]">
                    删除选中
                  </Button>
                </Popconfirm>
              )}
            </Space>

            <Button type="primary" size="small" className="text-[11px]" icon={<RocketOutlined />} onClick={handleOpenCreate}>
              创建 AI 漫剧
            </Button>
          </Space>
        </div>
      </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
      <Row gutter={12}>
        <Col xs={24} lg={18}>
          <Row gutter={viewMode === 'compact' ? [8, 8] : viewMode === 'large' ? [14, 14] : [12, 12]}>
            {!loading && filteredSorted.length === 0 && (
              <Col span={24}>
                <Card>
                  <div className="text-center text-gray-500 py-8 text-sm space-y-3">
                    <div>{search ? '没有匹配的项目' : '暂无项目，点击「创建 AI 漫剧」开始'}</div>
                    {!search ? (
                      <Space size="small" wrap>
                        <Button type="primary" size="small" icon={<RocketOutlined />} onClick={handleOpenCreate}>
                          创建 AI 漫剧
                        </Button>
                        <Tooltip title="Film Core 是项目级 overview；创建项目后自动出现在项目工作台。">
                          <Button size="small" icon={<DeploymentUnitOutlined />} onClick={handleOpenFilmCoreEntry}>
                            Film Core
                          </Button>
                        </Tooltip>
                      </Space>
                    ) : null}
                  </div>
                </Card>
              </Col>
            )}
            {filteredSorted.map((p) => (
              <Col
                key={p.id}
                xs={24}
                sm={viewMode === 'compact' ? 12 : viewMode === 'grid' ? 12 : 24}
                md={viewMode === 'compact' ? 8 : viewMode === 'grid' ? 8 : 24}
                lg={viewMode === 'compact' ? 6 : viewMode === 'grid' ? 6 : 24}
                xl={viewMode === 'compact' ? 4 : viewMode === 'grid' ? 6 : 24}
              >
                {renderCard(p)}
              </Col>
            ))}
          </Row>
        </Col>

        <Col xs={24} lg={6} className="flex-shrink-0">
          <div className="h-full">
            <Card
              size="small"
              title="项目速览"
              className="mb-1.5"
              bodyStyle={{ padding: '10px' }}
              headStyle={{ minHeight: 36, paddingInline: 10 }}
            >
              {selectedProject ? (
                <div className="space-y-2">
                  <div>
                    <div className="text-[11px] text-gray-500 mb-0.5">项目名称</div>
                    <div className="font-medium">{selectedProject.name}</div>
                  </div>
                  <div>
                    <div className="text-[11px] text-gray-500 mb-0.5">简介</div>
                    <div className="text-xs text-gray-600 line-clamp-2">
                      {selectedProject.description || '暂无描述'}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-gray-500">
                    <span>视频风格：{selectedProject.style}</span>
                    <span>种子：{selectedProject.seed}</span>
                  </div>
                  <div>
                    <div className="text-[11px] text-gray-500 mb-0.5">进度</div>
                    <Progress
                      percent={selectedProject.progress}
                      size="small"
                      strokeColor={{ from: '#6366f1', to: '#22c55e' }}
                    />
                  </div>
                  <div className="text-[11px] text-gray-500">
                    章 {selectedProject.stats.chapters} · 角 {selectedProject.stats.roles} · 场 {selectedProject.stats.scenes} · 道 {selectedProject.stats.props}
                  </div>
                  <Button
                    type="primary"
                    block
                    size="small"
                    icon={<EnterOutlined />}
                    onClick={() => navigate(`/projects/${selectedProject.id}`)}
                    className="text-[11px]"
                  >
                    进入章节工作台
                  </Button>
                  <Button
                    block
                    size="small"
                    icon={<DeploymentUnitOutlined />}
                    onClick={() => navigate(getProjectFilmCorePath(selectedProject.id))}
                    className="text-[11px]"
                  >
                    Film Core 状态
                  </Button>
                </div>
              ) : (
                <div className="text-gray-500 text-sm py-6 text-center">
                  将鼠标悬停在项目卡片上查看详情
                </div>
              )}
            </Card>
          </div>
        </Col>
      </Row>
      </div>

      <Modal
        title="创建 AI 漫剧"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={720}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateSubmit}
          initialValues={{
            creation_mode: 'text_to_drama',
            visual_style: projectStyleOptions.visualStyles[0]?.value ?? '动漫',
            style:
              projectStyleOptions.defaultStyleByVisual?.[projectStyleOptions.visualStyles[0]?.value ?? '动漫'] ??
              projectStyleOptions.stylesByVisual[projectStyleOptions.visualStyles[0]?.value ?? '动漫']?.[0]?.value ??
              '国漫',
            seed: Math.floor(Math.random() * 99999),
            unifyStyle: true,
            episode_count: 3,
            shots_per_episode: 6,
            default_video_ratio: defaultVideoRatio ?? '9:16',
            automation_mode: 'automatic',
            reference_harvest_enabled: true,
          }}
        >
          <Form.Item name="creation_mode" label="入口模式">
            <Segmented
              block
              options={[
                { label: '自动生成漫剧', value: 'text_to_drama' },
                { label: '空项目', value: 'blank' },
              ]}
            />
          </Form.Item>
          {creationMode === 'text_to_drama' ? (
            <>
              <Form.Item name="project_name" label="项目名称（选填）">
                <Input placeholder="留空则使用文本首句" />
              </Form.Item>
              <Form.Item
                name="source_text"
                label="一句话 / 梗概 / 小说正文"
                rules={[{ required: true, message: '请输入文字或上传小说文件' }]}
              >
                <Input.TextArea rows={8} placeholder="输入故事设定、人物关系、开端冲突或完整正文" />
              </Form.Item>
              <Upload beforeUpload={handleNovelFileBeforeUpload} showUploadList={false} accept=".txt,.md,text/plain,text/markdown">
                <Button icon={<UploadOutlined />}>上传小说文件</Button>
              </Upload>
            </>
          ) : (
            <>
              <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
                <Input placeholder="例如：现实都市爱情短剧" />
              </Form.Item>
              <Form.Item name="description" label="项目简介（选填）">
                <Input.TextArea rows={4} placeholder="项目简介与风格说明，建议 80–120 字" />
              </Form.Item>
            </>
          )}
          <ProjectVisualStyleAndStyleFields form={form} options={projectStyleOptions} />
          <Row gutter={12}>
            {creationMode === 'text_to_drama' ? (
              <>
                <Col xs={24} sm={8}>
                  <Form.Item name="episode_count" label="集数">
                    <InputNumber min={1} max={50} className="w-full" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item name="shots_per_episode" label="每集镜头">
                    <InputNumber min={1} max={30} className="w-full" />
                  </Form.Item>
                </Col>
              </>
            ) : (
              <Col xs={24} sm={8}>
                <Form.Item name="seed" label="全局种子值" tooltip="固定种子可确保整部短剧视觉调性一致">
                  <InputNumber min={0} className="w-full" />
                </Form.Item>
              </Col>
            )}
            <Col xs={24} sm={8}>
              <Form.Item name="default_video_ratio" label="默认视频比例">
                <Select allowClear options={videoRatioOptions} placeholder="未设置时由模型/供应商决定" />
              </Form.Item>
            </Col>
          </Row>
          {creationMode === 'text_to_drama' ? (
            <>
              <Form.Item name="automation_mode" label="流程开关">
                <Select
                  options={[
                    { label: '自动推进', value: 'automatic' },
                    { label: '人工停等', value: 'manual' },
                  ]}
                />
              </Form.Item>
              <Form.Item
                name="reference_harvest_enabled"
                label="创建角色网络参考采集任务"
                valuePropName="checked"
                tooltip="默认只创建候选 URL 与授权线索采集任务，不直接下载或商用外部素材"
              >
                <Switch />
              </Form.Item>
            </>
          ) : (
            <Form.Item
              name="unifyStyle"
              label="所有章节强制继承此风格"
              valuePropName="checked"
              tooltip="开启后所有章节继承项目风格"
            >
              <Switch />
            </Form.Item>
          )}
          <Form.Item className="mb-0">
            <Space>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={creatingProject}>
                {creationMode === 'text_to_drama' ? '创建并进入 Film Core' : '创建并进入章节'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑项目"
        open={editModalOpen}
        onCancel={() => { setEditModalOpen(false); setEditingProject(null) }}
        footer={null}
        width={520}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
          initialValues={{ style: '真人都市', visual_style: '现实', unifyStyle: true }}
        >
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="项目名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="项目简介与风格说明" />
          </Form.Item>
          <ProjectVisualStyleAndStyleFields form={editForm} options={projectStyleOptions} />
          <Form.Item name="seed" label="全局种子值" tooltip="固定种子可确保整部短剧视觉调性一致">
            <InputNumber min={0} className="w-full" />
          </Form.Item>
          <Form.Item name="default_video_ratio" label="默认视频比例">
            <Select allowClear placeholder="未设置时由模型/供应商决定" options={videoRatioOptions} />
          </Form.Item>
          <Form.Item name="unifyStyle" label="风格统一" valuePropName="checked" tooltip="开启后所有章节继承项目风格">
            <Switch />
          </Form.Item>
          <Form.Item className="mb-0">
            <Space>
              <Button onClick={() => { setEditModalOpen(false); setEditingProject(null) }}>取消</Button>
              <Button type="primary" htmlType="submit">保存</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProjectLobby
