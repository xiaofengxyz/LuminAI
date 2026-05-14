import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Input,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Tag,
  Timeline,
  Typography,
  message,
} from 'antd'
import {
  ApartmentOutlined,
  CheckCircleOutlined,
  ControlOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import {
  completeWorkflowStage,
  createIndustrialRun,
  createIndustrialPlan,
  editWorkflowState,
  loadIndustrialOverview,
  loadWorkflowState,
  regenerateWorkflowStage,
  type FilmIndustrialOverview,
  type FilmIndustrialPlan,
  type FilmIndustrialRun,
  type FilmImplementationPhase,
  type FilmPipelineStage,
  type FilmProductionModule,
  type FilmWorkflowState,
} from '../../../../../services/industrialFilm'

const { Text, Title, Paragraph } = Typography

const statusColor: Record<string, string> = {
  done: 'green',
  ready: 'blue',
  active: 'processing',
  warning: 'gold',
  waiting: 'default',
  waiting_operator: 'gold',
  needs_input: 'gold',
  blocked: 'red',
  completed: 'green',
}

const statusLabel: Record<string, string> = {
  done: '已完成',
  ready: '可执行',
  active: '执行中',
  warning: '需补强',
  waiting: '等待中',
  waiting_operator: '人工停等',
  needs_input: '需输入',
  blocked: '阻塞',
  completed: '已完成',
}

const moduleStatusLabel: Record<string, string> = {
  done: '已完成',
  active: '推进中',
  waiting: '等待中',
  blocked: '阻塞',
}

const severityColor: Record<string, string> = {
  high: 'red',
  medium: 'gold',
  low: 'green',
  normal: 'green',
}

function stageTag(status: string) {
  return <Tag color={statusColor[status] ?? 'default'}>{statusLabel[status] ?? status}</Tag>
}

function severityTag(severity: string) {
  return <Tag color={severityColor[severity] ?? 'default'}>{severity}</Tag>
}

function timelineColor(stage: FilmPipelineStage) {
  if (stage.status === 'done') return 'green'
  if (stage.status === 'blocked') return 'red'
  if (stage.status === 'warning') return 'orange'
  if (stage.status === 'active') return 'blue'
  return 'gray'
}

function phaseTag(phase: FilmImplementationPhase) {
  return <Tag color={phase.status === 'done' ? 'green' : 'gold'}>{phase.status === 'done' ? '已完成' : phase.status}</Tag>
}

/**
 * 将后端模块状态映射为 Ant Design 颜色，保持 Film Core 进度视图稳定。
 */
function moduleStatusTag(module: FilmProductionModule) {
  const color = module.status === 'done' ? 'green' : module.status === 'blocked' ? 'red' : module.status === 'active' ? 'processing' : 'default'
  return <Tag color={color}>{moduleStatusLabel[module.status] ?? module.status}</Tag>
}

/**
 * 根据模块 route_hint 给出项目内回跳地址，避免前端硬编码业务模块名称。
 */
function moduleRoute(projectId: string, module: FilmProductionModule) {
  if (module.route_hint.includes('tab=chapters')) return `/projects/${projectId}?tab=chapters`
  if (module.route_hint.includes('tab=roles')) return `/projects/${projectId}?tab=roles`
  if (module.route_hint.includes('tab=settings')) return `/projects/${projectId}?tab=settings`
  if (module.route_hint.includes('tab=edit')) return `/projects/${projectId}?tab=edit`
  return `/projects/${projectId}?tab=filmCore`
}

/**
 * 从工作流状态中读取角色网络参考采集候选，供 Film Core 以人工可审方式展示。
 */
function referenceHarvestItems(workflow: FilmWorkflowState | null): Array<Record<string, any>> {
  const items = workflow?.stage_data?.image_runtime?.reference_harvest?.items
  return Array.isArray(items) ? items.filter((item) => item && typeof item === 'object') : []
}

export function FilmCoreTab() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [overview, setOverview] = useState<FilmIndustrialOverview | null>(null)
  const [workflow, setWorkflow] = useState<FilmWorkflowState | null>(null)
  const [plan, setPlan] = useState<FilmIndustrialPlan | null>(null)
  const [run, setRun] = useState<FilmIndustrialRun | null>(null)
  const [selectedStageKey, setSelectedStageKey] = useState('novel_engine')
  const [workflowNote, setWorkflowNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [planning, setPlanning] = useState(false)
  const [running, setRunning] = useState(false)
  const [savingWorkflow, setSavingWorkflow] = useState(false)
  const [regeneratingWorkflow, setRegeneratingWorkflow] = useState(false)
  const [completingWorkflow, setCompletingWorkflow] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const blockingActions = useMemo(
    () => overview?.operator_next_actions.filter((item) => item.severity === 'high') ?? [],
    [overview],
  )
  const phasePercent = useMemo(() => {
    if (!overview?.implementation_status.total_phases) return 0
    return Math.round(
      (overview.implementation_status.completed_phases / overview.implementation_status.total_phases) * 100,
    )
  }, [overview])
  const selectedWorkflowStage = useMemo(
    () => workflow?.stages.find((stage) => stage.key === selectedStageKey) ?? workflow?.stages[0],
    [workflow, selectedStageKey],
  )
  const harvestItems = useMemo(() => referenceHarvestItems(workflow), [workflow])

  const refresh = async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const [overviewData, workflowData] = await Promise.all([
        loadIndustrialOverview(projectId),
        loadWorkflowState(projectId),
      ])
      setOverview(overviewData)
      setWorkflow(workflowData)
      if (workflowData.stages.length > 0 && !workflowData.stages.some((stage) => stage.key === selectedStageKey)) {
        setSelectedStageKey(workflowData.stages[0].key)
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Film Core 状态加载失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleWorkflowEdit = async () => {
    if (!projectId || !selectedWorkflowStage) return
    setSavingWorkflow(true)
    try {
      const note = workflowNote.trim() || 'operator stage edit'
      const data = await editWorkflowState(projectId, selectedWorkflowStage.key, {
        actor: 'studio_operator',
        note,
        patch: {
          operator_note: note,
          ui_saved_at: new Date().toISOString(),
        },
      })
      setWorkflow(data.workflow)
      message.success(`工作流阶段已保存到 v${data.workflow.version}`)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '工作流阶段保存失败'
      message.error(msg)
    } finally {
      setSavingWorkflow(false)
    }
  }

  const handleWorkflowModeChange = async (checked: boolean) => {
    if (!projectId || !selectedWorkflowStage) return
    const mode: 'automatic' | 'manual' = checked ? 'automatic' : 'manual'
    setSavingWorkflow(true)
    try {
      const data = await editWorkflowState(projectId, selectedWorkflowStage.key, {
        actor: 'studio_operator',
        note: `set ${selectedWorkflowStage.key} execution mode to ${mode}`,
        execution_mode: mode,
        auto_advance: checked,
        patch: {
          automation: {
            mode,
            auto_advance: checked,
            stop_after_stage: !checked,
          },
          ui_saved_at: new Date().toISOString(),
        },
      })
      setWorkflow(data.workflow)
      message.success(mode === 'automatic' ? '阶段已设为自动推进' : '阶段已设为人工停等')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '阶段开关保存失败'
      message.error(msg)
    } finally {
      setSavingWorkflow(false)
    }
  }

  const handleWorkflowComplete = async () => {
    if (!projectId || !selectedWorkflowStage) return
    setCompletingWorkflow(true)
    try {
      const data = await completeWorkflowStage(projectId, selectedWorkflowStage.key, {
        actor: 'studio_operator',
        execution_mode: selectedWorkflowStage.automation.mode,
        result: {
          operator_note: workflowNote.trim(),
          completed_from: 'film_core_ui',
        },
      })
      setWorkflow(data.workflow)
      message.success(
        selectedWorkflowStage.automation.mode === 'automatic'
          ? '阶段已完成并自动推进下一阶段'
          : '阶段已完成，已停等人工操作',
      )
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '阶段完成失败'
      message.error(msg)
    } finally {
      setCompletingWorkflow(false)
    }
  }

  const handleWorkflowRegenerate = async () => {
    if (!projectId || !selectedWorkflowStage) return
    setRegeneratingWorkflow(true)
    try {
      const reason = workflowNote.trim() || 'operator requested stage regeneration'
      const data = await regenerateWorkflowStage(projectId, selectedWorkflowStage.key, {
        actor: 'studio_operator',
        reason,
        provider: 'runtime_adapter',
        model: 'project_default_model',
        patch: {
          preserve_approved_outputs: true,
          target_stage: selectedWorkflowStage.key,
        },
      })
      setWorkflow(data.workflow)
      message.success(`已为 ${selectedWorkflowStage.title} 创建重生成任务`)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '工作流阶段重生成失败'
      message.error(msg)
    } finally {
      setRegeneratingWorkflow(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [projectId])

  const handlePlan = async () => {
    if (!projectId) return
    setPlanning(true)
    try {
      const data = await createIndustrialPlan(projectId, {
        provider: 'runtime_adapter',
        model: 'project_default_video_model',
      })
      setPlan(data)
      message.success('工业闭环计划已生成')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '工业闭环计划生成失败'
      message.error(msg)
    } finally {
      setPlanning(false)
    }
  }

  const handleRun = async () => {
    if (!projectId) return
    if (!overview?.shooting_gate.ready) {
      message.warning('拍摄前置门禁未通过，先补齐角色、资产和镜头细节')
      return
    }
    setRunning(true)
    try {
      const data = await createIndustrialRun(projectId, {
        provider: 'runtime_adapter',
        model: 'project_default_video_model',
        mode: 'queue_only',
      })
      setRun(data)
      message.success(`已创建 ${data.created_task_count} 个工业闭环任务`)
      await refresh()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '工业闭环任务创建失败'
      message.error(msg)
    } finally {
      setRunning(false)
    }
  }

  if (!projectId) {
    return <Empty description="项目不存在" />
  }

  if (loading && !overview) {
    return (
      <div className="flex justify-center items-center py-16">
        <Spin size="large" tip="加载 Film Core…" />
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="space-y-4">
        {error ? <Alert type="error" showIcon message={error} /> : null}
        <Button icon={<ReloadOutlined />} onClick={refresh}>
          刷新
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4 pb-6">
      {error ? <Alert type="warning" showIcon message={error} /> : null}

      <div>
        <Title level={4} className="!mb-1">
          Film Core Overview
        </Title>
        <Paragraph type="secondary" className="!mb-0">
          这里是项目级工业电影核心：九阶段落地证据、11 节点生产流水线、一致性健康、痛点诊断、计划预览和任务写回入口。
        </Paragraph>
        <Text type="secondary" className="text-xs">
          入口路径：项目列表 Film Core / 项目速览 Film Core 状态 / 项目工作台顶部 Film Core / `/projects/{projectId}?tab=filmCore`
        </Text>
      </div>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <Space wrap>
          <Tag color="blue" icon={<ApartmentOutlined />}>
            {overview.workflow_mode}
          </Tag>
          <Tag color={overview.asset_health.summary === 'ready' ? 'green' : 'gold'}>
            资产状态 {overview.asset_health.summary}
          </Tag>
          <Tag color={overview.qa_retry.risk_level === 'high' ? 'red' : 'green'}>
            QA 风险 {overview.qa_retry.risk_level}
          </Tag>
        </Space>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={refresh} loading={loading}>
            刷新
          </Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={handlePlan} loading={planning}>
            生成闭环计划
          </Button>
          <Button
            icon={<ControlOutlined />}
            onClick={handleRun}
            loading={running}
            disabled={!overview.shooting_gate.ready}
          >
            创建生产任务
          </Button>
        </Space>
      </div>

      {blockingActions.length > 0 ? (
        <Alert
          type="error"
          showIcon
          message="工业闭环存在阻塞项"
          description={blockingActions.map((item) => item.action).join(' / ')}
        />
      ) : (
        <Alert type="success" showIcon message="项目已具备进入批量生产闭环的基础条件" />
      )}

      <Card
        title="拍摄前置门禁"
        size="small"
        extra={<Tag color={overview.shooting_gate.ready ? 'green' : 'red'}>{overview.shooting_gate.state}</Tag>}
      >
        <Alert
          type={overview.shooting_gate.ready ? 'success' : 'warning'}
          showIcon
          message={overview.shooting_gate.message}
        />
        {overview.shooting_gate.blockers.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {overview.shooting_gate.blockers.map((item) => (
              <Tag key={item} color="red">
                {item}
              </Tag>
            ))}
          </div>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {overview.shooting_gate.required_before_shooting.map((item) => (
            <Tag key={item}>{item}</Tag>
          ))}
        </div>
        <Divider className="!my-3" />
        <Text type="secondary" className="text-xs">
          可用运行时：{overview.shooting_gate.allowed_runtime_models.join(' / ')}
        </Text>
      </Card>

      <Card title="AI漫剧生产进度" size="small">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {overview.production_modules.map((module) => (
            <div key={module.key} className="rounded border border-gray-100 bg-gray-50 px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-gray-900">{module.title}</span>
                {moduleStatusTag(module)}
              </div>
              <Progress percent={module.progress} size="small" className="mt-2" />
              <div className="mt-1 text-xs text-gray-600">{module.summary}</div>
              <div className="mt-2 flex flex-wrap gap-1">
                {module.tasks.slice(0, 4).map((item) => (
                  <Tag key={item} className="mr-0 text-[11px]">
                    {item}
                  </Tag>
                ))}
              </div>
              {module.blockers.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-1">
                  {module.blockers.map((item) => (
                    <Tag key={item} color="red" className="mr-0 text-[11px]">
                      {item}
                    </Tag>
                  ))}
                </div>
              ) : null}
              <div className="mt-2 flex items-center justify-between gap-2">
                <Text type="secondary" className="text-xs">
                  {module.next_action}
                </Text>
                <Button
                  size="small"
                  type="link"
                  icon={<LinkOutlined />}
                  disabled={!module.can_return}
                  onClick={() => projectId && navigate(moduleRoute(projectId, module))}
                >
                  返回修改
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {harvestItems.length > 0 ? (
        <Card title="角色网络参考采集" size="small">
          <Row gutter={[12, 12]}>
            {harvestItems.slice(0, 6).map((item) => {
              const characterName = String(item.character_name ?? item.character_key ?? '角色')
              const imageUrls = Array.isArray(item.image_search_urls) ? item.image_search_urls : []
              const videoUrls = Array.isArray(item.video_search_urls) ? item.video_search_urls : []
              return (
                <Col xs={24} md={12} xl={8} key={String(item.character_key ?? characterName)}>
                  <div className="h-full rounded border border-gray-100 bg-gray-50 px-3 py-2">
                    <div className="font-medium text-gray-900">{characterName}</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {imageUrls.slice(0, 2).map((url: string, index: number) => (
                        <a key={`image-${url}`} href={url} target="_blank" rel="noreferrer">
                          图片候选 {index + 1}
                        </a>
                      ))}
                      {videoUrls.slice(0, 2).map((url: string, index: number) => (
                        <a key={`video-${url}`} href={url} target="_blank" rel="noreferrer">
                          视频候选 {index + 1}
                        </a>
                      ))}
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      {Array.isArray(item.image_queries) ? item.image_queries[0] : ''}
                    </div>
                  </div>
                </Col>
              )
            })}
          </Row>
          <div className="mt-3 text-xs text-gray-500">
            参考采集只保存候选搜索入口与授权核查线索，实际下载和商用使用需要后续 worker 或人工确认版权。
          </div>
        </Card>
      ) : null}

      <Card title="统一入口职责" size="small">
        <Row gutter={[12, 12]}>
          {overview.creation_entries.map((entry) => (
            <Col xs={24} md={12} key={entry.key}>
              <div className="h-full rounded border border-gray-100 bg-gray-50 px-3 py-2">
                <div className="font-medium text-gray-900">{entry.title}</div>
                <div className="mt-1 text-xs text-gray-600">{entry.purpose}</div>
                <div className="mt-2 text-xs text-gray-500">{entry.when_to_use}</div>
                <div className="mt-2 rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600">
                  {entry.output}
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic title="工业化分数" value={overview.industrial_score} suffix="%" prefix={<CheckCircleOutlined />} />
            <Progress percent={overview.industrial_score} showInfo={false} size="small" className="mt-2" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic title="可 QA 视频" value={overview.qa_retry.generated_or_accepted_videos} />
            <Text type="secondary">自动重试候选 {overview.qa_retry.planned_retry_candidates}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic title="待确认资产" value={overview.asset_health.pending_candidate_count} prefix={<WarningOutlined />} />
            <Text type="secondary">对白候选 {overview.asset_health.pending_dialogue_count}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="九阶段完成"
              value={overview.implementation_status.completed_phases}
              suffix={`/ ${overview.implementation_status.total_phases}`}
              prefix={<ControlOutlined />}
            />
            <Text type="secondary">{overview.implementation_status.status === 'complete' ? '已全部落地' : '继续推进中'}</Text>
          </Card>
        </Col>
      </Row>

      <Card
        title="九阶段交付状态"
        size="small"
        extra={<Tag color={overview.implementation_status.status === 'complete' ? 'green' : 'gold'}>{overview.implementation_status.label}</Tag>}
      >
        <div className="mb-3">
          <Progress percent={phasePercent} size="small" />
          <Text type="secondary">{overview.implementation_status.evidence}</Text>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {overview.implementation_phases.map((phase) => (
            <div key={phase.key} className="rounded border border-gray-100 bg-gray-50 px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <Space size="small" wrap>
                  <span className="text-xs font-medium text-gray-500">{phase.phase}</span>
                  {phaseTag(phase)}
                </Space>
                <Text type="secondary" className="text-xs">
                  {phase.owner}
                </Text>
              </div>
              <div className="mt-1 font-medium text-gray-900">{phase.title}</div>
              <div className="mt-1 text-xs text-gray-600">{phase.evidence}</div>
              <div className="mt-1 text-xs text-gray-500">{phase.surface}</div>
            </div>
          ))}
        </div>
      </Card>

      {workflow ? (
        <Card
          title="CineForge 可编辑工作流状态"
          size="small"
          extra={<Tag color="blue">{workflow.workflow_key} · v{workflow.version}</Tag>}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={10}>
              <Space direction="vertical" className="w-full" size="middle">
                <Select
                  className="w-full"
                  value={selectedWorkflowStage?.key}
                  onChange={setSelectedStageKey}
                  options={workflow.stages.map((stage) => ({
                    value: stage.key,
                    label: `${stage.title} · ${stage.status.state ?? 'unknown'}`,
                  }))}
                />
                <div className="flex items-center justify-between gap-3 rounded border border-gray-100 bg-gray-50 px-3 py-2">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-800">阶段推进开关</div>
                    <div className="text-xs text-gray-500">
                      {selectedWorkflowStage?.automation.mode === 'automatic'
                        ? '完成后自动进入下一阶段'
                        : '完成后停等人工审核或修改'}
                    </div>
                  </div>
                  <Switch
                    checked={selectedWorkflowStage?.automation.mode === 'automatic'}
                    checkedChildren="自动"
                    unCheckedChildren="人工"
                    loading={savingWorkflow}
                    onChange={handleWorkflowModeChange}
                  />
                </div>
                <Input.TextArea
                  rows={4}
                  value={workflowNote}
                  onChange={(event) => setWorkflowNote(event.target.value)}
                  placeholder="记录本次阶段编辑或重生成原因"
                />
                <Space wrap>
                  <Button
                    type="primary"
                    onClick={handleWorkflowEdit}
                    loading={savingWorkflow}
                    disabled={!selectedWorkflowStage?.editable}
                  >
                    保存阶段编辑
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={handleWorkflowRegenerate}
                    loading={regeneratingWorkflow}
                    disabled={!selectedWorkflowStage?.regeneratable}
                  >
                    重生成阶段
                  </Button>
                  <Button
                    icon={<CheckCircleOutlined />}
                    onClick={handleWorkflowComplete}
                    loading={completingWorkflow}
                  >
                    完成并推进
                  </Button>
                </Space>
                <Text type="secondary" className="text-xs">
                  最近任务：{workflow.last_task_id ?? '暂无'} · 编辑 {workflow.edit_log.length} 次 · 重生成 {workflow.regenerate_log.length} 次
                </Text>
              </Space>
            </Col>
            <Col xs={24} lg={14}>
              {selectedWorkflowStage ? (
                <div>
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <Space wrap>
                      <span className="font-medium">{selectedWorkflowStage.title}</span>
                      <Tag>{selectedWorkflowStage.owner}</Tag>
                      <Tag color="purple">{selectedWorkflowStage.qa_gate}</Tag>
                    </Space>
                    {stageTag(String(selectedWorkflowStage.status.state ?? 'waiting'))}
                  </div>
                  <Divider className="!my-3" />
                  <pre className="max-h-72 overflow-auto rounded border border-gray-100 bg-gray-50 p-3 text-xs text-gray-700">
                    {JSON.stringify(selectedWorkflowStage.data, null, 2)}
                  </pre>
                </div>
              ) : (
                <Empty description="暂无工作流阶段" />
              )}
            </Col>
          </Row>
        </Card>
      ) : null}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title={`生产闭环 · ${overview.pipeline.length} 个运行节点`} size="small">
            <Timeline
              items={overview.pipeline.map((stage) => ({
                color: timelineColor(stage),
                children: (
                  <div className="pb-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <Space size="small" wrap>
                        <span className="font-medium">{stage.title}</span>
                        {stageTag(stage.status)}
                      </Space>
                      <Text type="secondary">{stage.owner}</Text>
                    </div>
                    <div className="mt-1 text-sm text-gray-600">{stage.description}</div>
                    <div className="mt-1 text-xs text-gray-500">{stage.evidence}</div>
                    <div className="mt-1 text-xs text-gray-700">{stage.next_action}</div>
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card title="一致性健康" size="small">
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm">
                  <span>角色身份</span>
                  <span>{overview.asset_health.identity_score}%</span>
                </div>
                <Progress percent={overview.asset_health.identity_score} size="small" showInfo={false} />
              </div>
              <div>
                <div className="flex justify-between text-sm">
                  <span>场景连续</span>
                  <span>{overview.asset_health.scene_score}%</span>
                </div>
                <Progress percent={overview.asset_health.scene_score} size="small" showInfo={false} />
              </div>
              <div>
                <div className="flex justify-between text-sm">
                  <span>道具绑定</span>
                  <span>{overview.asset_health.prop_score}%</span>
                </div>
                <Progress percent={overview.asset_health.prop_score} size="small" showInfo={false} />
              </div>
              <div>
                <div className="flex justify-between text-sm">
                  <span>服装锁定</span>
                  <span>{overview.asset_health.costume_score}%</span>
                </div>
                <Progress percent={overview.asset_health.costume_score} size="small" showInfo={false} />
              </div>
            </div>
          </Card>

          <Card title="痛点诊断" size="small" className="mt-4">
            <div className="space-y-3">
              {overview.pain_points.map((item) => (
                <div key={item.key} className="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{item.title}</span>
                    {severityTag(item.severity)}
                  </div>
                  <div className="mt-1 text-xs text-gray-500">{item.diagnosis}</div>
                  <div className="mt-1 text-sm text-gray-700">{item.solution}</div>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {plan ? (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title={`闭环计划 ${plan.plan_id}`} size="small">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <div className="text-xs text-gray-500">渲染队列</div>
                  <div className="text-xl font-semibold">{plan.render_queue.length}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">重试候选</div>
                  <div className="text-xl font-semibold">{plan.retry_policy.planned_retry_candidates}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">后期</div>
                  <div className="text-xl font-semibold">{plan.post_production.enabled ? 'Ready' : 'Waiting'}</div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {plan.qa_policy.continuity_checks.map((item) => (
                  <Tag key={item}>{item}</Tag>
                ))}
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="参考项目拆解" size="small">
              <div className="space-y-2">
                {overview.reference_projects.slice(0, 4).map((item) => (
                  <div key={item.name} className="flex items-start justify-between gap-3 border-b border-gray-100 pb-2 last:border-b-0">
                    <div>
                      <a href={item.url} target="_blank" rel="noreferrer" className="font-medium">
                        {item.name}
                      </a>
                      <div className="text-xs text-gray-500">{item.adopted_layer}</div>
                    </div>
                    <Text type="secondary" className="max-w-60 text-right">
                      {item.rule}
                    </Text>
                  </div>
                ))}
              </div>
            </Card>
          </Col>
        </Row>
      ) : null}

      {run ? (
        <Card
          title={`任务写回 · ${run.run_id}`}
          size="small"
          extra={<Tag color="blue">{run.mode}</Tag>}
        >
          <Row gutter={[12, 12]}>
            <Col xs={12} sm={6}>
              <Statistic title="总任务" value={run.created_task_count} />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic title="渲染" value={run.render_task_count} />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic title="QA" value={run.qa_task_count} />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic title="重试/后期" value={run.retry_task_count + run.post_task_count} />
            </Col>
          </Row>
          <div className="mt-3 flex flex-wrap gap-2">
            {run.tasks.slice(0, 8).map((item) => (
              <Tag key={item.task_id} color={item.status === 'succeeded' ? 'green' : 'processing'}>
                {item.task_kind} · {item.relation_entity_id}
              </Tag>
            ))}
          </div>
          <div className="mt-3 text-xs text-gray-500">
            已写入 Jellyfish generation_tasks 与 generation_task_links；真实供应商 worker 完成后会继续回填文件与镜头视频关系。
          </div>
        </Card>
      ) : null}
    </div>
  )
}
