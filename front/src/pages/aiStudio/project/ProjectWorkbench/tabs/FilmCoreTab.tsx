import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Tag,
  Timeline,
  Typography,
  message,
} from 'antd'
import {
  ApartmentOutlined,
  CheckCircleOutlined,
  ControlOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import {
  createIndustrialPlan,
  loadIndustrialOverview,
  type FilmIndustrialOverview,
  type FilmIndustrialPlan,
  type FilmPipelineStage,
} from '../../../../../services/industrialFilm'

const { Text } = Typography

const statusColor: Record<string, string> = {
  done: 'green',
  ready: 'blue',
  active: 'processing',
  warning: 'gold',
  waiting: 'default',
  blocked: 'red',
}

const statusLabel: Record<string, string> = {
  done: '已完成',
  ready: '可执行',
  active: '执行中',
  warning: '需补强',
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

export function FilmCoreTab() {
  const { projectId } = useParams<{ projectId: string }>()
  const [overview, setOverview] = useState<FilmIndustrialOverview | null>(null)
  const [plan, setPlan] = useState<FilmIndustrialPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [planning, setPlanning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const blockingActions = useMemo(
    () => overview?.operator_next_actions.filter((item) => item.severity === 'high') ?? [],
    [overview],
  )

  const refresh = async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await loadIndustrialOverview(projectId)
      setOverview(data)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Film Core 状态加载失败'
      setError(msg)
    } finally {
      setLoading(false)
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
            <Statistic title="流程节点" value={overview.pipeline.length} prefix={<ControlOutlined />} />
            <Text type="secondary">从剧本到最终剪辑</Text>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="生产闭环" size="small">
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
    </div>
  )
}
