import streamlit as st
import pandas as pd 
import numpy as np 
from load_data import load_and_process_data, create_nutrient_constraints, load_all_menus, load_sample_file
from evaluation_function import calculate_harmony_matrix, get_top_n_harmony_pairs
from MOO import MultiObjectiveDietOptimizer
from utils import diet_to_dataframe, count_menu_changes

# Set page config
st.set_page_config(page_title="식단 최적화 프로그램", page_icon="🍽️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .menu-item {
        background-color: #f1f3f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .menu-item strong {
        color: #1e88e5;
    }
    .emoji-rank {
        font-size: 1.2em;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 및 초기화 (이전과 동일)
@st.cache_data
def load_data():
    diet_db_path = '../data/DIET_2401.xlsx'
    menu_db_path = '../data/Menu_ingredient_nutrient.xlsx'
    ingre_db_path = '../data/Ingredient_Price.xlsx'
    
    diet_db = load_and_process_data(diet_db_path, menu_db_path, ingre_db_path)
    nutrient_constraints = create_nutrient_constraints()
    harmony_matrix, menus, menu_counts, _ = calculate_harmony_matrix(diet_db)
    all_menus = load_all_menus(menu_db_path, ingre_db_path)
    
    return diet_db, nutrient_constraints, harmony_matrix, menus, menu_counts, all_menus

diet_db, nutrient_constraints, harmony_matrix, menus, menu_counts, all_menus = load_data()

# Streamlit 앱 시작
st.title('🍽️ 식단 최적화 프로그램')
st.markdown("---")

# 사이드바: 최적화 파라미터 및 가중치 설정 (이전과 동일)
with st.sidebar:
    st.header('🎚️ 최적화 설정')
    
    st.subheader('최적화 파라미터')
    generations = st.number_input('세대 수', min_value=10, max_value=500, value=100, step=10)
    population_size = st.number_input('인구 크기', min_value=10, max_value=200, value=50, step=10)

# 기존 데이터 분석 결과 표시
st.header('📊 현재까지 급식 제공 현황')

col1, col2 = st.columns(2)

with col1:
    st.subheader('🍽️ 가장 많이 함께 나온 메뉴 조합')
    top_5_pairs = get_top_n_harmony_pairs(harmony_matrix, menus, 5)
    for i, (menu1, menu2, frequency) in enumerate(top_5_pairs, 1):
        emoji_rank = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1]
        st.markdown(f"""
        <div class="menu-item">
            <span class="emoji-rank">{emoji_rank}</span>
            <strong>{menu1}</strong> - <strong>{menu2}</strong>: {frequency}회
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader('🍲 가장 자주 나온 메뉴')
    top_5_menus = menu_counts.most_common(5)
    for i, (menu, occurrences) in enumerate(top_5_menus, 1):
        emoji_rank = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1]
        st.markdown(f"""
        <div class="menu-item">
            <span class="emoji-rank">{emoji_rank}</span>
            <strong>{menu}</strong>: {occurrences}회
        </div>
        """, unsafe_allow_html=True)

# 초기 식단 업로드 (이전과 동일)
st.header('📤 초기 식단 업로드')
uploaded_file = st.file_uploader("초기 식단 Excel 파일을 업로드하세요", type="xlsx")

def calculate_improvements(initial_fitness, optimized_fitness):
    improvements = []
    for init, opt in zip(initial_fitness, optimized_fitness):
        if init != 0:
            imp = (opt - init) / abs(init) * 100
        else:
            imp = float('inf') if opt > 0 else (0 if opt == 0 else float('-inf'))
        improvements.append(imp)
    return improvements

if uploaded_file is not None:
    #import_sample = load_sample_file(uploaded_file)
    weekly_diet = load_and_process_data(uploaded_file, '../data/Menu_ingredient_nutrient.xlsx', '../data/Ingredient_Price.xlsx')
    
    optimizer = MultiObjectiveDietOptimizer(all_menus, nutrient_constraints, harmony_matrix)
    initial_fitness = optimizer.fitness(diet_db, weekly_diet)
    
    st.subheader('📅 초기 식단')
    st.dataframe(diet_to_dataframe(weekly_diet, "Initial Diet"), use_container_width=True)
    st.info(f"📊 초기 식단 적합도: 영양({initial_fitness[0]:.2f}), 비용({initial_fitness[1]:.2f}), 조화({initial_fitness[2]:.2f}), 다양성({initial_fitness[3]:.2f})")
        
if st.button('🚀 식단 최적화 시작'):
    with st.spinner('최적화 진행 중...'):
        pareto_front = optimizer.optimize(diet_db, weekly_diet, generations, population_size)
    
    st.success('최적화 완료!')
    
    # 3가지 이상 개선된 식단 선별
    improved_diets = []
    for optimized_diet in pareto_front:
        optimized_fitness = optimizer.fitness(diet_db, optimized_diet)
        improvements = calculate_improvements(initial_fitness, optimized_fitness)
        if sum(1 for imp in improvements if imp > 0) >= 3:
            improved_diets.append((optimized_diet, optimized_fitness, improvements))
    
    # 최대 5개까지 선별
    improved_diets = improved_diets[:5]
    
    if improved_diets:
        st.subheader('🏆 아래 식단으로 바꿔보는건 어떨까요?')
        for i, (optimized_diet, optimized_fitness, improvements) in enumerate(improved_diets, 1):
            st.markdown(f"### 제안 식단 {i}")
            st.dataframe(diet_to_dataframe(optimized_diet, f"Optimized Diet {i}"), use_container_width=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("영양 점수", f"{optimized_fitness[0]:.2f}", f"{improvements[0]:.2f}%")
            with col2:
                st.metric("비용 점수", f"{optimized_fitness[1]:.2f}", f"{improvements[1]:.2f}%")
            with col3:
                st.metric("조화 점수", f"{optimized_fitness[2]:.2f}", f"{improvements[2]:.2f}%")
            with col4:
                st.metric("다양성 점수", f"{optimized_fitness[3]:.2f}", f"{improvements[3]:.2f}%")
            
            menu_changes = count_menu_changes(weekly_diet, optimized_diet)
            st.markdown('#### 📈 카테고리별 메뉴 변경 비율')
            for category, counts in menu_changes.items():
                percentage = (counts['changed'] / counts['total']) * 100 if counts['total'] > 0 else 0
                st.markdown(f"""
                <div class="menu-item">
                    <strong>{category}</strong>: {counts['changed']}/{counts['total']} ({percentage:.2f}%)
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("3가지 이상 개선된 식단을 찾지 못했습니다. 다시 시도해보세요.")

st.markdown("---")
st.caption("© 2024 식단 최적화 프로그램. All rights reserved.")