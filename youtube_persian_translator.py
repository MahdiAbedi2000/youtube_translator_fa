"""
ابزار تحت وب برای ترجمه زیرنویس ویدیوهای یوتیوب به فارسی با استفاده از Streamlit و Google Gemini.
- دریافت متن ویدیو از Supadata API
- ترجمه خودکار به فارسی با مدل Gemini
- رابط کاربری راست‌به‌چپ و مناسب فارسی
- امکان خلاصه‌سازی و دانلود نتایج
-پسورد پیش فرض 1111 ذخیره شده است و قابلیت تغییر دارد 
⚠️ توجه: برای استفاده باید کلیدهای API معتبر خود را وارد کنید. کلیدهای پیش‌فرض حذف شده‌اند.
"""
import streamlit as st
import requests
import json
from google import genai
import time
import re

# API Keys (برای امنیت، مقداردهی نشده‌اند. لطفاً کلیدهای خود را وارد کنید)
SUPADATA_API_KEY = ""
GOOGLE_API_KEY = ""



# Initialize Streamlit UI with RTL support and custom font
st.set_page_config(page_title="مترجم ویدیوهای یوتیوب", layout="wide")
st.markdown("""
<style>
    @font-face {
        font-family: 'Vazir';
        src: url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir-Regular.woff2');
    }
    body, .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #3a0000 100%) !important;
        color: #fff !important;
    }
    .persian-text {
        font-family: 'Vazir', sans-serif;
        direction: rtl;
        text-align: right;
        color: #ff1744 !important;
        text-shadow: 1px 1px 8px #000;
    }
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #ff1744 !important;
        background: #1a1a1a !important;
        color: #fff !important;
        font-family: 'Vazir', sans-serif;
        font-size: 1.1rem;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 2px solid #ff5252 !important;
        box-shadow: 0 0 8px #ff1744;
    }
    .rtl-text-area textarea {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Vazir', sans-serif !important;
        background: #1a1a1a !important;
        color: #fff !important;
        border: 2px solid #ff1744 !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff1744 0%, #1a1a1a 100%) !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 0.5rem 2rem !important;
        margin-top: 1rem !important;
        border: none !important;
        box-shadow: 0 2px 8px #ff1744;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1a1a1a 0%, #ff1744 100%) !important;
        color: #fff !important;
        box-shadow: 0 4px 16px #ff5252;
    }
    .stSlider > div {
        color: #ff1744 !important;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #ff1744 0%, #1a1a1a 100%) !important;
    }
    .stStatus {
        background: #2d0a0a !important;
        color: #fff !important;
        border-left: 5px solid #ff1744 !important;
    }
    .stDownloadButton > button {
        background: #ff1744 !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        border: none !important;
        margin-top: 1rem !important;
        box-shadow: 0 2px 8px #ff1744;
    }
    .stDownloadButton > button:hover {
        background: #b71c1c !important;
        color: #fff !important;
    }
    .stSidebar {
        background: #1a1a1a !important;
        color: #fff !important;
        border-right: 2px solid #ff1744 !important;
    }
    .stSidebar .persian-text {
        color: #ff1744 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="persian-text">مترجم ویدیوهای یوتیوب</h1>', unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.markdown('<h2 class="persian-text" style="color:#ff9800; text-shadow:2px 2px 10px #000;">⚙️ تنظیمات پیشرفته</h2>', unsafe_allow_html=True)
    st.markdown('<div style="height:8px; background:linear-gradient(90deg,#ff9800,#ff1744); border-radius:4px; margin-bottom:10px;"></div>', unsafe_allow_html=True)
    chunk_size = st.slider("اندازه هر بخش (کاراکتر)", 10000, 20000, 12000, 1000)
    st.markdown('<hr style="border:1px dashed #ff9800;">', unsafe_allow_html=True)
    st.markdown('<h4 class="persian-text" style="color:#ff9800;">🔑 دسترسی به API</h4>', unsafe_allow_html=True)
    if 'password_checked' not in st.session_state:
        st.session_state['password_checked'] = False
    if 'password_success' not in st.session_state:
        st.session_state['password_success'] = False
    password = st.text_input("رمز عبور (در صورت داشتن)", type="password")
    confirm_btn = st.button("تأیید رمز")
    use_custom_keys = False
    user_supadata_key = ""
    user_google_key = ""
    supadata_key = None
    google_key = None
    if confirm_btn:
        if password == "1111":
            st.session_state['password_checked'] = True
            st.session_state['password_success'] = True
        else:
            st.session_state['password_checked'] = True
            st.session_state['password_success'] = False
    if st.session_state['password_checked']:
        if st.session_state['password_success']:
            st.success("دسترسی ویژه فعال شد! از APIهای پیش‌فرض استفاده می‌شود.")
            supadata_key = SUPADATA_API_KEY
            google_key = GOOGLE_API_KEY
        else:
            st.error("رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.")
            st.info("در صورت نداشتن رمز، کلیدهای API خود را وارد کنید:")
            user_supadata_key = st.text_input("Supadata API Key")
            user_google_key = st.text_input("Google API Key")
            if user_supadata_key and user_google_key:
                supadata_key = user_supadata_key
                google_key = user_google_key
                use_custom_keys = True

# تابع تقسیم متن به بخش‌های کوچکتر با حفظ ساختار جملات
def split_text(text, max_chunk_size=8000):
    """Split text into chunks, preserving sentence structure"""
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_size = len(sentence)
        # اگر جمله به تنهایی بزرگتر از max_chunk_size باشد، آن را به کلمات تقسیم می‌کنیم
        if sentence_size > max_chunk_size:
            if current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []
                current_size = 0
            words = sentence.split()
            temp_chunk = []
            temp_size = 0
            for word in words:
                if temp_size + len(word) + 1 > max_chunk_size:
                    if temp_chunk:
                        chunks.append(' '.join(temp_chunk))
                    temp_chunk = [word]
                    temp_size = len(word)
                else:
                    temp_chunk.append(word)
                    temp_size += len(word) + 1
            if temp_chunk:
                chunks.append(' '.join(temp_chunk))
        # اگر اضافه کردن جمله به چانک فعلی از max_chunk_size تجاوز کند
        elif current_size + sentence_size + 2 > max_chunk_size:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size + 2  # +2 برای ". "
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    st.write(f"تعداد کل کاراکترها: {len(text)}")
    st.write(f"تعداد بخش‌ها: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        st.write(f"طول بخش {i+1}: {len(chunk)} کاراکتر")
    
    return chunks

# تابع ترجمه یک بخش با مکانیزم تلاش مجدد
def translate_chunk(client, chunk, retry_count=3):
    """Translate a single chunk with retry mechanism"""
    for attempt in range(retry_count):
        try:
            prompt = (f"You are a professional English to Persian translator with expertise in fluent and natural-sounding translations. Your task is to translate the following English text into Persian. Ensure the Persian translation is fluent, natural, and reads as if it were originally written in Persian. Pay attention to idioms, cultural references, and nuances in the English text and translate them appropriately into Persian. Avoid literal translations that may sound awkward or unnatural in Persian. Focus on conveying the intended message in clear and idiomatic Persian."
                      f"Provide only the Persian translation:\n\n{chunk}")
            st.info(f"Chunk for translation: {chunk}")  # نمایش چانک برای ترجمه
            response = client.models.generate_content(
                model="gemini-2.0-flash",  # در صورت نیاز می‌توانید به gemini-1.0-pro تغییر دهید
                contents=[{"text": prompt}]
            )
            st.info(f"Translation response: {response.text}")  # نمایش پاسخ ترجمه
            return response.text
        except Exception as e:
            st.error(f"Error during translation attempt {attempt + 1}: {str(e)}")
            if attempt == retry_count - 1:
                raise e
            time.sleep(2 ** attempt)
    return None

# Main interface
youtube_url = st.text_input("لینک ویدیوی یوتیوب را وارد کنید:")
col1, col2 = st.columns(2)
translate_button = col1.button("شروع ترجمه")
if col2.button("پاک کردن حافظه موقت"):
    st.cache_data.clear()

if translate_button:
    if not youtube_url:
        st.error("لطفاً لینک ویدیو را وارد کنید")
    elif not supadata_key or not google_key:
        st.error("لطفاً رمز صحیح وارد کنید یا هر دو کلید API را وارد نمایید.")
    else:
        try:
            with st.status("در حال ترجمه...", expanded=True) as status:
                # دریافت متن زیرنویس از API
                status.write("در حال دریافت متن ویدیو...")
                headers = {'x-api-key': supadata_key}
                try:
                    rr = requests.get(
                        f'https://api.supadata.ai/v1/youtube/transcript?url={youtube_url}',
                        headers=headers,
                        timeout=300
                    )
                    rr.raise_for_status()
                    response_json = rr.json()
                    
                    st.write("API Response:", response_json)  # نمایش خروجی API برای دیباگ
                    
                    # دسترسی به محتوا
                    content = response_json.get('content', [])
                    if isinstance(content, list):
                        text_content = []
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                text_content.append(item['text'])
                            elif isinstance(item, str):
                                text_content.append(item)
                    
                    # بعد از اتصال متون:
                    content = " ".join(text_content)

                    # پاکسازی: حذف ویرگول‌هایی که ممکن است در اطراف رشته‌ها ایجاد شده باشند
                    content = re.sub(r'\s*,\s*', ' ', content).strip()
                    
                    if not content:
                        st.error("متنی برای ترجمه یافت نشد!")
                        st.stop()
                        
                    st.info(f"متن استخراج شده: {len(content)} کاراکتر")
                
                except requests.exceptions.RequestException as e:
                    st.error("خطا در دریافت متن ویدیو")
                    st.error(f"جزئیات خطا: {str(e)}")
                    st.stop()
                
                # ایجاد کلاینت ترجمه
                client = genai.Client(api_key=google_key)
                
                # فرآیند ترجمه
                try:
                    status.write("تقسیم متن به بخش‌های کوچکتر...")
                    chunks = split_text(content, chunk_size)
                    st.info(f"متن به {len(chunks)} بخش تقسیم شد")
                    
                    progress_bar = st.progress(0)
                    status.write("شروع ترجمه...")
                    
                    translations = []
                    for i, chunk in enumerate(chunks):
                        status.write(f"در حال ترجمه بخش {i+1} از {len(chunks)}...")
                        try:
                            translation = translate_chunk(client, chunk)
                            translations.append(translation)
                            progress = (i + 1) / len(chunks)
                            progress_bar.progress(progress)
                            status.write(f"✅ بخش {i+1} با موفقیت ترجمه شد")
                            time.sleep(1)  # تاخیر کوتاه برای جلوگیری از محدودیت نرخ
                        except Exception as e:
                            st.error(f"خطا در ترجمه بخش {i+1}: {str(e)}")
                            continue
                    
                    final_translation = "\n".join(translations)
                    status.write("✅ ترجمه تکمیل شد!")
                    
                    if not final_translation:
                        st.error("خطا: ترجمه خالی است!")
                        st.stop()
                    
                    st.success(f"ترجمه {len(chunks)} بخش با موفقیت انجام شد")
                    
                    # دکمه خلاصه‌سازی هر ۵ بخش
                    summarize = st.button("خلاصه‌سازی هر ۵ بخش ترجمه‌شده (با مدل)")
                    summaries = []
                    if summarize:
                        st.info("در حال خلاصه‌سازی هر ۵ بخش...")
                        for i in range(0, len(translations), 5):
                            group = translations[i:i+5]
                            group_text = "\n".join(group)
                            summary_prompt = ("متن زیر را خلاصه کن به طوری تمام مطالب را پوشش دهد. فقط خلاصه فارسی را ارائه بده.\n\n" + group_text)
                            try:
                                response = client.models.generate_content(
                                    model="gemini-2.0-flash",
                                    contents=[{"text": summary_prompt}]
                                )
                                summaries.append(response.text)
                            except Exception as e:
                                st.error(f"خطا در خلاصه‌سازی گروه {i//5+1}: {str(e)}")
                                summaries.append("")
                        st.success(f"خلاصه‌سازی {len(summaries)} گروه انجام شد.")
                        for idx, summ in enumerate(summaries):
                            st.markdown(f'<h4 class="persian-text" style="color:#ff9800;">خلاصه گروه {idx+1}</h4>', unsafe_allow_html=True)
                            st.text_area(f"خلاصه گروه {idx+1}", summ, height=150, key=f"summary_{idx}", label_visibility="collapsed")
                        st.download_button(
                            label="⬇️ دانلود همه خلاصه‌ها",
                            data="\n\n".join(summaries),
                            file_name="summaries.txt",
                            mime="text/plain"
                        )
                    
                    # نمایش نتایج در دو ستون با پشتیبانی RTL
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<h3 class="persian-text" style="color:#ff9800;">متن اصلی</h3>', unsafe_allow_html=True)
                        st.info(f"تعداد کاراکترها: {len(content)}")
                        st.markdown('<div style="direction:rtl;text-align:right">', unsafe_allow_html=True)
                        st.text_area("Original", content, height=300, key="original_text", label_visibility="collapsed")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button(
                            label="⬇️ دانلود زیرنویس اصلی",
                            data=content,
                            file_name="subtitle.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.markdown('<h3 class="persian-text" style="color:#ff1744;">ترجمه فارسی</h3>', unsafe_allow_html=True)
                        st.info(f"تعداد کاراکترها: {len(final_translation)}")
                        st.markdown('<div style="direction:rtl;text-align:right">', unsafe_allow_html=True)
                        st.text_area("Translation", final_translation, height=300, key="translation_text", label_visibility="collapsed")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button(
                            label="⬇️ دانلود ترجمه فارسی",
                            data=final_translation,
                            file_name="translation.txt",
                            mime="text/plain"
                        )

                except Exception as e:
                    st.error("خطای غیرمنتظره در فرآیند ترجمه")
                    st.exception(e)
        
        except Exception as e:
            st.error("خطای غیرمنتظره")
            st.exception(e)

# همیشه راهنما و پیام انتهایی را نمایش بده
st.markdown("""
<hr style='border:1px solid #ff1744;'>
<div style='text-align:center; color:#ff1744; font-family:Vazir; font-size:1.1rem; margin-top:2em;'>
    ❤️ برنامه با عشق توسط <b>مهدی عابدی</b> توسعه داده شده است ❤️
</div>
<div style='background:#2d0a0a; color:#fff; border-radius:10px; padding:1.5em; margin-top:2em; font-family:Vazir; font-size:1.05rem;'>
    <b>راهنمای استفاده:</b><br>
    1. لینک ویدیوی یوتیوب را در کادر بالا وارد کنید.<br>
    2. روی دکمه <b>شروع ترجمه</b> کلیک کنید.<br>
    3. منتظر بمانید تا متن ویدیو دریافت و ترجمه شود.<br>
    4. پس از اتمام ترجمه، می‌توانید متن فارسی را مشاهده و با دکمه <b>دانلود ترجمه</b> ذخیره کنید.<br>
    <br>
    <b>نکته:</b> اگر ترجمه طولانی بود، کمی صبر کنید تا همه بخش‌ها ترجمه شوند.<br>
    <b>در صورت بروز خطا:</b> اتصال اینترنت و اعتبار کلیدهای API را بررسی کنید.<br>
</div>
""", unsafe_allow_html=True)
