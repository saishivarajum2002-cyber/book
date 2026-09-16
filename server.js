require("dotenv").config();
const express = require("express");
const path = require("path");
const fs = require("fs");
const nodemailer = require("nodemailer");
const { Webhook } = require("standardwebhooks");

const app = express();
const PORT = process.env.PORT || 3000;

// --- Config from environment ---
const DODO_WEBHOOK_KEY = process.env.DODO_WEBHOOK_KEY;
const SMTP_HOST = process.env.SMTP_HOST;
const SMTP_PORT = Number(process.env.SMTP_PORT || 587);
const SMTP_USER = process.env.SMTP_USER;
const SMTP_PASS = process.env.SMTP_PASS;
const FROM_EMAIL = process.env.FROM_EMAIL || SMTP_USER || "books@theinstinctivetrust.com";
const BOOK_TITLE = process.env.BOOK_TITLE || "The Instinctive Trust Skill";
const AUTHOR_NAME = process.env.AUTHOR_NAME || "Sai Shivarajuu M";

// Paths
const PUBLIC_DIR = path.join(__dirname, "public");
const PRODUCTS_DIR = path.join(__dirname, "products");
const WORKBOOKS_DIR = path.join(PRODUCTS_DIR, "workbooks");
const CHAPTER_1_PATH = path.join(PUBLIC_DIR, "downloads", "The_Instinctive_Trust_Skill_Chapter_1.pdf");
const EBOOK_PATH = path.join(PRODUCTS_DIR, "The_Instinctive_Trust_Skill_EBOOK.pdf");

if (!DODO_WEBHOOK_KEY) {
  console.warn("\x1b[33m%s\x1b[0m", "[WARN] DODO_WEBHOOK_KEY is not set in .env. Live webhook verification will fail until set.");
}

const webhook = new Webhook(DODO_WEBHOOK_KEY || "whsec_placeholder");

// Configure Transporter (supports mock mode if credentials not yet added)
const isSmtpConfigured = Boolean(SMTP_HOST && SMTP_USER && SMTP_PASS);

const mailer = isSmtpConfigured
  ? nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT,
      secure: SMTP_PORT === 465,
      auth: { user: SMTP_USER, pass: SMTP_PASS },
    })
  : null;

// Ledger of processed payment IDs to prevent duplicate sends on webhook retries
const processedPaymentIds = new Set();

// 1. Raw Webhook route (MUST come before any body parsers)
app.post(
  "/webhook/dodo",
  express.raw({ type: "*/*" }),
  async (req, res) => {
    let rawBody;
    try {
      rawBody = req.body.toString("utf8");
    } catch (err) {
      return res.status(400).send("Invalid body encoding");
    }

    const webhookHeaders = {
      "webhook-id": req.header("webhook-id") || "",
      "webhook-signature": req.header("webhook-signature") || "",
      "webhook-timestamp": req.header("webhook-timestamp") || "",
    };

    let payload;
    try {
      await webhook.verify(rawBody, webhookHeaders);
      payload = JSON.parse(rawBody);
    } catch (err) {
      console.error("[Webhook Error] Signature verification failed:", err.message);
      return res.status(401).send("Invalid signature");
    }

    // Acknowledge receipt immediately so Dodo doesn't retry
    res.status(200).send("ok");

    try {
      await handleDodoEvent(payload);
    } catch (err) {
      console.error("[Webhook Error] Error processing payload:", err);
    }
  }
);

// 2. Body parser for regular JSON & URL-encoded routes
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 3. Serve static frontend assets
app.use(express.static(PUBLIC_DIR));

// 4. Instant Free Chapter 1 Download Route
app.get("/download/chapter-1", (req, res) => {
  if (!fs.existsSync(CHAPTER_1_PATH)) {
    return res.status(404).send("Chapter 1 file is being prepared. Please check back shortly.");
  }
  
  res.download(
    CHAPTER_1_PATH,
    "The_Instinctive_Trust_Skill_Chapter_1_Free.pdf",
    (err) => {
      if (err) {
        console.error("Error downloading Chapter 1:", err);
      } else {
        console.log(`[Free Download] Chapter 1 downloaded by ${req.ip} at ${new Date().toISOString()}`);
      }
    }
  );
});

// 5. System Health Check
app.get("/api/health", (req, res) => {
  const status = {
    server: "running",
    ebookFound: fs.existsSync(EBOOK_PATH),
    chapter1Found: fs.existsSync(CHAPTER_1_PATH),
    workbooksFound: [1, 2, 3, 4, 5].every((d) =>
      fs.existsSync(path.join(WORKBOOKS_DIR, `Day_${d}_Workbook_Action_Plan.pdf`))
    ),
    masterWorkbookFound: fs.existsSync(path.join(WORKBOOKS_DIR, "5_Day_Master_Workbook_Action_Plan.pdf")),
    smtpConfigured: isSmtpConfigured,
    dodoWebhookKeyConfigured: Boolean(DODO_WEBHOOK_KEY && DODO_WEBHOOK_KEY !== "whsec_xxxxxxxxxxxxxxxxxxxx")
  };
  res.json(status);
});

// 6. Test Email Delivery Route (Use this to verify your SMTP setup safely)
app.post("/api/test-delivery", async (req, res) => {
  const targetEmail = req.body.email || req.query.email;
  const targetName = req.body.name || req.query.name || "Test Reader";

  if (!targetEmail) {
    return res.status(400).json({ error: "Please provide an email address in the body: { email: 'your@email.com' }" });
  }

  if (!isSmtpConfigured) {
    return res.status(503).json({
      error: "SMTP credentials not configured in .env yet. Please fill SMTP_HOST, SMTP_USER, SMTP_PASS."
    });
  }

  try {
    const result = await sendBookPackage(targetEmail, targetName, "TEST-MANUAL-DELIVERY");
    res.json({
      success: true,
      message: `Complete book package (Ebook + 5 Daily Action Plans) sent to ${targetEmail}`,
      details: result
    });
  } catch (err) {
    console.error("Manual test delivery failed:", err);
    res.status(500).json({ error: "Failed to send email", details: err.message });
  }
});

// --- Core Payment & Delivery Handlers ---

async function handleDodoEvent(payload) {
  const eventType = payload.type;
  const data = payload.data || {};

  const isSuccessfulPayment =
    eventType === "payment.succeeded" ||
    eventType === "checkout.session.completed" ||
    data.status === "succeeded";

  if (!isSuccessfulPayment) {
    console.log(`[Dodo Webhook] Event ignored: ${eventType}`);
    return;
  }

  const paymentId = data.payment_id || data.id || `order_${Date.now()}`;
  const customerEmail = data.customer?.email || data.customer_email;
  const customerName = data.customer?.name || "Reader";

  if (!customerEmail) {
    console.error("[Dodo Webhook] No customer email in payload:", data);
    return;
  }

  if (processedPaymentIds.has(paymentId)) {
    console.log(`[Dodo Webhook] Payment ${paymentId} already fulfilled. Skipping.`);
    return;
  }

  console.log(`[Dodo Webhook] Valid purchase confirmed for ${customerEmail} ($10.99). Dispatching book package...`);
  await sendBookPackage(customerEmail, customerName, paymentId);
  processedPaymentIds.add(paymentId);
}

async function sendBookPackage(toEmail, customerName, paymentId) {
  if (!isSmtpConfigured) {
    console.warn(`[Mock Mode] Email delivery simulated for ${toEmail}. Configure .env SMTP settings to send real emails.`);
    return { mock: true, recipient: toEmail };
  }

  // Compile all 6 attachments
  const attachments = [];

  // 1. Full Ebook
  if (fs.existsSync(EBOOK_PATH)) {
    attachments.push({
      filename: `${BOOK_TITLE} - Complete Ebook.pdf`,
      path: EBOOK_PATH,
    });
  } else {
    console.error(`Missing ebook file at: ${EBOOK_PATH}`);
  }

  // 2. Day 1 through Day 5 Action Plan Workbook sub-PDFs
  for (let day = 1; day <= 5; day++) {
    const wbPath = path.join(WORKBOOKS_DIR, `Day_${day}_Workbook_Action_Plan.pdf`);
    if (fs.existsSync(wbPath)) {
      attachments.push({
        filename: `Day_${day}_Action_Plan_Workbook.pdf`,
        path: wbPath,
      });
    }
  }

  // 3. Combined Master 5-Day Workbook
  const masterPath = path.join(WORKBOOKS_DIR, "5_Day_Master_Workbook_Action_Plan.pdf");
  if (fs.existsSync(masterPath)) {
    attachments.push({
      filename: "5_Day_Master_Workbook_Action_Plan.pdf",
      path: masterPath,
    });
  }

  const mailOptions = {
    from: `"${AUTHOR_NAME}" <${FROM_EMAIL}>`,
    to: toEmail,
    subject: `Your Copy of "${BOOK_TITLE}" + 5-Day Action Plan Workbooks`,
    text: `Hi ${customerName},\n\n` +
      `Thank you for purchasing "${BOOK_TITLE}"!\n\n` +
      `Your complete package is attached to this email:\n` +
      `• The Complete 220-Page Ebook: "${BOOK_TITLE}"\n` +
      `• Day 1 Workbook: Anchoring Your Baseline & Radical Predictability\n` +
      `• Day 2 Workbook: Open Demeanor & Territory Expansion\n` +
      `• Day 3 Workbook: Gesture Mastery & Calming Stress Tells\n` +
      `• Day 4 Workbook: Reading Others & Disarming Confrontation\n` +
      `• Day 5 Workbook: Somatic Rehearsal & The 30-Day Integration\n` +
      `• The Complete 5-Day Master Action Plan Workbook\n\n` +
      `HOW TO BEGIN:\n` +
      `1. Read Part I to understand why confidence is radical predictability.\n` +
      `2. Print out or save the Day 1 Workbook and execute the 3-Second Threshold Pause.\n` +
      `3. Complete one daily action worksheet every day this week.\n\n` +
      `If you have any questions or feedback along the way, simply hit reply to this email.\n\n` +
      `Warm regards,\n` +
      `${AUTHOR_NAME}`,
    html: `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1c1a17; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2ddd3; border-radius: 8px; background: #faf8f5;">
        <div style="border-bottom: 2px solid #a87432; padding-bottom: 15px; margin-bottom: 20px;">
          <span style="font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #a87432; font-weight: bold;">Official Delivery</span>
          <h1 style="font-size: 24px; margin: 5px 0 0 0; color: #16202c; font-family: Georgia, serif;">${BOOK_TITLE}</h1>
          <p style="margin: 4px 0 0 0; font-size: 13px; color: #666;">By ${AUTHOR_NAME}</p>
        </div>

        <p>Hi <strong>${customerName}</strong>,</p>
        <p>Thank you for your purchase! Your complete book package and action plan workbooks are attached directly to this email.</p>

        <div style="background: #ffffff; border: 1px solid #e0d8c8; border-radius: 6px; padding: 16px; margin: 20px 0;">
          <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #16202c;">📦 What is attached in this email:</h3>
          <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #333;">
            <li style="margin-bottom: 6px;"><strong>The Complete Ebook (220 Pages)</strong> — Full PDF edition</li>
            <li style="margin-bottom: 6px;"><strong>Day 1 Action Plan</strong> — Anchoring Your Baseline & Radical Predictability</li>
            <li style="margin-bottom: 6px;"><strong>Day 2 Action Plan</strong> — Open Demeanor & Territory Expansion</li>
            <li style="margin-bottom: 6px;"><strong>Day 3 Action Plan</strong> — Gesture Mastery & Calming Stress Tells</li>
            <li style="margin-bottom: 6px;"><strong>Day 4 Action Plan</strong> — Reading Others & Disarming Confrontation</li>
            <li style="margin-bottom: 6px;"><strong>Day 5 Action Plan</strong> — Somatic Rehearsal & The 30-Day Integration</li>
            <li><strong>5-Day Master Action Plan Workbook</strong> — Combined printable edition</li>
          </ul>
        </div>

        <h3 style="font-size: 15px; color: #16202c; margin-top: 25px;">🚀 Recommended Next Step:</h3>
        <p style="font-size: 14px; color: #444;">
          Start with <strong>Day 1 Workbook</strong> today. Execute the <em>3-Second Threshold Pause</em> every time you enter a room or meeting. Notice how immediately your presence shifts.
        </p>

        <p style="font-size: 13px; color: #777; margin-top: 30px; border-top: 1px solid #e2ddd3; padding-top: 15px;">
          Need help or didn't receive an attachment? Reply directly to this email and our team will assist you immediately.<br/>
          Order ID: <code style="background: #eee; padding: 2px 4px; border-radius: 3px;">${paymentId}</code>
        </p>
      </div>
    `,
    attachments,
  };

  const info = await mailer.sendMail(mailOptions);
  console.log(`[Email Delivered] Successfully sent to ${toEmail}. Message ID: ${info.messageId}`);
  return info;
}

app.listen(PORT, () => {
  console.log(`\n=================================================`);
  console.log(`  "${BOOK_TITLE}" Sales & Delivery Server`);
  console.log(`  Author: ${AUTHOR_NAME}`);
  console.log(`  Server live at: http://localhost:${PORT}`);
  console.log(`  Free Chapter 1: http://localhost:${PORT}/download/chapter-1`);
  console.log(`  Health Check:   http://localhost:${PORT}/api/health`);
  console.log(`=================================================\n`);
});
