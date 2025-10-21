import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import re

st.set_page_config(
    page_title="Cào tin Chứng khoán", 
    page_icon="📈", 
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .article-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background: white;
    }
    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .cafef { background: #ff6b6b; color: white; }
    .vietstock { background: #4ecdc4; color: white; }
    .nguoiquansat { background: #95e1d3; color: #2c3e50; }
    .baomoi { background: #f38181; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sources' not in st.session_state:
    st.session_state.sources = [
        {
            'id': 'cafef',
            'name': 'CafeF',
            'url': 'https://cafef.vn/timeline/3/trang-{}.chn',
            'active': True
        },
        {
            'id': 'vietstock',
            'name': 'VietStock',
            'url': 'https://vietstock.vn/chung-khoan.htm',
            'active': True
        },
        {
            'id': 'nguoiquansat',
            'name': 'Người Quan Sát',
            'url': 'https://nguoiquansat.vn/chung-khoan',
            'active': True
        },
        {
            'id': 'baomoi',
            'name': 'Báo Mới',
            'url': 'https://baomoi.com/chung-khoan.epi',
            'active': True
        }
    ]

if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []

# Helper functions
def get_headers():
    """Tạo headers để tránh bị chặn"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    }

def parse_relative_time(time_str):
    """Parse thời gian tương đối (X phút trước, X giờ trước)"""
    now = datetime.now()
    time_str = time_str.lower().strip()
    
    try:
        if 'giây' in time_str or 'giay' in time_str:
            seconds = int(re.search(r'\d+', time_str).group())
            return now - timedelta(seconds=seconds)
        elif 'phút' in time_str or 'phut' in time_str:
            minutes = int(re.search(r'\d+', time_str).group())
            return now - timedelta(minutes=minutes)
        elif 'giờ' in time_str or 'gio' in time_str:
            hours = int(re.search(r'\d+', time_str).group())
            return now - timedelta(hours=hours)
        elif 'ngày' in time_str or 'ngay' in time_str:
            days = int(re.search(r'\d+', time_str).group())
            return now - timedelta(days=days)
    except:
        pass
    
    # Try parsing as datetime
    for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%H:%M %d/%m/%Y']:
        try:
            return datetime.strptime(time_str, fmt)
        except:
            continue
    
    return now

def scrape_cafef(target_date, max_pages=5):
    """Cào tin từ CafeF"""
    articles = []
    base_url = 'https://cafef.vn/timeline/3/trang-{}.chn'
    
    try:
        for page in range(1, max_pages + 1):
            url = base_url.format(page)
            response = requests.get(url, headers=get_headers(), timeout=15)
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_='tlitem')
            
            for item in items:
                try:
                    title_tag = item.find('h3', class_='title')
                    if not title_tag:
                        continue
                    
                    link_tag = title_tag.find('a')
                    if not link_tag:
                        continue
                    
                    time_tag = item.find('span', class_='time')
                    desc_tag = item.find('p', class_='sapo')
                    
                    title = link_tag.text.strip()
                    link = link_tag.get('href', '')
                    if not link.startswith('http'):
                        link = 'https://cafef.vn' + link
                    
                    time_str = time_tag.text.strip() if time_tag else ''
                    content = desc_tag.text.strip() if desc_tag else ''
                    
                    article_date = parse_relative_time(time_str)
                    
                    if article_date.date() >= target_date:
                        articles.append({
                            'title': title,
                            'link': link,
                            'time': time_str,
                            'datetime': article_date,
                            'content': content,
                            'source': 'cafef'
                        })
                except Exception as e:
                    continue
            
            time.sleep(1)
            
    except Exception as e:
        st.error(f"Lỗi khi cào CafeF: {str(e)}")
    
    return articles

def scrape_vietstock(target_date):
    """Cào tin từ VietStock"""
    articles = []
    url = 'https://vietstock.vn/chung-khoan.htm'
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return articles
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('div', class_='news-item')
        
        for item in items[:20]:  # Giới hạn 20 tin
            try:
                title_tag = item.find('h3')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                time_tag = item.find('span', class_='date')
                desc_tag = item.find('p', class_='desc')
                
                if not link_tag:
                    continue
                
                title = link_tag.text.strip()
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = 'https://vietstock.vn' + link
                
                time_str = time_tag.text.strip() if time_tag else ''
                content = desc_tag.text.strip() if desc_tag else ''
                
                article_date = parse_relative_time(time_str)
                
                if article_date.date() >= target_date:
                    articles.append({
                        'title': title,
                        'link': link,
                        'time': time_str,
                        'datetime': article_date,
                        'content': content,
                        'source': 'vietstock'
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        st.error(f"Lỗi khi cào VietStock: {str(e)}")
    
    return articles

def scrape_nguoiquansat(target_date):
    """Cào tin từ Người Quan Sát"""
    articles = []
    url = 'https://nguoiquansat.vn/chung-khoan'
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return articles
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('article', class_='item-news')[:20]
        
        for item in items:
            try:
                title_tag = item.find('h3', class_='title-news')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                time_tag = item.find('span', class_='time-ago')
                desc_tag = item.find('div', class_='sapo')
                
                if not link_tag:
                    continue
                
                title = link_tag.text.strip()
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = 'https://nguoiquansat.vn' + link
                
                time_str = time_tag.text.strip() if time_tag else ''
                content = desc_tag.text.strip() if desc_tag else ''
                
                article_date = parse_relative_time(time_str)
                
                if article_date.date() >= target_date:
                    articles.append({
                        'title': title,
                        'link': link,
                        'time': time_str,
                        'datetime': article_date,
                        'content': content,
                        'source': 'nguoiquansat'
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        st.error(f"Lỗi khi cào Người Quan Sát: {str(e)}")
    
    return articles

def scrape_baomoi(target_date):
    """Cào tin từ Báo Mới"""
    articles = []
    url = 'https://baomoi.com/chung-khoan.epi'
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return articles
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('div', class_='story')[:20]
        
        for item in items:
            try:
                title_tag = item.find('h4', class_='story__heading')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                time_tag = item.find('time')
                desc_tag = item.find('div', class_='story__summary')
                
                if not link_tag:
                    continue
                
                title = link_tag.get('title', link_tag.text.strip())
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = 'https://baomoi.com' + link
                
                time_str = time_tag.text.strip() if time_tag else ''
                content = desc_tag.text.strip() if desc_tag else ''
                
                article_date = parse_relative_time(time_str)
                
                if article_date.date() >= target_date:
                    articles.append({
                        'title': title,
                        'link': link,
                        'time': time_str,
                        'datetime': article_date,
                        'content': content,
                        'source': 'baomoi'
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        st.error(f"Lỗi khi cào Báo Mới: {str(e)}")
    
    return articles

# Main UI
st.markdown('<div class="main-header">📈 Công cụ cào tin Chứng khoán</div>', unsafe_allow_html=True)
st.markdown("Thu thập tin tức từ các nguồn uy tín trong ngày")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Cài đặt")
    
    start_date = st.date_input(
        "📅 Ngày bắt đầu",
        value=datetime.now(),
        max_value=datetime.now()
    )
    
    st.subheader("Nguồn tin")
    for source in st.session_state.sources:
        source['active'] = st.checkbox(
            source['name'],
            value=source['active'],
            key=f"source_{source['id']}"
        )
    
    st.divider()
    
    # Add custom source
    with st.expander("➕ Thêm nguồn mới"):
        new_name = st.text_input("Tên nguồn", key="new_source_name")
        new_url = st.text_input("URL", key="new_source_url")
        if st.button("Lưu", key="add_source_btn"):
            if new_name and new_url:
                new_id = new_name.lower().replace(' ', '_')
                st.session_state.sources.append({
                    'id': new_id,
                    'name': new_name,
                    'url': new_url,
                    'active': True
                })
                st.success(f"✅ Đã thêm {new_name}")
                st.rerun()

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    scrape_button = st.button("🔍 Cào tin tức", type="primary", use_container_width=True)

with col2:
    if st.session_state.scraped_data:
        st.metric("Tổng số tin", len(st.session_state.scraped_data))

# Scraping process
if scrape_button:
    active_sources = [s for s in st.session_state.sources if s['active']]
    
    if not active_sources:
        st.warning("⚠️ Vui lòng chọn ít nhất một nguồn tin!")
    else:
        all_articles = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, source in enumerate(active_sources):
            status_text.info(f"🔄 Đang cào tin từ {source['name']}...")
            
            try:
                if source['id'] == 'cafef':
                    articles = scrape_cafef(start_date)
                elif source['id'] == 'vietstock':
                    articles = scrape_vietstock(start_date)
                elif source['id'] == 'nguoiquansat':
                    articles = scrape_nguoiquansat(start_date)
                elif source['id'] == 'baomoi':
                    articles = scrape_baomoi(start_date)
                else:
                    articles = []
                
                all_articles.extend(articles)
                status_text.success(f"✅ {source['name']}: {len(articles)} tin")
                
            except Exception as e:
                status_text.error(f"❌ Lỗi {source['name']}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(active_sources))
            time.sleep(0.5)
        
        # Sort by datetime
        all_articles.sort(key=lambda x: x['datetime'], reverse=True)
        st.session_state.scraped_data = all_articles
        
        status_text.success(f"🎉 Hoàn thành! Tìm thấy {len(all_articles)} tin tức")

# Display results
if st.session_state.scraped_data:
    st.divider()
    
    # Export button
    df = pd.DataFrame(st.session_state.scraped_data)
    df_export = df[['title', 'link', 'time', 'content', 'source']].copy()
    
    csv = df_export.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="⬇️ Tải xuống CSV",
        data=csv,
        file_name=f"tin-chung-khoan-{start_date}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.subheader(f"📰 Kết quả: {len(st.session_state.scraped_data)} tin tức")
    
    # Filter by source
    source_filter = st.multiselect(
        "Lọc theo nguồn:",
        options=list(set([a['source'] for a in st.session_state.scraped_data])),
        default=list(set([a['source'] for a in st.session_state.scraped_data]))
    )
    
    filtered_data = [a for a in st.session_state.scraped_data if a['source'] in source_filter]
    
    # Display articles
    for article in filtered_data:
        source_class = article['source']
        
        st.markdown(f"""
        <div class="article-card">
            <span class="source-badge {source_class}">{article['source'].upper()}</span>
            <span style="color: #666; font-size: 0.875rem;">🕐 {article['time']}</span>
            <h3 style="margin: 0.5rem 0;">{article['title']}</h3>
            <p style="color: #555; margin: 0.5rem 0;">{article['content']}</p>
            <a href="{article['link']}" target="_blank" style="color: #1f77b4; text-decoration: none;">
                🔗 Đọc thêm →
            </a>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>⚠️ <strong>Lưu ý:</strong> Tool này chỉ dùng cho mục đích học tập. Vui lòng tuân thủ robots.txt và terms of service của từng website.</p>
    <p>Phát triển bởi <strong>Streamlit</strong> | Version 1.0</p>
</div>
""", unsafe_allow_html=True)
