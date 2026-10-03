# build_db.py
import requests
import pandas as pd
import json
import re
from io import StringIO
from collections import Counter

SHEETS = {
    "5": "1206739171",
    "6": "261206848",
    "7": "706362656",
    "8": "1186075388",
    "9": "486305514",
    "10": "1769685584",
}

BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTs5vemsCfmbu3ZaKuxmuWSnO-gxaRWlJ3_5VgeRSS-OpVfqhC6XsJxdHgGE3bc8FQuAegu8xlOid_u/pub?output=csv&gid={}"

IGNORE_WORDS = ['нет дз', 'без дневника', 'не задано', 'нет', 'без дз', 'без д/з', 'нет дз 2', 'дз 5']
GRADE_PATTERN = re.compile(r'\b([2-5])\b')

STOP_WORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все',
    'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по',
    'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из',
    'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или',
    'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь',
    'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
    'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без',
    'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто',
    'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом',
    'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем',
    'сказать', 'всех', 'никогда', 'сегодня', 'можно', 'при', 'наконец', 'два', 'об',
    'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про',
    'всего', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо',
    'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой',
    'им', 'более', 'всегда', 'конечно', 'всю', 'между', 'стр', 'класс', 'урок',
    'написать', 'прочитать', 'выучить', 'сделать', 'задание', 'тетрадь', 'тетради',
    'учебник', 'учебника', 'вопросы', 'вопрос', 'ответить', 'дописать', 'записать',
    'выполнить', 'работа', 'работе', 'рабочая', 'рабочей', 'письменно', 'записи',
    'домашнее', 'параграф', 'параграфа', 'пункт', 'страница', 'задания',
}

WORD_PATTERN = re.compile(r'[а-яёa-z]{4,}', re.IGNORECASE)

BASE_SUBJECTS = [
    'Математика', 'Алгебра', 'Геометрия', 'Русский язык', 'Литература',
    'Английский язык', 'История', 'Обществознание', 'Физика', 'Химия',
    'Биология', 'География', 'Информатика', 'Физкультура', 'ОБЖ',
    'Музыка', 'ИЗО', 'Технология', 'ВиС', 'Проектная деятельность',
    'Классный час', 'Разг. Английский', 'Доп. Математика', 'Доп. Русский',
    'ОДНКР', 'Инд. проект', 'СП', 'Психология',
]


def normalize_subject(subj):
    if not subj:
        return None
    s = str(subj).strip()
    if '/' in s:
        return None
    lower = s.lower()
    for base in BASE_SUBJECTS:
        bl = base.lower()
        if bl == lower:
            return base
        if lower.startswith(bl[:5]) and len(lower) >= 4:
            return base
        if bl.startswith(lower[:5]) and len(bl) >= 4:
            return base
        if lower.startswith('русск') and bl == 'русский язык':
            return base
        if lower.startswith('литер') and bl == 'литература':
            return base
        if lower.startswith('англ') and bl == 'английский язык':
            return base
        if lower.startswith('матем') and bl == 'математика':
            return base
        if lower.startswith('геом') and bl == 'геометрия':
            return base
        if lower.startswith('алгеб') and bl == 'алгебра':
            return base
        if lower.startswith('истор') and bl == 'история':
            return base
        if lower.startswith('обществ') and bl == 'обществознание':
            return base
        if lower.startswith('физк') and bl == 'физкультура':
            return base
        if lower.startswith('информ') and bl == 'информатика':
            return base
        if lower.startswith('биол') and bl == 'биология':
            return base
        if lower.startswith('хим') and bl == 'химия':
            return base
        if lower.startswith('геогр') and bl == 'география':
            return base
        if lower.startswith('муз') and bl == 'музыка':
            return base
        if lower == 'изо' and bl == 'изо':
            return base
        if lower.startswith('технол') and bl == 'технология':
            return base
        if lower.startswith('проект') and bl == 'проектная деятельность':
            return base
        if lower.startswith('классн') and bl == 'классный час':
            return base
        if lower.startswith('разг') and bl == 'разг. английский':
            return base
        if lower.startswith('доп. рус') and bl == 'доп. русский':
            return base
        if lower.startswith('доп. мат') and bl == 'доп. математика':
            return base
        if lower.startswith('однкр') and bl == 'однкр':
            return base
        if lower.startswith('инд. проект') and bl == 'инд. проект':
            return base
        if lower == 'сп' and bl == 'сп':
            return base
        if lower.startswith('психол') and bl == 'психология':
            return base
    return None


def split_teachers(teacher_str):
    if not teacher_str:
        return []
    s = str(teacher_str).strip()
    if not s or s.lower() == 'nan':
        return []
    s = re.sub(r'[/,;]', ' ', s)
    pattern = re.compile(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]?\.?')
    matches = pattern.findall(s)
    result = []
    for m in matches:
        m = m.strip()
        m = re.sub(r'\s+', ' ', m)
        if not m.endswith('.'):
            m += '.'
        if len(m) >= 5:
            result.append(m)
    if not result:
        pattern2 = re.compile(r'[А-ЯЁ][а-яё]+\s*[А-ЯЁ]\.?[А-ЯЁ]?\.?')
        for m in pattern2.findall(s):
            m = m.strip()
            if len(m) >= 5:
                result.append(m)
    if not result and len(s) >= 5:
        result.append(s)
    return result


def get_teacher_key(name):
    if not name:
        return None
    s = name.strip()
    s = s.replace('3', 'З').replace('0', 'О').replace('1', 'И')
    s = re.sub(r'[.,/]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    parts = s.split()
    if len(parts) < 2:
        return s.lower()[:4]
    lastname = parts[0].lower()[:3]
    first = parts[1][0].lower() if len(parts[1]) > 0 else ''
    return f"{lastname}_{first}"


def is_date(s):
    return bool(re.match(r'\d{2}\.\d{2}\.\d{4}', s.strip()))


def extract_date(s):
    m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', s.strip())
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    return None


def parse_cell(cell_value):
    if cell_value is None or pd.isna(cell_value):
        return [], 0, 0
    s = str(cell_value).strip()
    if not s or s.lower() in ('nan', ''):
        return [], 0, 0
    grades = []
    absences = 0
    late = 0
    if re.search(r'\bн\b|\bн!|\bН\b|\bН!', s, re.IGNORECASE):
        absences = 1
    if re.search(r'\bоп\b', s, re.IGNORECASE):
        late = 1
    s_clean = s
    for word in IGNORE_WORDS:
        s_clean = s_clean.replace(word, ' ')
        s_clean = s_clean.replace(word.capitalize(), ' ')
    for match in GRADE_PATTERN.finditer(s_clean):
        grades.append(int(match.group(1)))
    return grades, absences, late


def extract_words(text):
    if not text or pd.isna(text):
        return []
    s = str(text).strip().lower()
    if not s or s == 'nan' or s in ('нет дз', 'без дз', 'нет', 'не задано', '-', 'без д/з'):
        return []
    words = WORD_PATTERN.findall(s)
    result = []
    for w in words:
        if w in STOP_WORDS:
            continue
        if len(w) < 4:
            continue
        w_norm = re.sub(r'(ые|ая|ое|ий|ый|ой|ых|ым|ом|ем|ах|ях|ов|ев|ам|ям|ами|ями|у|ю|а|я|ы|и|е|о)$', '', w)
        if len(w_norm) >= 4 and w_norm not in STOP_WORDS:
            result.append(w_norm)
    return result


def download_sheet(gid):
    url = BASE_URL.format(gid)
    print(f"[CSV] Скачиваю gid={gid}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text), header=None)
    return df


def parse_sheet(df, class_name):
    if len(df) < 2:
        return {}, {}, []

    headers = [str(x).strip() if pd.notna(x) else "" for x in df.iloc[0]]

    subject_col = None
    topic_col = None
    hw_col = None
    teacher_col = None

    for i, h in enumerate(headers):
        h_low = h.lower().strip()
        if 'предмет' in h_low and 'урок' not in h_low and subject_col is None:
            subject_col = i
        elif 'тема' in h_low and topic_col is None:
            topic_col = i
        elif ('домашн' in h_low or h_low == 'дз') and hw_col is None:
            hw_col = i
        elif ('педагог' in h_low or 'фио' in h_low or 'учитель' in h_low or 'преподав' in h_low) and teacher_col is None:
            teacher_col = i

    if subject_col is None:
        return {}, {}, []

    student_cols = []
    for i, h in enumerate(headers):
        if i in (subject_col, topic_col, hw_col, teacher_col):
            continue
        if h and h != 'nan' and 'урок' not in h.lower() and '№' not in h:
            student_cols.append((i, h))

    students = {}
    for _, name in student_cols:
        students[name] = {'grades': [], 'absences': [], 'late': []}

    teachers = {}
    homework_list = []
    current_date = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        col0 = str(row[0]).strip() if pd.notna(row[0]) else ""

        if is_date(col0):
            current_date = extract_date(col0)
            continue
        if not col0 or not col0.isdigit():
            continue
        if not current_date:
            continue

        subject = ""
        if subject_col < len(row) and pd.notna(row[subject_col]):
            subject = str(row[subject_col]).strip()
        if not subject or subject == 'nan':
            continue

        teacher = ""
        if teacher_col is not None and teacher_col < len(row):
            cell_val = row[teacher_col]
            if pd.notna(cell_val):
                teacher = str(cell_val).strip()

        hw_text = ""
        if hw_col is not None and hw_col < len(row):
            hw_val = row[hw_col]
            if pd.notna(hw_val):
                hw_text = str(hw_val).strip()

        topic_text = ""
        if topic_col is not None and topic_col < len(row):
            topic_val = row[topic_col]
            if pd.notna(topic_val):
                topic_text = str(topic_val).strip()

        homework_list.append({
            'date': current_date,
            'lesson_num': col0,
            'subject': subject,
            'subject_norm': normalize_subject(subject),
            'topic': topic_text if topic_text != 'nan' else '',
            'hw': hw_text if hw_text != 'nan' else '',
            'teacher': teacher if teacher != 'nan' else '',
        })

        teacher_list = split_teachers(teacher)

        for t in teacher_list:
            if t not in teachers:
                teachers[t] = {
                    'grades_count': 0,
                    'subjects': set(),
                    'grades_by_value': Counter(),
                    'students_by_value': {2: Counter(), 3: Counter(), 4: Counter(), 5: Counter()},
                    'homework_words': Counter(),
                }
            for w in extract_words(hw_text):
                teachers[t]['homework_words'][w] += 1

        for col_idx, name in student_cols:
            if col_idx >= len(row):
                continue
            cell = row[col_idx]
            grades, absences, late = parse_cell(cell)

            for g in grades:
                students[name]['grades'].append({
                    'date': current_date,
                    'subject': subject,
                    'value': g,
                    'raw': str(cell).strip()[:50] if pd.notna(cell) else "",
                })
                for t in teacher_list:
                    teachers[t]['grades_count'] += 1
                    teachers[t]['subjects'].add(subject)
                    teachers[t]['grades_by_value'][g] += 1
                    teachers[t]['students_by_value'][g][name] += 1

            if absences:
                students[name]['absences'].append({'date': current_date, 'subject': subject})
            if late:
                students[name]['late'].append({'date': current_date, 'subject': subject})

    teachers_out = {}
    for name, data in teachers.items():
        most_common = None
        if data['grades_by_value']:
            most_common = data['grades_by_value'].most_common(1)[0][0]

        top_students = {}
        for val in [2, 3, 4, 5]:
            counter = data['students_by_value'][val]
            top = []
            for student_name, count in counter.most_common(5):
                top.append({'name': student_name, 'count': count})
            top_students[str(val)] = top

        top_words = [{'word': w, 'count': c} for w, c in data['homework_words'].most_common(50)]

        teachers_out[name] = {
            'grades_count': data['grades_count'],
            'subjects': sorted(data['subjects']),
            'grades_by_value': {
                '2': data['grades_by_value'].get(2, 0),
                '3': data['grades_by_value'].get(3, 0),
                '4': data['grades_by_value'].get(4, 0),
                '5': data['grades_by_value'].get(5, 0),
            },
            'most_common': most_common,
            'top_students': top_students,
            'homework_words': top_words,
        }

    return students, teachers_out, homework_list


def merge_by_lastname(all_teachers):
    by_lastname = {}
    for key, data in all_teachers.items():
        best_name = max(data['names'], key=len) if data['names'] else ''
        parts = best_name.split()
        if not parts:
            continue
        lastname = parts[0].lower()[:3]
        if lastname not in by_lastname:
            by_lastname[lastname] = []
        by_lastname[lastname].append((key, data))

    merged_keys = set()
    for lastname, group in by_lastname.items():
        if len(group) <= 1:
            continue
        def score(item):
            key, data = item
            best = max(data['names'], key=len) if data['names'] else ''
            return (len(best.split()) * 1000 + data['grades_count'])
        group.sort(key=score, reverse=True)
        main_key, main_data = group[0]
        for key, data in group[1:]:
            if key == main_key or key in merged_keys:
                continue
            main_data['names'].update(data['names'])
            main_data['grades_count'] += data['grades_count']
            main_data['subjects'].update(data['subjects'])
            for k, v in data['grades_by_value'].items():
                main_data['grades_by_value'][k] += v
            for val in [2, 3, 4, 5]:
                for student_name, cnt in data['students_by_value'][val].items():
                    main_data['students_by_value'][val][student_name] += cnt
            for w, cnt in data['homework_words'].items():
                main_data['homework_words'][w] += cnt
            merged_keys.add(key)

    for key in merged_keys:
        if key in all_teachers:
            del all_teachers[key]

    return all_teachers


def calc_streak(grades):
    sorted_g = sorted(grades, key=lambda g: g['date'])
    max_s = 0
    cur = 0
    for g in sorted_g:
        if g['value'] == 5:
            cur += 1
            if cur > max_s:
                max_s = cur
        else:
            cur = 0
    return max_s if max_s >= 3 else 0


def calc_recovery(absentees, grades):
    """Вклинивание в урок: минимум 3 пропуска подряд"""
    if not absentees:
        return {'percent': 0, 'avg': 0, 'events': 0, 'history': []}

    by_subject = {}
    for a in absentees:
        norm = normalize_subject(a['subject'])
        if not norm:
            continue
        if norm not in by_subject:
            by_subject[norm] = []
        by_subject[norm].append({'date': a['date'], 'type': 'absence', 'dateObj': a['date']})

    for g in grades:
        norm = normalize_subject(g['subject'])
        if not norm:
            continue
        if norm not in by_subject:
            by_subject[norm] = []
        by_subject[norm].append({'date': g['date'], 'type': 'grade', 'value': g['value'], 'dateObj': g['date']})

    def parse(d):
        m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', d)
        if not m:
            return (0, 0, 0)
        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))

    events = []
    for subj, items in by_subject.items():
        items.sort(key=lambda x: parse(x['dateObj']))
        absent_count = 0
        first_abs = None
        for item in items:
            if item['type'] == 'absence':
                absent_count += 1
                if not first_abs:
                    first_abs = item['date']
            elif item['type'] == 'grade' and absent_count > 0:
                # Только если пропущено 3+ уроков подряд
                if absent_count >= 3:
                    events.append({
                        'subject': subj,
                        'absenceDate': first_abs,
                        'gradeDate': item['date'],
                        'grade': item['value'],
                        'missed': absent_count,
                    })
                absent_count = 0
                first_abs = None

    if not events:
        return {'percent': 0, 'avg': 0, 'events': 0, 'history': []}

    total_sum = 0
    total_count = 0
    for e in events:
        if e['grade'] == 2:
            total_sum += 2 * 2
            total_count += 2
        else:
            total_sum += e['grade']
            total_count += 1

    avg = total_sum / total_count
    percent = avg / 5 * 100

    return {'percent': round(percent, 1), 'avg': round(avg, 2), 'events': len(events), 'history': events}


def calc_relations_with_teachers(student_grades, teachers):
    if not teachers:
        return {}

    subjectToTeachers = {}
    for tname, t in teachers.items():
        for subj in t.get('subjects', []):
            norm = normalize_subject(subj)
            if not norm:
                continue
            if norm not in subjectToTeachers:
                subjectToTeachers[norm] = []
            if tname not in subjectToTeachers[norm]:
                subjectToTeachers[norm].append(tname)

    teacherGrades = {}
    for g in student_grades:
        norm = normalize_subject(g['subject'])
        if not norm:
            continue
        for t in subjectToTeachers.get(norm, []):
            if t not in teacherGrades:
                teacherGrades[t] = []
            teacherGrades[t].append(g['value'])

    result = {}
    for t, vals in teacherGrades.items():
        total = 0
        count = 0
        for v in vals:
            if v == 2:
                total += 2 * 2
                count += 2
            else:
                total += v
                count += 1
        avg = total / count
        percent = avg / 5 * 100
        result[t] = {
            'avg': round(avg, 2),
            'percent': round(percent, 1),
            'count': len(vals),
        }
    return result


def main():
    db = {'classes': {}, 'teachers': {}}
    all_teachers = {}

    for class_name, gid in SHEETS.items():
        print(f"\n=== Класс {class_name} ===")
        try:
            df = download_sheet(gid)
            students, teachers, homework_list = parse_sheet(df, class_name)

            students_out = {}
            for name, data in students.items():
                grades = [g['value'] for g in data['grades']]
                avg = sum(grades) / len(grades) if grades else 0
                students_out[name] = {
                    'grades': data['grades'],
                    'absences': data['absences'],
                    'late': data['late'],
                    'stats': {
                        'avg': round(avg, 2),
                        'count': len(grades),
                        'absences_count': len(data['absences']),
                        'late_count': len(data['late']),
                    },
                }

            db['classes'][class_name] = {
                'students': students_out,
                'homework': homework_list,
            }

            for tname, tdata in teachers.items():
                key = get_teacher_key(tname)
                if key not in all_teachers:
                    all_teachers[key] = {
                        'names': set(),
                        'grades_count': 0,
                        'subjects': set(),
                        'grades_by_value': Counter(),
                        'students_by_value': {2: Counter(), 3: Counter(), 4: Counter(), 5: Counter()},
                        'homework_words': Counter(),
                    }
                at = all_teachers[key]
                at['names'].add(tname)
                at['grades_count'] += tdata['grades_count']
                for s in tdata['subjects']:
                    at['subjects'].add(s)
                for k, v in tdata['grades_by_value'].items():
                    at['grades_by_value'][int(k)] += v
                for val in [2, 3, 4, 5]:
                    for st in tdata['top_students'].get(str(val), []):
                        at['students_by_value'][val][st['name']] += st['count']
                for w in tdata['homework_words']:
                    at['homework_words'][w['word']] += w['count']

            print(f"[{class_name}] Учеников: {len(students_out)}, ДЗ: {len(homework_list)}")
        except Exception as e:
            print(f"[!] Ошибка в {class_name}: {e}")
            import traceback
            traceback.print_exc()
            db['classes'][class_name] = {'students': {}, 'homework': []}

    all_teachers = merge_by_lastname(all_teachers)

    for key, tdata in all_teachers.items():
        best_name = max(tdata['names'], key=len)
        most_common = None
        if tdata['grades_by_value']:
            most_common = tdata['grades_by_value'].most_common(1)[0][0]
        top_students = {}
        for val in [2, 3, 4, 5]:
            counter = tdata['students_by_value'][val]
            top = [{'name': sn, 'count': c} for sn, c in counter.most_common(5)]
            top_students[str(val)] = top
        top_words = [{'word': w, 'count': c} for w, c in tdata['homework_words'].most_common(50)]

        db['teachers'][best_name] = {
            'grades_count': tdata['grades_count'],
            'subjects': sorted(tdata['subjects']),
            'grades_by_value': {
                '2': tdata['grades_by_value'].get(2, 0),
                '3': tdata['grades_by_value'].get(3, 0),
                '4': tdata['grades_by_value'].get(4, 0),
                '5': tdata['grades_by_value'].get(5, 0),
            },
            'most_common': most_common,
            'top_students': top_students,
            'homework_words': top_words,
            'aliases': sorted(tdata['names']),
        }

    print("\n=== Считаю метрики учеников ===")
    rankings = {'relation': [], 'recovery': [], 'streak': []}

    for class_name, classData in db['classes'].items():
        for student_name, sdata in classData['students'].items():
            relations = calc_relations_with_teachers(sdata['grades'], db['teachers'])
            if relations:
                avg_percent = sum(r['percent'] for r in relations.values()) / len(relations)
            else:
                avg_percent = 0

            recovery = calc_recovery(sdata['absences'], sdata['grades'])
            streak = calc_streak(sdata['grades'])

            sdata['metrics'] = {
                'relation_percent': round(avg_percent, 1),
                'recovery_percent': recovery['percent'],
                'recovery_avg': recovery['avg'],
                'recovery_events': recovery['events'],
                'recovery_history': recovery['history'],
                'streak': streak,
                'relations_by_teacher': relations,
            }

            rankings['relation'].append({
                'name': student_name, 'class': class_name, 'value': round(avg_percent, 1)
            })
            rankings['recovery'].append({
                'name': student_name, 'class': class_name, 'value': recovery['percent']
            })
            rankings['streak'].append({
                'name': student_name, 'class': class_name, 'value': streak
            })

    rankings['relation'].sort(key=lambda x: -x['value'])
    rankings['recovery'].sort(key=lambda x: -x['value'])
    rankings['streak'].sort(key=lambda x: -x['value'])

    print("\n=== Считаю топ по предметам ===")
    subject_rankings = {}

    for class_name, classData in db['classes'].items():
        for student_name, sdata in classData['students'].items():
            by_subject = {}
            for g in sdata['grades']:
                norm = normalize_subject(g['subject'])
                if not norm:
                    continue
                if norm not in by_subject:
                    by_subject[norm] = []
                by_subject[norm].append(g['value'])

            for subj, vals in by_subject.items():
                avg = sum(vals) / len(vals)
                if subj not in subject_rankings:
                    subject_rankings[subj] = []
                subject_rankings[subj].append({
                    'name': student_name,
                    'class': class_name,
                    'avg': round(avg, 2),
                    'count': len(vals),
                })

    for subj in subject_rankings:
        subject_rankings[subj].sort(key=lambda x: -x['avg'])

    rankings['subjects'] = subject_rankings
    db['rankings'] = rankings

    print(f"Предметов в топе: {len(subject_rankings)}")

    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово!")
    print(f"Классов: {len(db['classes'])}")
    print(f"Учителей: {len(db['teachers'])}")
    total_hw = sum(len(c.get('homework', [])) for c in db['classes'].values())
    print(f"Всего ДЗ: {total_hw}")


if __name__ == '__main__':
    main()
