# -*- coding: utf-8 -*-
"""
بات مشاور تحصیلی - Educational Advisor Bot
"""

import requests
import time
import pandas as pd
from datetime import datetime
import os
import shutil
import sys

# توکن بات
TOKEN = os.environ.get('BOT_TOKEN')
if TOKEN is None:
    print("ERROR: لطفا متغیر محیطی BOT_TOKEN را تنظیم کنید.")
    sys.exit(1)

URL = f"https://api.telegram.org/bot{TOKEN}/"

print("🎓 راه‌اندازی بات مشاور تحصیلی...")

users = {}
student_data = {}

# سیستم مدیریت وضعیت کاربران
class UserState:
    def __init__(self):
        self.current_action = None
        self.grade = None
        self.assessment_data = {}
        self.study_plan = {}
        self.alarms = []
        self.alarm_setup_step = 0
        self.temp_alarm_data = {}
        self.last_activity = time.time()

user_states = {}

def log_event(event_type, chat_id, details=""):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] [{event_type}] User:{chat_id} {details}"
    print(f"📝 {log_message}")
    
    try:
        with open('bot_logs.txt', 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    except:
        pass

def send_message(chat_id, text, buttons=None):
    try:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if buttons:
            data["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
        requests.post(URL + "sendMessage", json=data)
        print(f"📤 {text[:40]}...")
    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")

def get_user_state(chat_id):
    if chat_id not in user_states:
        user_states[chat_id] = UserState()
    return user_states[chat_id]

def safe_send_message(chat_id, text, buttons=None):
    try:
        send_message(chat_id, text, buttons)
        log_event("MESSAGE_SENT", chat_id, f"Text: {text[:30]}")
    except Exception as e:
        log_event("SEND_ERROR", chat_id, f"Error: {str(e)}")
        time.sleep(1)
        try:
            send_message(chat_id, "⚠️ خطای موقت، لطفاً مجدد تلاش کنید", create_main_menu())
        except:
            pass
        
def create_main_menu():
    return [
        [{"text": "📊 ارزیابی تحصیلی"}, {"text": "🎯 برنامه‌ریزی"}],
        [{"text": "⏰ آلارم مطالعه"}, {"text": "📅 برنامه هفتگی"}],
        [{"text": "📈 پیگیری پیشرفت"}, {"text": "😊 مدیریت استرس"}],
        [{"text": "📞 مشاوره تخصصی"}, {"text": "ℹ️ راهنما"}]
    ]

def show_welcome(chat_id, name):
    log_event("WELCOME_SHOWN", chat_id, f"User: {name}")
    text = f"""🌟 <b>سلام {name} عزیز!</b>

🎓 <b>به رهنمای تحصیلی خوش آمدید</b>

📚 <b>خدمات تخصصی ما برای پایه‌های ششم تا دوازدهم:</b>
• ارزیابی دقیق وضعیت تحصیلی
• برنامه‌ریزی درسی شخصی‌سازی شده
• سیستم آلارم مطالعه هوشمند
• پیگیری پیشرفت تحصیلی
• مدیریت استرس و اضطراب امتحان

👇 <b>لطفاً یکی از خدمات را انتخاب کنید:</b>"""
    
    safe_send_message(chat_id, text, create_main_menu())

# ======== سیستم ارزیابی تحصیلی ========
def show_educational_assessment(chat_id):
    log_event("ASSESSMENT_SHOWN", chat_id)
    text = """📊 <b>ارزیابی تحصیلی</b>

🎒 <b>لطفاً پایه تحصیلی خود را انتخاب کنید:</b>"""
    
    buttons = [
        [{"text": "📚 ششم"}, {"text": "📚 هفتم"}, {"text": "📚 هشتم"}],
        [{"text": "📚 نهم"}, {"text": "🎯 دهم"}, {"text": "🎯 یازدهم"}],
        [{"text": "🎯 دوازدهم"}, {"text": "🔙 بازگشت به منو"}]
    ]
    safe_send_message(chat_id, text, buttons)
       
def create_assessment_buttons():
    return [
        [{"text": "🟢 عالی"}, {"text": "🟡 متوسط"}, {"text": "🔴 ضعیف"}],
        [{"text": "🔙 بازگشت به منو"}]
    ]

def start_grade_selection(chat_id, grade):
    log_event("ASSESSMENT_STARTED", chat_id, f"Grade: {grade}")
    users[chat_id] = {
        'action': 'educational_assessment',
        'grade': grade,
        'step': 0,
        'answers': [],
        'last_activity': time.time()
    }
    
    questions = {
        "ششم": [
            "۱. وضعیت شما در درس ریاضی چگونه است؟",
            "۲. عملکردتان در علوم چطور است؟",
            "۳. وضعیت درس فارسی چگونه است؟",
            "۴. ساعت مطالعه روزانه شما چقدر است؟",
            "۵. چه مشکلاتی در یادگیری دارید؟"
        ],
        "نهم": [
            "۱. وضعیت دروس اصلی (ریاضی، علوم، فارسی) چگونه است؟",
            "۲. برای انتخاب رشته چه برنامه‌ای دارید؟",
            "۳. ساعت مطالعه روزانه چقدر است؟",
            "۴. در چه دروسی نیاز به کمک دارید؟",
            "۵. هدف تحصیلی شما چیست؟"
        ],
        "دوازدهم": [
            "۱. وضعیت دروس تخصصی چگونه است؟",
            "۲. برنامه‌ریزی کنکور دارید؟",
            "۳. ساعت مطالعه روزانه چقدر است؟",
            "۴. سطح استرس شما چقدر است؟",
            "۵. چه منابعی استفاده می‌کنید؟"
        ]
    }
    
    user_questions = questions.get(grade, questions["ششم"])
    users[chat_id]['questions'] = user_questions
    
    text = f"""📝 <b>ارزیابی تحصیلی پایه {grade}</b>

این ارزیابی {len(user_questions)} سوال دارد و وضعیت تحصیلی شما را تحلیل می‌کند.

<b>لطفاً به سوالات با دقت پاسخ دهید:</b>"""
    
    safe_send_message(chat_id, text, create_assessment_buttons())
    send_next_question(chat_id)

def send_next_question(chat_id):
    if chat_id not in users:
        return
    
    user = users[chat_id]
    if user['step'] < len(user['questions']):
        question = user['questions'][user['step']]
        text = f"<b>سوال {user['step'] + 1} از {len(user['questions'])}</b>\n\n{question}"
        safe_send_message(chat_id, text, create_assessment_buttons())
    else:
        show_assessment_results(chat_id)

def handle_assessment_answer(chat_id, answer):
    log_event("ASSESSMENT_ANSWER", chat_id, f"Answer: {answer}")
    if answer == "🔙 بازگشت به منو":
        if chat_id in users:
            del users[chat_id]
        safe_send_message(chat_id, "🔙 بازگشت به منوی اصلی", create_main_menu())
        return
    
    if chat_id not in users:
        return
    
    user = users[chat_id]
    user['last_activity'] = time.time()
    
    if answer in ["🟢 عالی", "🟡 متوسط", "🔴 ضعیف"]:
        score_map = {"🟢 عالی": 2, "🟡 متوسط": 1, "🔴 ضعیف": 0}
        user['answers'].append(score_map[answer])
        user['step'] += 1
        
        if user['step'] < len(user['questions']):
            send_next_question(chat_id)
        else:
            show_assessment_results(chat_id)

def show_assessment_results(chat_id):
    log_event("ASSESSMENT_COMPLETED", chat_id)
    if chat_id not in users:
        return
    
    user = users[chat_id]
    total_score = sum(user['answers'])
    max_score = len(user['answers']) * 2
    grade = user['grade']
    
    if total_score >= max_score * 0.8:
        status = "🟢 وضعیت عالی"
        recommendation = "شما در مسیر درستی قرار دارید. ادامه دهید!"
    elif total_score >= max_score * 0.6:
        status = "🟡 وضعیت قابل قبول"
        recommendation = "نیاز به بهبود دارید. برنامه‌ریزی بهتری نیاز است."
    else:
        status = "🔴 نیاز به توجه فوری"
        recommendation = "وضعیت بحرانی! نیاز به مشاوره تخصصی دارید."
    
    text = f"""📊 <b>نتایج ارزیابی تحصیلی</b>

🎒 <b>پایه:</b> {grade}
📈 <b>امتیاز شما:</b> {total_score} از {max_score}
📋 <b>وضعیت:</b> {status}

💡 <b>توصیه‌ها:</b>
{recommendation}

🎯 <b>قدم بعدی:</b>
برای دریافت برنامه‌ریزی شخصی، از منوی اصلی گزینه «🎯 برنامه‌ریزی» را انتخاب کنید."""

    safe_send_message(chat_id, text, create_main_menu())
    save_assessment_result(chat_id, user, total_score)
    del users[chat_id]

def save_assessment_result(chat_id, user_data, score):
    try:
        file_name = 'educational_data.xlsx'
        new_row = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': chat_id,
            'grade': user_data.get('grade', ''),
            'total_score': score,
            'answers': str(user_data.get('answers', []))
        }
        
        if os.path.exists(file_name):
            df = pd.read_excel(file_name)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])
        
        df.to_excel(file_name, index=False)
        log_event("DATA_SAVED", chat_id, "Assessment results saved")
    except Exception as e:
        log_event("SAVE_ERROR", chat_id, f"Error: {str(e)}")

# ======== سیستم برنامه‌ریزی ========
def show_study_planner(chat_id):
    log_event("PLANNER_SHOWN", chat_id)
    text = """🎯 <b>سیستم برنامه‌ریزی درسی هوشمند</b>

📊 این سیستم بر اساس:
• پایه تحصیلی شما
• سطح درسی
• زمان‌های در دسترس
• اهداف تحصیلی

برنامه‌ای شخصی‌سازی شده تولید می‌کند.

👇 لطفاً پایه تحصیلی خود را انتخاب کنید:"""
    
    buttons = [
        [{"text": "📚 ششم"}, {"text": "📚 هفتم"}, {"text": "📚 هشتم"}],
        [{"text": "📚 نهم"}, {"text": "🎯 دهم"}, {"text": "🎯 یازدهم"}],
        [{"text": "🎯 دوازدهم"}, {"text": "🔙 بازگشت به منو"}]
    ]
    safe_send_message(chat_id, text, buttons)

def create_detailed_study_plan(chat_id, grade):
    weekly_plans = {
        "ششم": {
            "title": "📅 برنامه هفتگی پایه ششم",
            "schedule": """
📋 <b>برنامه روزهای هفته:</b>
<b>شنبه:</b>
⏰ ۱۶:۰۰-۱۷:۰۰ - ریاضی
⏰ ۱۷:۳۰-۱۸:۱۵ - علوم
⏰ ۱۹:۰۰-۱۹:۴۵ - فارسی
            """,
            "recommendations": """
💡 <b>توصیه‌های تخصصی:</b>
• مطالعه روزانه ۲-۳ ساعت
• استراحت بین مطالعه
• حل تمرینات عملی
            """
        }
    }
    
    default_plan = {
        "title": f"📅 برنامه هفتگی پایه {grade}",
        "schedule": f"""
📋 <b>برنامه پیشنهادی پایه {grade}:</b>
⏰ ۱۶:۰۰-۱۷:۳۰ - دروس اصلی
⏰ ۱۸:۰۰-۱۹:۰۰ - دروس فرعی
        """,
        "recommendations": f"""
💡 <b>توصیه‌های پایه {grade}:</b>
• مطالعه منظم روزانه
• استراحت بین جلسات مطالعه
        """
    }
    
    plan = weekly_plans.get(grade, default_plan)
    text = f"{plan['title']}\n\n{plan['schedule']}\n\n{plan['recommendations']}"
    safe_send_message(chat_id, text, create_main_menu())
    log_event("DETAILED_PLAN_CREATED", chat_id, f"Grade: {grade}")

# ======== سیستم آلارم مطالعه ========
def show_alarm_system(chat_id):
    log_event("ALARM_SYSTEM", chat_id)
    text = """⏰ <b>سیستم آلارم مطالعه هوشمند</b>

🎯 <b>ویژگی‌ها:</b>
• ⏰ یادآور زمان مطالعه
• ☕ هشدار زمان استراحت

👇 لطفاً نوع سرویس مورد نیاز را انتخاب کنید:"""
    
    buttons = [
        [{"text": "⏰ تنظیم آلارم"}, {"text": "📊 عادات مطالعه"}],
        [{"text": "🔙 بازگشت به منو"}]
    ]
    safe_send_message(chat_id, text, buttons)

def start_alarm_setup(chat_id):
    user_state = get_user_state(chat_id)
    user_state.current_action = "alarm_setup"
    user_state.alarm_setup_step = 1
    user_state.temp_alarm_data = {}
    
    text = """⏰ <b>تنظیم آلارم جدید</b>
لطفاً نوع آلارم را انتخاب کنید:"""
    
    buttons = [
        [{"text": "📚 آلارم مطالعه"}, {"text": "☕ آلارم استراحت"}],
        [{"text": "🔙 بازگشت"}]
    ]
    safe_send_message(chat_id, text, buttons)

def ask_alarm_time(chat_id):
    text = """🕒 <b>زمان آلارم</b>
لطفاً زمان آلارم را انتخاب کنید:"""
    
    buttons = [
        [{"text": "۰۷:۰۰"}, {"text": "۰۸:۰۰"}, {"text": "۰۹:۰۰"}],
        [{"text": "۱۴:۰۰"}, {"text": "۱۶:۰۰"}, {"text": "۱۸:۰۰"}],
        [{"text": "🔙 بازگشت"}]
    ]
    safe_send_message(chat_id, text, buttons)

def ask_alarm_days(chat_id):
    text = """📅 <b>روزهای هفته</b>
لطفاً روزهای فعال بودن آلارم را انتخاب کنید:"""
    
    buttons = [
        [{"text": "شنبه"}, {"text": "یکشنبه"}, {"text": "دوشنبه"}],
        [{"text": "سه‌شنبه"}, {"text": "چهارشنبه"}, {"text": "پنجشنبه"}],
        [{"text": "جمعه"}, {"text": "🎯 همه روزها"}, {"text": "✅ تایید"}],
        [{"text": "🔙 بازگشت"}]
    ]
    safe_send_message(chat_id, text, buttons)

def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def handle_alarm_setup(chat_id, user_text):
    user_state = get_user_state(chat_id)
    
    if user_text == "🔙 بازگشت":
        user_state.current_action = None
        show_alarm_system(chat_id)
        return
    
    if user_state.alarm_setup_step == 1:
        alarm_types = {
            "📚 آلارم مطالعه": "study",
            "☕ آلارم استراحت": "break"
        }
        
        if user_text in alarm_types:
            user_state.temp_alarm_data['type'] = alarm_types[user_text]
            user_state.alarm_setup_step = 2
            ask_alarm_time(chat_id)
        else:
            safe_send_message(chat_id, "⚠️ لطفاً از گزینه‌های موجود انتخاب کنید.")
    
    elif user_state.alarm_setup_step == 2:
        if is_valid_time(user_text):
            user_state.temp_alarm_data['time'] = user_text
            user_state.alarm_setup_step = 3
            ask_alarm_days(chat_id)
        else:
            safe_send_message(chat_id, "⚠️ زمان نامعتبر! لطفاً از دکمه‌ها استفاده کنید.")
    
    elif user_state.alarm_setup_step == 3:
        if user_text == "✅ تایید":
            save_alarm(chat_id)
        else:
            process_alarm_days(chat_id, user_text)

def process_alarm_days(chat_id, day_text):
    user_state = get_user_state(chat_id)
    if 'days' not in user_state.temp_alarm_data:
        user_state.temp_alarm_data['days'] = []
    
    days_map = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
    if day_text in days_map and day_text not in user_state.temp_alarm_data['days']:
        user_state.temp_alarm_data['days'].append(day_text)
        selected = "، ".join(user_state.temp_alarm_data['days'])
        safe_send_message(chat_id, f"✅ روزهای انتخاب شده: {selected}")

def save_alarm(chat_id):
    user_state = get_user_state(chat_id)
    alarm_data = {
        'id': len(user_state.alarms) + 1,
        'type': user_state.temp_alarm_data.get('type', 'study'),
        'time': user_state.temp_alarm_data.get('time', '08:00'),
        'days': user_state.temp_alarm_data.get('days', ['all']),
        'active': True
    }
    
    user_state.alarms.append(alarm_data)
    text = f"""✅ <b>آلارم با موفقیت تنظیم شد</b>
• نوع: {alarm_data['type']}
• زمان: {alarm_data['time']}
• روزها: {', '.join(alarm_data['days'])}"""
    
    safe_send_message(chat_id, text, create_main_menu())
    user_state.current_action = None

def show_user_alarms(chat_id):
    user_state = get_user_state(chat_id)
    if not user_state.alarms:
        text = "⏰ شما هیچ آلارم فعالی ندارید."
    else:
        text = "⏰ <b>آلارم‌های فعال شما:</b>\n"
        for alarm in user_state.alarms:
            text += f"• {alarm['type']} - {alarm['time']}\n"
    
    safe_send_message(chat_id, text, create_main_menu())

# ======== سیستم مدیریت استرس ========
def show_stress_management(chat_id):
    log_event("STRESS_MANAGEMENT", chat_id)
    text = """😊 <b>مدیریت استرس و اضطراب</b>
لطفاً سطح استرس خود را انتخاب کنید:"""
    
    buttons = [
        [{"text": "🟢 کم"}, {"text": "🟡 متوسط"}],
        [{"text": "🟠 زیاد"}, {"text": "🔴 بسیار زیاد"}],
        [{"text": "🔙 بازگشت به منو"}]
    ]
    safe_send_message(chat_id, text, buttons)
    
    if chat_id not in users:
        users[chat_id] = {}
    users[chat_id]['action'] = 'stress_assessment'

def handle_stress_assessment(chat_id, stress_level):
    if stress_level == "🔙 بازگشت به منو":
        if chat_id in users:
            users[chat_id]['action'] = None
        show_welcome(chat_id, "کاربر")
        return
    
    responses = {
        "🟢 کم": "🟢 وضعیت عالی! ادامه دهید.",
        "🟡 متوسط": "🟡 نیاز به استراحت بیشتر دارید.",
        "🟠 زیاد": "🟠 با مشاور تماس بگیرید: 09121094069",
        "🔴 بسیار زیاد": "🔴 نیاز به مشاوره فوری دارید."
    }
    
    response = responses.get(stress_level, "⚠️ لطفاً از گزینه‌های موجود انتخاب کنید.")
    safe_send_message(chat_id, response, create_main_menu())
    
    if chat_id in users:
        users[chat_id]['action'] = None

# ======== سایر سیستم‌ها ========
def show_progress_tracking(chat_id):
    text = "📈 <b>پیگیری پیشرفت تحصیلی</b>\n\nاین سرویس به زودی فعال می‌شود..."
    safe_send_message(chat_id, text, create_main_menu())

def show_help(chat_id):
    text = """ℹ️ <b>راهنمای استفاده</b>

🎓 <b>خدمات موجود:</b>
• 📊 ارزیابی تحصیلی
• 🎯 برنامه‌ریزی درسی  
• ⏰ آلارم مطالعه
• 😊 مدیریت استرس

📞 <b>مشاوره:</b> 09121094069"""
    safe_send_message(chat_id, text, create_main_menu())

def backup_data():
    try:
        if not os.path.exists('backup'):
            os.makedirs('backup')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        print(f"✅ پشتیبان‌گیری انجام شد - {timestamp}")
    except Exception as e:
        log_event("BACKUP_ERROR", "SYSTEM", f"Error: {str(e)}")

def cleanup_old_sessions():
    try:
        current_time = time.time()
        to_remove = []
        for chat_id, user_data in users.items():
            if current_time - user_data.get('last_activity', 0) > 7200:
                to_remove.append(chat_id)
        for chat_id in to_remove:
            del users[chat_id]
    except Exception as e:
        log_event("CLEANUP_ERROR", "SYSTEM", f"خطا در پاک‌سازی: {e}")

# ======== حلقه اصلی بات ========
print("🤖 بات تحصیلی فعال شد...")
last_update_id = 0

while True:
    try:
        response = requests.get(URL + f"getUpdates?offset={last_update_id + 1}")
        data = response.json()
        
        if "result" in data:
            for update in data["result"]:
                update_id = update["update_id"]
                if update_id > last_update_id:
                    last_update_id = update_id
                    
                    if "message" in update:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"]
                        user_name = update["message"]["chat"].get("first_name", "کاربر")
                        
                        print(f"📩 {user_name}: {user_text}")
                        
                        if chat_id in users:
                            users[chat_id]['last_activity'] = time.time()
                        
                        user_state = get_user_state(chat_id)
                        
                        if chat_id in users and users[chat_id].get('action') == 'educational_assessment':
                            handle_assessment_answer(chat_id, user_text)
                        elif chat_id in users and users[chat_id].get('action') == 'stress_assessment':
                            handle_stress_assessment(chat_id, user_text)
                        elif user_state.current_action == "alarm_setup":
                            handle_alarm_setup(chat_id, user_text)
                        else:
                            if user_text == "/start":
                                show_welcome(chat_id, user_name)
                            elif user_text == "📊 ارزیابی تحصیلی":
                                show_educational_assessment(chat_id)
                            elif user_text == "🎯 برنامه‌ریزی":
                                show_study_planner(chat_id)
                            elif user_text == "⏰ آلارم مطالعه":
                                show_alarm_system(chat_id)
                            elif user_text == "⏰ تنظیم آلارم":
                                start_alarm_setup(chat_id)
                            elif user_text == "📊 عادات مطالعه":
                                show_user_alarms(chat_id)
                            elif user_text == "😊 مدیریت استرس":
                                show_stress_management(chat_id)
                            elif user_text == "📈 پیگیری پیشرفت":
                                show_progress_tracking(chat_id)
                            elif user_text in ["📚 ششم", "📚 هفتم", "📚 هشتم", "📚 نهم", "🎯 دهم", "🎯 یازدهم", "🎯 دوازدهم"]:
                                grade = user_text.split(" ")[1]
                                if chat_id in users and users[chat_id].get('action') == 'educational_assessment':
                                    start_grade_selection(chat_id, grade)
                                else:
                                    create_detailed_study_plan(chat_id, grade)
                            elif user_text == "📞 مشاوره تخصصی":
                                send_message(chat_id, "📞 برای مشاوره با شماره 09121094069 تماس بگیرید", create_main_menu())
                            elif user_text == "ℹ️ راهنما":
                                show_help(chat_id)
                            elif user_text == "🔙 بازگشت به منو":
                                show_welcome(chat_id, user_name)
                            else:
                                safe_send_message(chat_id, "⚠️ لطفاً از منوی زیر انتخاب کنید:", create_main_menu())
                        
                        time.sleep(0.5)
        
        if time.time() % 600 < 1:
            cleanup_old_sessions()
        if time.time() % 3600 < 1:
            backup_data()
        
    except Exception as e:
        print(f"⚠️ خطا: {e}")
        time.sleep(3)
