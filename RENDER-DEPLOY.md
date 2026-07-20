# 🚀 Easiest Zero Investment Deploy Guide
## Render.com — Free, No Credit Card, Auto-deploy from GitHub

---

## কেন Render?

```
✅ সম্পূর্ণ ফ্রি (no credit card)
✅ GitHub থেকে auto-deploy
✅ 24/7 bot running
✅ Environment variables support
✅ Easy setup (5 মিনিট)
```

---

## ধাপ ১: Render Account তৈরি (2 মিনিট)

```
১. যান: https://render.com
২. "Get Started for Free" ক্লিক
৩. "GitHub" দিয়ে sign up করুন
৪. GitHub authorize করুন
৫. ✅ Account ready!
```

## ধাপ ২: Web Service তৈরি (3 মিনিট)

```
১. Dashboard এ যান
২. "New +" ক্লিক (উপরে ডানদিকে)
৩. "Web Service" ক্লিক
৪. "Connect a repository" ক্লিক
৫. "betvortex-bot" repo সিলেক্ট করুন
৬. "Connect" ক্লিক
```

## ধাপ ৩: Settings সেট করুন

```
Name: betvortex-bot
Region: Singapore (বা nearest)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python bot.py
Instance Type: Free
```

## ধাপ ৪: Environment Variables সেট করুন

```
"Environment" ট্যাব ক্লিক করুন
"Add Environment Variable" ক্লিক করুন
একে একে যোগ করুন:

Key: BOT_TOKEN
Value: (আপনার পুরো bot token - @BotFather থেকে)

Key: SUPABASE_URL
Value: (আপনার Supabase project URL)
Example: https://abcdefghij.supabase.co

Key: SUPABASE_KEY
Value: (আপনার Supabase anon key)
Example: eyJhbGciOiJIUzI1NiIs...

Key: ADMIN_ID
Value: (আপনার Telegram User ID)
```

## ধাপ ৫: Deploy করুন

```
১. "Create Web Service" ক্লিক করুন
২. Deploy শুরু হবে!
৩. 2-3 মিনিট অপেক্ষা করুন
৪. Logs এ দেখুন:

   ✅ "🎰 BetVortex Casino Bot is running!" = SUCCESS!
   ❌ Error = Variables check করুন
```

## ধাপ ৬: Bot Test করুন

```
১. Telegram এ যান
২. @BetVortexCasinoBot খুঁজুন
৩. START চাপুন
৪. /start পাঠান

🎉 কাজ করলে LIVE!
```

---

## ⚠️ Render Free Tier Limitations

```
• 15 মিনিট inactivity এ sleep যায়
• প্রথম request এ 30-60 সেকেন্ড delay
• এটা bot এর জন্য problem না (polling mode)

সমাধান:
• Bot polling mode এ চলবে (auto-wake)
• UptimeRobot দিয়ে ping করতে পারেন (optional)
```

---

## 🔄 Alternative: Replit (আরও সহজ)

```
যদি Render না চালে, Replit ব্যবহার করুন:

১. যান: https://replit.com
২. GitHub দিয়ে sign up
৩. "Create Repl" → "Import from GitHub"
৪. betvortex-bot repo select
৫. Run করুন

✅ আরও সহজ!
```

---

## 📋 তুলনা

| Platform | Free | Credit Card | Ease | Bot Support |
|----------|------|-------------|------|-------------|
| Render | ✅ | ❌ লাগবে না | ⭐⭐⭐⭐⭐ | ✅ Great |
| Replit | ✅ | ❌ লাগবে না | ⭐⭐⭐⭐⭐ | ✅ Good |
| Railway | ✅ | ⚠️ লাগে | ⭐⭐⭐⭐ | ✅ Great |
| Vercel | ✅ | ❌ লাগবে না | ⭐⭐⭐ | ⚠️ Webhook only |
| Fly.io | ✅ | ⚠️ লাগে | ⭐⭐⭐ | ✅ Great |

---

## 🎯 Recommendation

```
সবচেয়ে সহজ: Render.com
├── ফ্রি ✅
├── No credit card ✅
├── GitHub auto-deploy ✅
├── 24/7 bot running ✅
└── 5 মিনিট setup ✅
```
