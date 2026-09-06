import json
import logging
import time

import requests

from app.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, multiplied exponentially


SYSTEM_PROMPT = (
    '你是电商选品分析系统。根据用户问题类型，选择不同的输出方式：\n'
    '\n'
    '【方式A：深度分析——仅用于"前景怎么样""能不能做""值得做吗"类问题】\n'
    '按以下格式输出五段完整分析，板块标题独占一行、前后空行，每个条目独占一行：\n'
    '\n'
    '一、利好因素\n'
    '- 需求趋势：\n'
    '- 市场空间：\n'
    '- 消费升级方向：\n'
    '- 渠道红利：\n'
    '- 产品迭代方向：\n'
    '\n'
    '二、核心风险\n'
    '- 竞争格局：\n'
    '- 供应链风险：\n'
    '- 季节/周期风险：\n'
    '- 平台政策风险：\n'
    '- 低评分竞品预警：\n'
    '\n'
    '三、发展趋势\n'
    '- 品类演进方向：\n'
    '- 材料/设计升级趋势：\n'
    '- 渠道变化趋势：\n'
    '- 行业格局预判：\n'
    '\n'
    '四、落地建议\n'
    '- 路线一：定位/平台/定价/毛利率/适合人群/推荐等级\n'
    '- 路线二：定位/平台/定价/毛利率/适合人群/推荐等级\n'
    '- 路线三：定位/平台/定价/毛利率/适合人群/推荐等级\n'
    '\n'
    '五、数据总结\n'
    '- 品类核心指标\n'
    '- Top3单品\n'
    '- 竞争力判断\n'
    '- 一句话结论\n'
    '\n'
    '【方式B：简要回答——用于其他所有问题（推荐、排名、趋势、是什么、怎么选等）】\n'
    '直接回答问题，3-10句话，只列关键数据和结论，不需要五段结构。\n'
    '格式：每个要点独占一行，以「- 」开头。\n'
    '\n'
    '【通用规则】\n'
    '- 正式客观，引用具体数字，禁止口语、感叹号、人称代词\n'
    '- 上下文有数据直接引用，没有的标注「行业参考」\n'
    '- 每个「- 」条目独占一行，条目间空行\n'
)

CHAT_SYSTEM_PROMPT = (
    "你是 AI 电商选品助手，帮用户做选品决策。"
    "回复简短直接，不超过两句话。"
    "用户如果说的是日常闲聊（你好、谢谢、再见），正常简短回复即可。"
    "用户如果说的是选品相关问题但你没有收到商品数据，告诉用户'数据库暂无相关数据，换个品类试试'。"
)


def chat_with_context(query: str, context: list[str], stream: bool = False) -> str:
    """单轮对话（不带历史）。"""
    context_text = "\n\n---\n\n".join(context)
    user_prompt = f"参考商品信息：\n{context_text}\n\n用户问题：{query}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return _call_llm(messages, stream)


def _build_messages(query: str, context: list[str], history: list[dict], deep_thinking: bool = False):
    """构建消息列表并决定使用哪个模型。context 为空时走普通对话模式。"""
    if context:
        # 分析模式：注入商品数据
        context_text = "\n\n---\n\n".join(context)
        user_prompt = f"参考商品信息：\n{context_text}\n\n用户问题：{query}"
        system_prompt = SYSTEM_PROMPT
    else:
        # 普通对话模式：不注入商品数据
        user_prompt = query
        system_prompt = CHAT_SYSTEM_PROMPT

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    model = settings.LLM_REASONER_MODEL if deep_thinking else settings.LLM_MODEL
    return messages, model


def chat_with_history(query: str, context: list[str], history: list[dict], stream: bool = False, deep_thinking: bool = False) -> str:
    """多轮对话（带历史记录）。"""
    messages, model = _build_messages(query, context, history, deep_thinking)
    return _call_llm(messages, stream, model=model)


def chat_with_history_stream(query: str, context: list[str], history: list[dict], deep_thinking: bool = False):
    """多轮对话的流式版本，逐段 yield (kind, text)，kind ∈ {'reasoning', 'content'}。"""
    messages, model = _build_messages(query, context, history, deep_thinking)
    yield from _call_llm_stream(messages, model=model)


def _call_llm(messages: list[dict], stream: bool = False, model: str = None) -> str:
    """调用 LLM API（含重试逻辑）。"""
    if model is None:
        model = settings.LLM_MODEL

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "stream": stream,
    }
    # DeepSeek reasoner 不支持 temperature 参数
    if model == settings.LLM_REASONER_MODEL:
        payload.pop("temperature", None)

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{settings.LLM_API_BASE}/chat/completions",
                json=payload,
                headers=headers,
                stream=stream,
                timeout=120,
            )

            if stream:
                return resp

            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                logger.warning("LLM API 连接失败 (第 %s/%s 次)，%s秒后重试: %s", attempt, MAX_RETRIES, wait, e)
                time.sleep(wait)
            else:
                logger.error("LLM API 连接失败，已达最大重试次数: %s", e)

    raise last_error


def _call_llm_stream(messages: list[dict], model: str = None):
    """流式调用 LLM API，逐段 yield (kind, text)。"""
    if model is None:
        model = settings.LLM_MODEL

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if model != settings.LLM_REASONER_MODEL:
        payload["temperature"] = 0.7

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{settings.LLM_API_BASE}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                line = line[5:].strip()
                if line == "[DONE]":
                    return
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                choices = data.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                if delta.get("reasoning_content"):
                    yield ("reasoning", delta["reasoning_content"])
                if delta.get("content"):
                    yield ("content", delta["content"])
            return

        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                logger.warning("LLM 流式连接失败 (第 %s/%s 次)，%s秒后重试: %s", attempt, MAX_RETRIES, wait, e)
                time.sleep(wait)
            else:
                logger.error("LLM 流式连接失败，已达最大重试次数: %s", e)

    raise last_error
