import streamlit as st
import aiohttp
import asyncio
import json

# Streamlit의 세션 상태를 사용하여 대화 내용을 저장
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {'role': 'user',
         'content': '당신은 학교 수업에서 사용되는 인공지능입니다. 당신은 학생과 대화 중입니다. 대화 내용은 오로지 학교 수업과 관련되어야 합니다. 다른 대화 내용은 거부해야 합니다. 응답은 세 문장 이하로 생성하시오. 응답의 끝에는 질문을 추가해서 대화를 이어가시오. 해당 내용과 관련 없는 내용이 입력되면 답변을 거부하고 원래 주제로 대화할 수 있도록 이끌어 주세요.'},
        {'role': 'assistant', 'content': '네'},
        {'role': 'assistant', 'content': '어떤 주제로 이야기를 나눠볼까요?'}
    ]

if "input_message" not in st.session_state:
    st.session_state.input_message = ""

if "copied_chat_history" not in st.session_state:
    st.session_state.copied_chat_history = ""

if "user_age" not in st.session_state:
    st.session_state.user_age = ""

if "last_grade_level" not in st.session_state:
    st.session_state.last_grade_level = ""


# 비동기 API 호출을 위한 함수 정의
async def fetch_completion(completion_request, session):
    url = 'https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003'
    headers = {
        'X-NCP-CLOVASTUDIO-API-KEY': 'NTA0MjU2MWZlZTcxNDJiY6Yo7+BLuaAQ2B5+PgEazGquXEqiIf8NRhOG34cVQNdq',
        'X-NCP-APIGW-API-KEY': 'DilhGClorcZK5OTo1QgdfoDQnBNOkNaNksvlAVFE',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': 'd1950869-54c9-4bb8-988d-6967d113e03f',
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'text/event-stream'
    }

    async with session.post(url, headers=headers, json=completion_request) as response:
        response_data = await response.text()
        return response_data


# 비동기 API 호출을 실행하는 함수
async def execute_completion(completion_request):
    async with aiohttp.ClientSession() as session:
        response_data = await fetch_completion(completion_request, session)
        lines = response_data.split("\n")

        json_data = None
        for i, line in enumerate(lines):
            if line.startswith("event:result"):
                next_line = lines[i + 1]
                json_data = next_line[5:]  # "data:" 이후의 문자열 추출
                break

        if json_data:
            try:
                chat_data = json.loads(json_data)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": chat_data["message"]["content"]}
                )
                print("Updated chat history:", st.session_state.chat_history)  # 콘솔에 chat_history 출력
            except json.JSONDecodeError as e:
                print("JSONDecodeError:", e)


# 사용자의 메시지를 처리하고 API 호출
def send_message():
    if st.session_state.input_message:
        # 사용자가 입력한 메시지에 '사용자 나이에 적절한 건전한 대화를 해주세요.' 문구를 추가
        user_message = st.session_state.input_message + " 사용자 나이에 적절한 건전한 대화를 해주세요."

        # st.session_state.chat_history에 사용자 메시지 추가
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        # API 요청을 위한 데이터 구성
        completion_request = {
            'messages': st.session_state.chat_history,
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 256,
            'temperature': 0.7,
            'repeatPenalty': 1.2,
            'stopBefore': [],
            'includeAiFilters': True,
            'seed': 0
        }

        # 비동기 API 호출 실행
        asyncio.run(execute_completion(completion_request))

        # 입력 필드 초기화
        st.session_state.input_message = ""


# Streamlit UI 구성
st.markdown('<h1 class="title">학습 도움 챗봇</h1>', unsafe_allow_html=True)

grade_level = st.radio(
    "학년을 선택하세요:",
    ('초등학생', '중학생', '고등학생'),
    horizontal=True
)


def update_user_age():
    if grade_level != st.session_state.last_grade_level:
        # 학년에 따라 사용자 나이 설정
        if grade_level == '초등학생':
            user_age = '12살'
        elif grade_level == '중학생':
            user_age = '15살'
        elif grade_level == '고등학생':
            user_age = '18살'

        # 세션 상태에 사용자 나이를 저장
        st.session_state.user_age = user_age
        st.session_state.last_grade_level = grade_level

        # 기존에 '나는 {나이}입니다.'로 시작하는 메시지를 chat_history에서 삭제
        st.session_state.chat_history = [
            message for message in st.session_state.chat_history
            if not (message['role'] == 'user' and "사용자는" in message['content'] and "입니다. 사용자 나이에 적절한 건전한 대화를 해주세요." in
                    message['content'])
        ]

        # 대화 내역에 사용자 연령 메시지 추가
        st.session_state.chat_history.append(
            {'role': 'user', 'content': f'사용자는 {st.session_state.user_age} 입니다. 사용자 나이에 적절한 건전한 대화를 해주세요.'}
        )


update_user_age()

# 대화창 출력
for message in st.session_state.chat_history[3:]:
    role = "User" if message["role"] == "user" else "Chatbot"

    # UI에 출력할 때는 '사용자 나이에 적절한 건전한 대화를 해주세요.' 문구를 제거
    content_to_display = message["content"].replace(" 사용자 나이에 적절한 건전한 대화를 해주세요.", "")

    # '나는 {나이}'로 시작하는 메시지는 출력하지 않음
    if "사용자는" in message["content"] and "입니다. 사용자 나이에 적절한 건전한 대화를 해주세요." in message["content"]:
        continue

    # 메시지를 콘솔에 출력 (대신 history 값은 출력하지 않음)
    print(f"{role}: {message['content']}")

    if role == "User":
        st.markdown(f'''
            <div style="background-color: #ADD8E6; 
                        text-align: right; 
                        padding: 10px; 
                        border-radius: 5px; 
                        margin: 10px 0;
                        max-width: 80%;
                        float: right;
                        clear: both;">
                {content_to_display}
            </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div style="background-color: #90EE90; 
                        text-align: left; 
                        padding: 10px; 
                        border-radius: 5px; 
                        margin: 10px 0;
                        max-width: 80%;
                        float: left;
                        clear: both;">
                {content_to_display}
            </div>''', unsafe_allow_html=True)

# 입력 폼 및 버튼
with st.form(key="input_form", clear_on_submit=True):
    user_message = st.text_input("학습하면서 궁금한 주제에 관해서 이야기를 나눠보세요:", key="input_message", placeholder="")
    submit_button = st.form_submit_button(label="입력", on_click=send_message)
