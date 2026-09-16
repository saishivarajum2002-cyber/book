# The Instinctive Trust Skill — Sales & Automated Delivery System

A complete sales funnel, free lead capture / chapter download, and multi-attachment automated fulfillment engine for **"The Instinctive Trust Skill: How to Build Confidence, Earn Trust, and Read People — Without Becoming Someone Else"** by **Sai Shivarajuu M**.

---

## 📦 What's Inside This System

1. **Free Chapter 1 Instant Download (`/download/chapter-1`)**:
   - Anyone visiting the landing page can immediately download Chapter 1 (`The_Instinctive_Trust_Skill_Chapter_1_Free.pdf`) with one click — zero friction, no barriers.
2. **Paid $10.99 Bundle (`https://checkout.dodopayments.com/buy/...`)**:
   - Bestseller landing page featuring a 3D book cover, chapter preview, and $10.99 checkout button.
3. **5 Dedicated Daily Action Plan Workbook PDFs**:
   - Generated from scratch based on the core teachings in the book:
     - `Day_1_Workbook_Action_Plan.pdf` — Anchoring Your Baseline & Radical Predictability
     - `Day_2_Workbook_Action_Plan.pdf` — Open Demeanor & Territory Expansion
     - `Day_3_Workbook_Action_Plan.pdf` — Gesture Mastery & Calming Stress Tells
     - `Day_4_Workbook_Action_Plan.pdf` — Reading Others & Disarming Confrontation
     - `Day_5_Workbook_Action_Plan.pdf` — Somatic Rehearsal & The 30-Day Integration
     - `5_Day_Master_Workbook_Action_Plan.pdf` — Complete 5-Day combined workbook edition
4. **Automated Multi-Attachment Email Delivery (`server.js`)**:
   - Node.js Express server verifies Dodo Payments webhooks with cryptographic signatures.
   - Upon payment confirmation ($10.99), the server instantly emails the buyer:
     - 📕 **The Complete 220-Page Ebook PDF**
     - 📝 **All 5 Daily Workbook Action Plan sub-PDFs**
     - 📘 **The 5-Day Master Action Plan Workbook PDF**
   - Total attachment payload is ~7.3 MB, fitting easily within standard email attachment limits (<10MB–25MB).

---

## 🚀 Quick Start (Local Development)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your configuration:
```env
# Dodo Payments (from Dodo Dashboard > Developer > Webhooks)
DODO_WEBHOOK_KEY=whsec_your_actual_key

# Email (SMTP) - Example for Gmail App Passwords:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASS=your-16-char-app-password
FROM_EMAIL="Sai Shivarajuu M" <youremail@gmail.com>

BOOK_TITLE=The Instinctive Trust Skill
AUTHOR_NAME=Sai Shivarajuu M
PORT=3000
```

### 3. Start the Server
```bash
npm start
```
Visit:
- **Landing Page**: [http://localhost:3000](http://localhost:3000)
- **Free Chapter 1 Download**: [http://localhost:3000/download/chapter-1](http://localhost:3000/download/chapter-1)
- **System Health**: [http://localhost:3000/api/health](http://localhost:3000/api/health)

---

## 🛠️ Generating & Customizing the Workbook PDFs

The 5-day action plan PDFs and master workbook are generated using Python & ReportLab.

To regenerate the PDFs at any time:
```bash
npm run build:workbooks
```
Or directly:
```bash
python generate_workbooks.py
```
All PDFs will be generated directly into `products/workbooks/`.

---

## 🧪 Testing Email Delivery (Without Live Payment)

You don't need to swipe a credit card to test your email delivery! Once your SMTP settings are configured in `.env`, trigger a test delivery directly to your inbox:

```bash
curl -X POST http://localhost:3000/api/test-delivery \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@example.com", "name": "Sai Shivarajuu"}'
```
This will compile and send all 7 PDFs (Ebook + 5 Daily Action Plans + Master Workbook) to your inbox.

---

## 💳 Connecting Dodo Payments

1. **Create Product in Dodo**:
   - Go to Dodo Payments Dashboard → **Products** → **Create Product**.
   - Title: *The Instinctive Trust Skill + 5-Day Action Plan*.
   - Price: **$10.99** (One-time payment).
   - Copy the Product ID (`p_...`).
2. **Update Product ID in Landing Page**:
   - Open `public/index.html` and update `const DODO_PRODUCT_ID = "your_actual_product_id";`.
3. **Configure Webhook**:
   - Go to Dodo Dashboard → **Developer** → **Webhooks** → **Add Webhook Endpoint**.
   - URL: `https://YOUR-DEPLOYED-DOMAIN.com/webhook/dodo`
   - Select events: `payment.succeeded` and `checkout.session.completed`.
   - Copy the **Signing Secret** into `.env` as `DODO_WEBHOOK_KEY`.

---

## 🌐 Deployment (Render, Railway, Fly.io)

This server is standard Node.js:
1. Push this repository to GitHub or GitLab.
2. In **Render** or **Railway**, create a new Web Service pointing to your repo.
3. Build Command: `npm install && npm run build:workbooks`
4. Start Command: `npm start`
5. Add your environment variables (`SMTP_*`, `DODO_WEBHOOK_KEY`) in the host dashboard.
