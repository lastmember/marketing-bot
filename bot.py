import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ 환경변수에서 키 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Claude 클라이언트 초기화
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 대화 기록 저장 (사용자별)
conversation_history = {}

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 영업/마케팅 전문 AI 비서입니다. 두 가지 역할을 합니다:

1. **카피 작성**: 제품/서비스 정보를 받으면 광고 카피, 슬로건, SNS 게시물, 이메일 제목, 랜딩페이지 문구 등을 작성합니다.

2. **카피 분석**: 기존 카피를 받으면 다음을 분석합니다:
   - 강점 및 약점
   - 타겟 고객 적합성
   - 감성적/이성적 소구 점수 (10점 만점)
   - 개선 제안 2~3가지
   - 종합 평점 (⭐ 1~5개)

항상 한국어로 답변하고, 실용적이고 구체적인 내용을 제공하세요."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 명령어"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []  # 대화 기록 초기화

    await update.message.reply_text(
        "안녕하세요! 마케팅 AI 비서입니다 ✨\n\n"
        "📝 *카피 작성*: 제품명, 타겟, 특징을 알려주세요\n"
        "🔍 *카피 분석*: 기존 카피를 붙여넣어 주세요\n\n"
        "명령어:\n"
        "/start - 대화 초기화\n"
        "/help - 사용법 보기\n"
        "/clear - 대화 기록 삭제\n\n"
        "무엇을 도와드릴까요?",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말"""
    await update.message.reply_text(
        "📖 *사용법*\n\n"
        "*카피 작성 예시:*\n"
        "→ '스킨케어 제품, 20-30대 여성, 자연성분 강조, 인스타 광고 문구 만들어줘'\n\n"
        "*카피 분석 예시:*\n"
        "→ '지금 이 문구 분석해줘: 당신의 피부가 말합니다, 자연이 답입니다'\n\n"
        "대화는 이어지니까 자유롭게 수정 요청도 가능해요!",
        parse_mode="Markdown"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """대화 기록 삭제"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("🗑️ 대화 기록을 초기화했어요. 새로 시작해볼까요?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 메시지 처리"""
    user_id = update.effective_user.id
    user_text = update.message.text

    # 대화 기록 없으면 초기화
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # 사용자 메시지 추가
    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    # 타이핑 표시
    await update.message.chat.send_action("typing")

    try:
        # Claude API 호출
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        reply = response.content[0].text

        # 응답 기록 추가
        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        # 대화 기록이 너무 길어지면 오래된 것 제거 (최근 20개 유지)
        if len(conversation_history[user_id]) > 20:
            conversation_history[user_id] = conversation_history[user_id][-20:]

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "⚠️ 오류가 발생했어요. 잠시 후 다시 시도해주세요."
        )
        print(f"Error: {e}")


def main():
    """봇 실행"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ 봇이 시작되었습니다!")
    app.run_polling()


if __name__ == "__main__":
    main()
