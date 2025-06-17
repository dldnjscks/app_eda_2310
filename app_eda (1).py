import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Population Trends 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **인구 추이 데이터셋**  
                - 파일명: `population_trends.csv`  
                - 설명: 한국 각 지역의 연도별 인구·출생아수·사망자수 데이터  
                - 주요 변수:  
                  - `연도`: 연도  
                  - `지역`: 행정구역명  
                  - `인구`: 해당 연도의 인구수  
                  - `출생아수(명)`: 해당 연도의 출생아수  
                  - `사망자수(명)`: 해당 연도의 사망자수  
                """)
# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        # 1) 데이터 로드 및 전처리
        df = pd.read_csv(uploaded)
        # '세종' 지역의 '-' 결측치를 0으로, 주요 열을 숫자형으로 변환
        mask_sejong = df['지역'] == '세종'
        df.loc[mask_sejong, ['인구','출생아수(명)','사망자수(명)']] = \
            df.loc[mask_sejong, ['인구','출생아수(명)','사망자수(명)']].replace('-', 0)
        for col in ['인구','출생아수(명)','사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 2) 탭 구조
        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화"
        ])

        # ── 기초 통계
        with tabs[0]:
            st.header("📝 기초 통계")
            st.subheader("데이터 구조 (`df.info()`)")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())

            st.subheader("기본 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

            st.subheader("결측치 및 중복 확인")
            st.write(df.isnull().sum())
            st.write(f"- 중복 행 개수: {df.duplicated().sum()}개")

        # ── 연도별 추이
        with tabs[1]:
            st.header("📈 연도별 전체 인구 추이")
            df_nation = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            ax.plot(df_nation['연도'], df_nation['인구'], marker='o')
            ax.set_title("Yearly Population Trend (Nationwide)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

        # ── 지역별 분석
        with tabs[2]:
            st.header("📊 지역별 인구 변화량 순위")
            years = sorted(df['연도'].unique())
            last_year = years[-1]
            prev_year = last_year - 5
            df_recent = df[df['연도'].isin([prev_year, last_year])]
            pivot = df_recent.pivot(index='지역', columns='연도', values='인구').drop('전국', errors='ignore')
            pivot['변화량'] = pivot[last_year] - pivot[prev_year]
            ranked = pivot['변화량'].sort_values(ascending=False)

            fig, ax = plt.subplots()
            sns.barplot(x=ranked.values, y=ranked.index, ax=ax)
            ax.set_xlabel("Population Change")
            ax.set_ylabel("Region")
            st.pyplot(fig)

        # ── 변화량 분석
        with tabs[3]:
            st.header("🔍 증감률 상위 지역 및 연도")
            df = df.sort_values(['지역','연도'])
            df['diff'] = df.groupby('지역')['인구'].diff()
            df['pct_change'] = df.groupby('지역')['인구'].pct_change()

            top100 = (
                df[df['지역'] != '전국']
                .nlargest(100, 'diff')[['지역','연도','diff']]
                .reset_index(drop=True)
            )
            st.dataframe(
                top100.style
                .background_gradient(subset=['diff'], cmap='bwr')
                .format({'diff': '{:,.0f}'})
            )

        # ── 시각화
        with tabs[4]:
            st.header("🌐 누적 영역 그래프")
            df_area = df[df['지역'] != '전국']
            area_pivot = df_area.pivot(index='연도', columns='지역', values='인구')
            fig, ax = plt.subplots()
            area_pivot.plot.area(ax=ax)
            ax.set_title("Population by Region Over Years")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()