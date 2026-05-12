from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus


@dataclass(frozen=True)
class CharacterSeed:
    key: str
    name: str
    description: str
    costume: str
    traits: list[str]
    image_queries: list[str]
    video_queries: list[str]


@dataclass(frozen=True)
class SceneSeed:
    key: str
    name: str
    description: str


@dataclass(frozen=True)
class PropSeed:
    key: str
    name: str
    description: str
    owner_character_key: str | None = None


@dataclass(frozen=True)
class ShotSeed:
    key: str
    title: str
    script_excerpt: str
    storyboard: str
    camera_shot: str
    camera_angle: str
    camera_movement: str
    duration: int
    scene_key: str
    character_keys: list[str]
    prop_keys: list[str]
    vfx_type: str
    vfx_note: str
    sfx: list[str]
    dialogue: list[dict[str, str]]


@dataclass(frozen=True)
class EpisodeSeed:
    index: int
    title: str
    summary: str
    novel_text: str
    script_outline: list[str]
    cliffhanger: str
    shots: list[ShotSeed]


@dataclass(frozen=True)
class TextToDramaBlueprint:
    project_name: str
    source_text: str
    series_logline: str
    world_bible: dict[str, object]
    relationship_graph: dict[str, object]
    characters: list[CharacterSeed]
    scenes: list[SceneSeed]
    props: list[PropSeed]
    vfx_notes: list[str]
    episodes: list[EpisodeSeed]
    reference_harvest: dict[str, object] = field(default_factory=dict)

    @property
    def generated_novel_text(self) -> str:
        return "\n\n".join(episode.novel_text for episode in self.episodes)


def build_text_to_drama_blueprint(
    *,
    source_text: str,
    project_name: str,
    episode_count: int,
    shots_per_episode: int,
    style: str,
    visual_style: str,
    reference_harvest_enabled: bool = True,
) -> TextToDramaBlueprint:
    """Build a deterministic AI manju production blueprint from one text input.

    This is deliberately provider-neutral: it creates recoverable story and asset
    state now, while a later LLM worker can replace the heuristic compiler behind
    the same schema.
    """

    normalized = _compact(source_text)
    sentences = _sentences(normalized)
    characters = _character_seeds(normalized, project_name)
    scenes = _scene_seeds(normalized, project_name)
    props = _prop_seeds(normalized, characters)
    vfx_notes = _vfx_notes(normalized)
    episodes = _episode_seeds(
        source_text=normalized,
        sentences=sentences,
        episode_count=episode_count,
        shots_per_episode=shots_per_episode,
        characters=characters,
        scenes=scenes,
        props=props,
        vfx_notes=vfx_notes,
    )
    world_bible = {
        "title": project_name,
        "style": style,
        "visual_style": visual_style,
        "source_premise": normalized[:800],
        "tone": _tone_from_text(normalized),
        "continuity_rules": [
            "角色身份、服装、核心道具和场景光线在跨集生产中保持稳定",
            "每集只推进一个核心悬念，上一集结尾必须在下一集开场回应",
            "所有图片/视频提示词必须从资产圣经和分镜状态编译，不手写散乱 prompt",
        ],
    }
    relationship_graph = {
        "nodes": [{"key": item.key, "name": item.name, "traits": item.traits} for item in characters],
        "edges": _relationship_edges(characters),
    }
    reference_harvest = _reference_harvest_plan(
        characters=characters,
        project_name=project_name,
        enabled=reference_harvest_enabled,
    )

    return TextToDramaBlueprint(
        project_name=project_name,
        source_text=normalized,
        series_logline=_series_logline(normalized, characters),
        world_bible=world_bible,
        relationship_graph=relationship_graph,
        characters=characters,
        scenes=scenes,
        props=props,
        vfx_notes=vfx_notes,
        episodes=episodes,
        reference_harvest=reference_harvest,
    )


def _compact(text: str) -> str:
    return " ".join(text.strip().split())


def _sentences(text: str) -> list[str]:
    separators = "。！？!?；;\n"
    result: list[str] = []
    current: list[str] = []
    for char in text:
        current.append(char)
        if char in separators:
            sentence = _compact("".join(current).strip("。！？!?；;"))
            if sentence:
                result.append(sentence)
            current = []
    tail = _compact("".join(current))
    if tail:
        result.append(tail)
    return result or [text or "一个角色被卷入新的命运事件"]


def _character_seeds(text: str, project_name: str) -> list[CharacterSeed]:
    candidates = _ordered_unique(_extract_named_roles(text))
    if not candidates:
        candidates = [_fallback_protagonist(text)]
    while len(candidates) < 3:
        candidates.append(["关键伙伴", "主要对手", "线索守护者"][len(candidates) - 1])

    seeds: list[CharacterSeed] = []
    for index, name in enumerate(candidates[:4], start=1):
        role = "主角" if index == 1 else ("对手" if index == 3 else "支线角色")
        costume = _costume_for(text, name, role)
        description = f"{name}是《{project_name}》的{role}，围绕核心事件承担明确动机和视觉识别点。"
        traits = ["行动主动", "情绪可见"] if index == 1 else ["关系明确", "用于推动冲突"]
        seeds.append(
            CharacterSeed(
                key=f"char_{index:03d}",
                name=name,
                description=description,
                costume=costume,
                traits=traits,
                image_queries=_reference_queries(project_name, name, costume, "character portrait reference"),
                video_queries=_reference_queries(project_name, name, costume, "cinematic motion reference"),
            )
        )
    return seeds


def _extract_named_roles(text: str) -> list[str]:
    role_words = [
        "少女",
        "少年",
        "女人",
        "男人",
        "警探",
        "医生",
        "学生",
        "老师",
        "父亲",
        "母亲",
        "姐姐",
        "哥哥",
        "妹妹",
        "弟弟",
        "主角",
        "导演",
        "老板",
        "刺客",
        "公主",
        "将军",
        "守护者",
        "追踪者",
    ]
    found = [word for word in role_words if word in text]
    # A tiny rule-based extractor catches names or role labels before common verbs.
    verbs = ("在", "发现", "拿", "带", "追", "对", "说", "看", "穿", "戴", "进入", "来到", "守护", "翻开", "寻找")
    for verb in verbs:
        parts = text.split(verb)
        if len(parts) < 2:
            continue
        prefix = parts[0][-6:].strip(" ，,。！？!?")
        if 1 <= len(prefix) <= 6 and not any(mark in prefix for mark in "的了和与每就"):
            found.append(prefix)
    return [name for name in found if name not in {"剧本", "城市", "雨夜", "记忆"}]


def _fallback_protagonist(text: str) -> str:
    if "古" in text or "宫" in text:
        return "年轻侠客"
    if "科幻" in text or "AI" in text or "机器人" in text:
        return "年轻工程师"
    return "年轻主角"


def _costume_for(text: str, name: str, role: str) -> str:
    if any(word in text for word in ("雨", "夜", "巷")):
        return f"{name}穿深色防水外套，带一处可重复识别的微光配饰"
    if any(word in text for word in ("古", "宫", "剑")):
        return f"{name}穿层次清晰的古装长衣，腰间保留固定纹样"
    if role == "对手":
        return f"{name}穿剪裁硬朗的暗色服装，轮廓与主角明显区分"
    return f"{name}穿项目统一风格服装，保留固定色块和标志性配饰"


def _scene_seeds(text: str, project_name: str) -> list[SceneSeed]:
    candidates: list[tuple[str, str]] = []
    if any(word in text for word in ("雨", "夜", "巷", "街", "城市")):
        candidates.append(("雨夜城市街巷", "潮湿反光的城市街巷，霓虹和雨幕强化悬疑感"))
    if any(word in text for word in ("学校", "教室", "学生")):
        candidates.append(("学校走廊", "长走廊与教室门口形成可重复使用的校园空间"))
    if any(word in text for word in ("公司", "办公室", "老板")):
        candidates.append(("办公室", "带玻璃隔断和冷色灯光的现代办公室"))
    if any(word in text for word in ("森林", "山", "村")):
        candidates.append(("野外密林", "层次丰富的树影与雾气形成冒险空间"))
    if any(word in text for word in ("宫", "古", "剑")):
        candidates.append(("古城内院", "高墙、石阶和灯笼构成古装主场景"))
    if not candidates:
        candidates.append((f"{project_name}核心场景", "围绕故事核心冲突设计的主场景，可承接多集拍摄"))
    candidates.append((f"{project_name}转折空间", "用于反转、追逐或揭示真相的可复用空间"))
    return [
        SceneSeed(key=f"scene_{index:03d}", name=name, description=description)
        for index, (name, description) in enumerate(_ordered_unique_pairs(candidates)[:3], start=1)
    ]


def _prop_seeds(text: str, characters: list[CharacterSeed]) -> list[PropSeed]:
    prop_map = [
        ("剧本", "发光剧本", "会发光并改写记忆的核心线索物"),
        ("信封", "缺失信封", "承载秘密交易信息的纸质信封"),
        ("钥匙", "旧钥匙", "能打开关键场景的旧钥匙"),
        ("项链", "标志项链", "用于锁定角色身份的随身饰品"),
        ("手机", "加密手机", "保存线索和倒计时提醒的电子道具"),
        ("剑", "旧剑", "古装动作线的核心武器"),
    ]
    owner = characters[0].key if characters else None
    props = [PropSeed(key=f"prop_{index:03d}", name=name, description=desc, owner_character_key=owner) for index, (token, name, desc) in enumerate(prop_map, start=1) if token in text]
    if not props:
        props.append(
            PropSeed(
                key="prop_001",
                name="核心线索物",
                description="由原始创意扩展出的关键道具，用于串联多集悬念",
                owner_character_key=owner,
            )
        )
    return props[:4]


def _vfx_notes(text: str) -> list[str]:
    notes: list[str] = []
    if any(word in text for word in ("光", "发光", "能量", "魔")):
        notes.append("能量微光沿核心道具扩散，强度随剧情转折增强")
    if any(word in text for word in ("记忆", "时间", "改写", "循环")):
        notes.append("记忆/时间变化用慢动作、画面残影和局部粒子表现")
    if any(word in text for word in ("雨", "雾", "夜")):
        notes.append("雨雾体积光用于保持悬疑氛围和场景连续性")
    return notes or ["不额外堆叠视效，优先保持角色表演和镜头连续性"]


def _episode_seeds(
    *,
    source_text: str,
    sentences: list[str],
    episode_count: int,
    shots_per_episode: int,
    characters: list[CharacterSeed],
    scenes: list[SceneSeed],
    props: list[PropSeed],
    vfx_notes: list[str],
) -> list[EpisodeSeed]:
    arcs = ["引爆事件", "代价升级", "关系反转", "真相逼近", "终局选择"]
    episodes: list[EpisodeSeed] = []
    groups = _group_sentences(sentences, episode_count)
    for episode_index in range(1, episode_count + 1):
        arc = arcs[min(episode_index - 1, len(arcs) - 1)]
        segment = groups[episode_index - 1]
        premise = _compact("。".join(segment)) or source_text
        title = f"第{episode_index}集 · {arc}"
        cliffhanger = _cliffhanger(episode_index, episode_count, characters, props)
        script_outline = _script_outline(premise, characters, props, cliffhanger)
        shots = _shot_seeds(
            episode_index=episode_index,
            shots_per_episode=shots_per_episode,
            premise=premise,
            characters=characters,
            scenes=scenes,
            props=props,
            vfx_notes=vfx_notes,
            cliffhanger=cliffhanger,
        )
        novel_text = _novel_text(title, premise, characters, scenes, props, cliffhanger)
        episodes.append(
            EpisodeSeed(
                index=episode_index,
                title=title,
                summary=_compact(f"{premise}。{cliffhanger}")[:220],
                novel_text=novel_text,
                script_outline=script_outline,
                cliffhanger=cliffhanger,
                shots=shots,
            )
        )
    return episodes


def _shot_seeds(
    *,
    episode_index: int,
    shots_per_episode: int,
    premise: str,
    characters: list[CharacterSeed],
    scenes: list[SceneSeed],
    props: list[PropSeed],
    vfx_notes: list[str],
    cliffhanger: str,
) -> list[ShotSeed]:
    shot_roles = ["建立场景", "发现异常", "角色行动", "冲突升级", "线索揭示", "悬念收束"]
    camera_shots = ["LS", "MS", "MCU", "MS", "CU", "MLS"]
    movements = ["STATIC", "DOLLY_IN", "TRACK", "PAN", "DOLLY_IN", "HANDHELD"]
    shots: list[ShotSeed] = []
    for shot_index in range(1, shots_per_episode + 1):
        role = shot_roles[(shot_index - 1) % len(shot_roles)]
        scene = scenes[(shot_index - 1) % len(scenes)]
        prop = props[(shot_index - 1) % len(props)]
        lead = characters[0]
        support = characters[min(shot_index % len(characters), len(characters) - 1)]
        is_final = shot_index == shots_per_episode
        script = cliffhanger if is_final else f"{role}：{premise[:120]}"
        dialogue = [
            {
                "speaker_key": lead.key,
                "speaker_name": lead.name,
                "text": f"我们必须在下一次变化前弄清{prop.name}的真相。",
            }
        ]
        shots.append(
            ShotSeed(
                key=f"ep{episode_index:02d}_shot_{shot_index:03d}",
                title=f"{role} {shot_index:03d}",
                script_excerpt=script,
                storyboard=f"{scene.name}中，{lead.name}围绕{prop.name}推进动作；画面重点是{role}和角色情绪变化。",
                camera_shot=camera_shots[(shot_index - 1) % len(camera_shots)],
                camera_angle="EYE_LEVEL" if shot_index % 4 else "LOW_ANGLE",
                camera_movement=movements[(shot_index - 1) % len(movements)],
                duration=5 + (shot_index % 3),
                scene_key=scene.key,
                character_keys=_ordered_unique([lead.key, support.key]),
                prop_keys=[prop.key],
                vfx_type=_vfx_type(vfx_notes),
                vfx_note=vfx_notes[(shot_index - 1) % len(vfx_notes)],
                sfx=["环境底噪", "脚步声"] if shot_index % 2 else ["环境底噪", "低频转场"],
                dialogue=dialogue,
            )
        )
    return shots


def _novel_text(
    title: str,
    premise: str,
    characters: list[CharacterSeed],
    scenes: list[SceneSeed],
    props: list[PropSeed],
    cliffhanger: str,
) -> str:
    lead = characters[0]
    support = characters[1] if len(characters) > 1 else characters[0]
    antagonist = characters[2] if len(characters) > 2 else support
    scene = scenes[0]
    prop = props[0]
    return (
        f"{title}\n"
        f"{scene.name}被一种不安的节奏笼罩，{lead.name}带着{lead.costume}出现在故事中心。"
        f"原始事件是：{premise}。\n"
        f"{support.name}试图帮助{lead.name}确认{prop.name}的来源，但{antagonist.name}已经提前布下阻力。"
        f"镜头需要反复确认{lead.name}的服装、道具和行动目标，避免跨集身份漂移。\n"
        f"本集结尾，{cliffhanger}"
    )


def _script_outline(
    premise: str,
    characters: list[CharacterSeed],
    props: list[PropSeed],
    cliffhanger: str,
) -> list[str]:
    lead = characters[0].name
    prop = props[0].name
    return [
        f"{lead}在开场确认核心异常：{premise[:80]}",
        f"{lead}围绕{prop}采取第一次主动行动",
        "支线角色提供信息，但同时制造新的误解或阻力",
        f"结尾悬念：{cliffhanger}",
    ]


def _reference_harvest_plan(
    *,
    characters: list[CharacterSeed],
    project_name: str,
    enabled: bool,
) -> dict[str, object]:
    items = []
    for character in characters:
        image_queries = character.image_queries
        video_queries = character.video_queries
        items.append(
            {
                "character_key": character.key,
                "character_name": character.name,
                "image_queries": image_queries,
                "video_queries": video_queries,
                "image_search_urls": [_search_url(query, "image") for query in image_queries],
                "video_search_urls": [_search_url(query, "video") for query in video_queries],
            }
        )
    return {
        "enabled": enabled,
        "mode": "web_metadata_queue",
        "project": project_name,
        "policy": "只采集候选 URL、来源和授权线索；下载/商用使用必须由后续 worker 校验版权和授权。",
        "items": items,
    }


def _reference_queries(project_name: str, character_name: str, costume: str, suffix: str) -> list[str]:
    return [
        f"{project_name} {character_name} {costume} {suffix}",
        f"{character_name} {costume} anime drama {suffix}",
    ]


def _search_url(query: str, media_type: str) -> str:
    tbm = "isch" if media_type == "image" else "vid"
    return f"https://www.google.com/search?tbm={tbm}&q={quote_plus(query)}"


def _group_sentences(sentences: list[str], episode_count: int) -> list[list[str]]:
    groups = [[] for _ in range(episode_count)]
    for index, sentence in enumerate(sentences):
        groups[index % episode_count].append(sentence)
    return [group or [sentences[index % len(sentences)]] for index, group in enumerate(groups)]


def _cliffhanger(
    episode_index: int,
    episode_count: int,
    characters: list[CharacterSeed],
    props: list[PropSeed],
) -> str:
    lead = characters[0].name
    prop = props[0].name
    if episode_index >= episode_count:
        return f"{lead}终于理解{prop}的真正代价，但必须在救人与保留真相之间做出选择。"
    return f"{prop}出现新的变化，{lead}发现下一集的危机已经被提前写下。"


def _series_logline(text: str, characters: list[CharacterSeed]) -> str:
    lead = characters[0].name if characters else "主角"
    return f"{lead}被卷入由“{text[:48]}”引发的连续危机，必须在每集结尾破解新的悬念。"


def _relationship_edges(characters: list[CharacterSeed]) -> list[dict[str, str]]:
    if len(characters) < 2:
        return []
    edges = [{"from": characters[0].key, "to": characters[1].key, "relation": "互补/协作"}]
    if len(characters) > 2:
        edges.append({"from": characters[0].key, "to": characters[2].key, "relation": "目标冲突"})
    return edges


def _tone_from_text(text: str) -> str:
    if any(word in text for word in ("雨", "夜", "秘密", "记忆")):
        return "悬疑、情绪化、强连续性"
    if any(word in text for word in ("笑", "喜剧", "误会")):
        return "轻喜剧、快节奏、反转密集"
    return "剧情向、强冲突、短剧节奏"


def _vfx_type(vfx_notes: list[str]) -> str:
    joined = " ".join(vfx_notes)
    if any(word in joined for word in ("能量", "魔法", "微光")):
        return "ENERGY_MAGIC"
    if any(word in joined for word in ("雨雾", "体积光", "雾")):
        return "VOLUMETRIC_FOG"
    if any(word in joined for word in ("慢动作", "时间")):
        return "SLOW_MOTION_TIME"
    return "NONE"


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _ordered_unique_pairs(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for name, description in values:
        if name not in seen:
            seen.add(name)
            result.append((name, description))
    return result
