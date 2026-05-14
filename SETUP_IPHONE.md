# دليل إعداد جوال أمي ـ خطوة بخطوة

**الوقت:** ~25 دقيقة جلسة وحدة على جوالها
**النتيجة:** أذان تلقائي كامل، 5 مرات يومياً، يتحدّث ذاتياً كل ليلة

**البيانات المصدر:** Tower Hamlets London — `https://mhmdlubbad.github.io/adhan/prayer_times_by_date.json`

---

## نظرة عامة (6 مراحل)

| # | المرحلة | وقت |
|---|---|---|
| 1 | نقل ملف الأذان لـ iCloud Drive | 3 دقايق |
| 2 | إنشاء 5 منبهات (Clock app) | 5 دقايق |
| 3 | Shortcut "Play Adhan" | 2 دقيقة |
| 4 | Shortcut "Update Adhan Alarms" | 10 دقايق |
| 5 | 6 Automations | 5 دقايق |
| 6 | تجربة | دقيقتين |

---

## Phase 1 ـ نقل ملف الأذان

**على جهازك (Mac):**
1. افتح Finder → روح على `~/adhan/`
2. اضغط right-click على `adhan.mp3` → Share → AirDrop → اختار جوال أمك

**على جوالها:**
3. لما يجي إشعار "Accept" → اضغطي Accept
4. لما يفتح خيار "Open with..." → اختاري **Files**
5. في تطبيق Files: اضغطي **Save to Files** → روحي على **iCloud Drive** → اضغطي **Save** بأعلى

الآن الملف محفوظ في `iCloud Drive/adhan.mp3`

---

## Phase 2 ـ إنشاء 5 منبهات في تطبيق Clock

افتحي تطبيق **Clock**.

### المنبه الأول: Fajr

1. اضغطي tab **Alarm** بأسفل
2. اضغطي **+** بأعلى يمين
3. حركي العجلات لـ **6:00 AM**
4. اضغطي **Label** → امسحي → اكتبي `Fajr` → Done
5. اضغطي **Sound** → اسحبي للأعلى → **None** → Back
6. اضغطي **Save**

### كرّري للباقي:

| Label | Time |
|---|---|
| `Dhuhr` | 1:00 PM |
| `Asr` | 5:00 PM |
| `Maghrib` | 8:00 PM |
| `Isha` | 10:00 PM |

> **مهم:** Labels حساسة للأحرف. اكتبيها بالضبط زي ما هي. الأوقات مؤقتة.

---

## Phase 3 ـ Shortcut "Play Adhan"

افتحي تطبيق **Shortcuts**.

1. tab **Shortcuts** بأسفل
2. **+** بأعلى يمين
3. اضغطي على اسم الـ Shortcut بأعلى → اكتبي `Play Adhan` → Done
4. **Add Action**
5. ابحثي: `get file`
6. اضغطي **Get File**
7. **Service** → **iCloud Drive**
8. **Show File Picker** = OFF
9. **Path** → Choose → اختاري `adhan.mp3` → Open
10. **Add Action**
11. ابحثي: `play sound`
12. اضغطي **Play Sound**
13. **Done**

**اختبار:** اضغطي على Play Adhan في القائمة. لازم تسمعي الأذان.

---

## Phase 4 ـ Shortcut "Update Adhan Alarms"

1. **+** بأعلى → سمي: `Update Adhan Alarms`

### Actions 1 + 2: تحميل البيانات

2. **Add Action** → ابحثي `url` → **URL**
3. الصقي:
   ```
   https://mhmdlubbad.github.io/adhan/prayer_times_by_date.json
   ```
4. **Add Action** → ابحثي `get contents` → **Get Contents of URL**

### Action 3: تحويل JSON

5. **Add Action** → ابحثي `dictionary` → **Get Dictionary from Input**

### Action 4: تنسيق تاريخ اليوم

6. **Add Action** → ابحثي `format date` → **Format Date**
7. **Date** → اختاري **Current Date**
8. **Date Format** → **Custom**
9. **Custom Format** → اكتبي بالضبط: `yyyy-MM-dd`

### Action 5: استخراج بيانات اليوم

10. **Add Action** → ابحثي `dictionary value` → **Get Dictionary Value**
11. **Get** = Value
12. **for** = اضغطي → اختاري magic variable **Formatted Date**
13. **in** = magic variable **Dictionary**

### Action 6: استخراج وقت الفجر

14. **Add Action** → **Get Dictionary Value**
15. **Get** = Value
16. **for** = اكتبي يدوياً: `Fajr`
17. **in** = magic variable **Dictionary Value** (السابقة)

### Action 7 + 8 + 9: حذف منبه الفجر القديم وإنشاء جديد

18. **Add Action** → ابحثي `find alarm` → **Find Alarms**
19. اضغطي **Filter** → ضيفي شرط: `Label` `is` `Fajr`
20. **Add Action** → ابحثي `remove alarm` → **Remove Alarm**
    - Magic variable: Find Alarms output
21. **Add Action** → ابحثي `create alarm` → **Create Alarm**
    - **Time** = magic variable **Dictionary Value** (من step 17)
    - **Label** = `Fajr`
    - **Sound** = None (لو الخيار موجود)
    - **Snooze** = Off

### كرّري Actions 6+7+8+9 لباقي الصلوات

3 actions لكل صلاة، 12 action إضافية:

| الصلاة | Get Dict Value key | Find Alarms label | Create Alarm Label |
|---|---|---|---|
| Dhuhr | `Dhuhr` | `Dhuhr` | `Dhuhr` |
| Asr | `Asr` | `Asr` | `Asr` |
| Maghrib | `Maghrib` | `Maghrib` | `Maghrib` |
| Isha | `Isha` | `Isha` | `Isha` |

اضغطي **Done**.

### اختبار

اشغلي Update Adhan Alarms. روحي على Clock → Alarm. لازم تشوفي أوقات اليوم.

---

## Phase 5 ـ Automations (6 automations)

tab **Automation** بأسفل.

### Automation 1: تحديث يومي

1. **+** → **Create Personal Automation**
2. **Time of Day**
3. **2:00 AM** → **Daily**
4. **Next**
5. **Add Action** → ابحثي `run shortcut` → **Run Shortcut**
6. **Shortcut** → **Update Adhan Alarms**
7. **Next**
8. **Run Immediately** = ON
9. **Notify When Run** = OFF
10. **Done**

### Automations 2-6: تشغيل الأذان عند رنين المنبه

كرري 5 مرات:

1. **+** → **Create Personal Automation**
2. اسحبي للأسفل → **Alarm**
3. **Is Stopped**
4. **Alarm** → اختاري الصلاة (Fajr في الأولى، Dhuhr في الثانية، إلخ)
5. **Next**
6. **Add Action** → **Run Shortcut**
7. اختاري **Play Adhan**
8. **Next**
9. **Run Immediately** = ON
10. **Done**

---

## Phase 6 ـ التجربة

1. Clock → Alarm → **Edit** → غيّري وقت **Fajr** للآن + دقيقتين → Save
2. ضعي الجوال، رفعي الصوت
3. انتظري ـ لازم تسمعي الأذان كامل
4. شغلي **Update Adhan Alarms** يدوياً عشان يرجع الوقت الصحيح

---

## مشاكل وحلولها

| المشكلة | الحل |
|---|---|
| Update بطلع error | تأكدي من الـ URL، تنسيق `yyyy-MM-dd` |
| الأوقات ما اتغيرت | اشغلي Update يدوياً، شوفي شو طلع |
| الأذان ما اشتغل | Run Immediately = ON في الـ automation |
| الأذان اشتغل مرتين | تأكدي من 5 alarm automations فقط، مش أكثر |
| automation بسأل كل مرة | Run Immediately = ON |

---

## تحديث 2027

عند نهاية 2026 على جهازك:
```bash
cd ~/adhan
python3 refresh_data.py 2027 --append
git add prayer_times.json prayer_times.csv prayer_times_by_date.json
git commit -m "2027 prayer times"
git push
```

الـ Pages تتحدث خلال دقيقة. مفش تغيير على جوال أمك.
