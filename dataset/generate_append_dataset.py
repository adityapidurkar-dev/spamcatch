import csv
import random
import re
import string
from collections import OrderedDict
from pathlib import Path

random.seed(20260330)

dataset_path = Path(r"c:\Users\graceharper\Desktop\AIProject\dataset\spam.csv")
if not dataset_path.exists():
    raise FileNotFoundError(f"Missing dataset file: {dataset_path}")

url_regex = re.compile(
    r"(https?://[^\s,]+|(?:bit\.ly|tinyurl\.com|t\.co|rb\.gy|rebrand\.ly)/[^\s,]+|www\.[^\s,]+)",
    re.IGNORECASE,
)


def has_url(text: str) -> bool:
    return bool(url_regex.search(text or ""))


existing_total = 0
existing_spam = 0
existing_ham = 0
existing_url_rows = 0

with dataset_path.open("r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_total += 1
        label = (row.get("label") or "").strip().lower()
        if label == "spam":
            existing_spam += 1
        elif label == "ham":
            existing_ham += 1
        if has_url(f"{row.get('subject', '')} {row.get('body', '')}"):
            existing_url_rows += 1

target_total = 90000
target_spam_total = target_total // 2
target_ham_total = target_total - target_spam_total

if existing_total >= target_total:
    print(
        f"No append needed: existing rows={existing_total}, which is already >= {target_total}."
    )
    raise SystemExit(0)

rows_to_add = target_total - existing_total

add_spam = max(target_spam_total - existing_spam, 0)
add_ham = max(target_ham_total - existing_ham, 0)

missing = rows_to_add - (add_spam + add_ham)
if missing > 0:
    for _ in range(missing):
        if (existing_spam + add_spam) <= (existing_ham + add_ham):
            add_spam += 1
        else:
            add_ham += 1
elif missing < 0:
    trim = -missing
    while trim > 0 and (add_spam > 0 or add_ham > 0):
        if add_spam >= add_ham and add_spam > 0:
            add_spam -= 1
        elif add_ham > 0:
            add_ham -= 1
        trim -= 1

if add_spam + add_ham != rows_to_add:
    raise RuntimeError("Failed to reconcile append counts.")

target_url_total = int(round(0.40 * target_total))
add_url_total = max(min(target_url_total - existing_url_rows, rows_to_add), 0)

spam_url_target = min(int(round(add_url_total * 0.68)), add_spam)
ham_url_target = min(add_url_total - spam_url_target, add_ham)
leftover_urls = add_url_total - (spam_url_target + ham_url_target)
if leftover_urls > 0:
    extra_spam = min(leftover_urls, add_spam - spam_url_target)
    spam_url_target += extra_spam
    leftover_urls -= extra_spam
if leftover_urls > 0:
    extra_ham = min(leftover_urls, add_ham - ham_url_target)
    ham_url_target += extra_ham
    leftover_urls -= extra_ham

if spam_url_target + ham_url_target != add_url_total:
    raise RuntimeError("Failed to reconcile URL targets.")


def allocate_counts(total: int, weights: OrderedDict) -> dict:
    keys = list(weights.keys())
    raw = [total * weights[k] for k in keys]
    base = [int(v) for v in raw]
    rem = total - sum(base)
    frac_order = sorted(
        [(raw[i] - base[i], i) for i in range(len(keys))], reverse=True
    )
    for i in range(rem):
        base[frac_order[i % len(keys)][1]] += 1
    return {keys[i]: base[i] for i in range(len(keys))}


spam_category_weights = OrderedDict(
    [
        ("phishing", 0.20),
        ("job_scams", 0.14),
        ("impersonation", 0.14),
        ("financial_investment", 0.16),
        ("bec", 0.14),
        ("delivery_service", 0.12),
        ("social_engineering", 0.10),
    ]
)
ham_category_weights = OrderedDict(
    [
        ("workplace", 0.30),
        ("meeting", 0.20),
        ("academic", 0.20),
        ("friendly", 0.15),
        ("newsletter", 0.15),
    ]
)

spam_category_remaining = allocate_counts(add_spam, spam_category_weights)
ham_category_remaining = allocate_counts(add_ham, ham_category_weights)


def pick_category(counter: dict) -> str:
    total = sum(counter.values())
    if total <= 0:
        return next(iter(counter.keys()))
    r = random.randint(1, total)
    running = 0
    for k, v in counter.items():
        running += v
        if r <= running:
            counter[k] -= 1
            return k
    k = next(iter(counter.keys()))
    counter[k] -= 1
    return k


def should_include_url(rows_left: int, urls_left: int) -> bool:
    if urls_left <= 0:
        return False
    if urls_left >= rows_left:
        return True
    return random.random() < (urls_left / rows_left)


first_names = [
    "Alex", "Jordan", "Taylor", "Morgan", "Avery", "Riley", "Casey", "Jamie", "Drew", "Robin",
    "Parker", "Cameron", "Quinn", "Skyler", "Reese", "Kai", "Dakota", "Emerson", "Blake", "Finley",
]
last_names = [
    "Nguyen", "Patel", "Kim", "Lopez", "Martin", "Shaw", "Turner", "Reed", "Brooks", "Diaz",
    "Morris", "Foster", "Powell", "Bailey", "Hayes", "Perry", "Bennett", "Ward", "Price", "Ramos",
]
cities = [
    "Chicago", "Austin", "Seattle", "Denver", "Boston", "Atlanta", "Phoenix", "Dallas", "San Diego", "Portland",
    "Toronto", "Dublin", "Singapore", "Warsaw", "Berlin", "Prague", "Lisbon", "Melbourne",
]

companies = [
    "Northfield Analytics", "Pioneer Cloud", "Harborline Systems", "Meridian Logistics", "Crestview Labs",
    "BrightCore Media", "BlueRidge Ventures", "SummitOak Partners", "Helios Retail Group", "Granite Peak Finance",
]
platforms = ["LinkedIn", "Indeed", "ZipRecruiter", "TalentHub", "CareerBuilder"]
roles = [
    "Data Entry Assistant", "Operations Coordinator", "Customer Support Associate", "Payment Processing Clerk",
    "Remote Admin Assistant", "Junior Research Analyst", "Procurement Assistant", "Project Support Specialist",
]
universities = [
    "Westbridge University", "Lakeside Institute", "North Valley College", "Riverside Technical University",
    "Pinecrest State University", "Grandview College",
]
banks = [
    "Union National Bank", "Cityline Credit Union", "Premier Savings", "First Harbor Bank", "Metropolitan Trust",
]
couriers = ["DHL", "FedEx", "UPS", "USPS", "Royal Mail", "Aramex"]
agencies = [
    "Department of Revenue", "Tax Processing Office", "Immigration Service Desk", "Benefits Administration Office",
]
products = ["CloudSync", "TaskPilot", "MarketPulse", "Reader Weekly", "DevOps Digest", "Studio Notes"]
projects = [
    "Q2 Budget Plan", "Customer Onboarding Flow", "API Reliability Initiative", "Campus Outreach Plan",
    "Product Launch Deck", "Security Audit Checklist", "Renewal Forecast",
]

legit_url_bases = [
    "https://google.com",
    "https://microsoft.com",
    "https://support.microsoft.com",
    "https://calendar.google.com",
    "https://www.linkedin.com",
    "https://www.nasa.gov/news",
    "https://docs.github.com",
    "https://www.coursera.org",
    "https://www.usps.com",
    "https://zoom.us",
    "https://www.apple.com",
]
legit_paths = [
    "security", "help", "account", "calendar", "events", "support", "learn", "docs", "updates", "status",
]
suspicious_left = [
    "secure", "verify", "auth", "billing", "compliance", "identity", "helpdesk", "payment", "portal", "review",
]
suspicious_right = [
    "center", "gateway", "node", "checkpoint", "desk", "service", "form", "scanner", "hub", "panel",
]
suspicious_tlds = [".xyz", ".top", ".site", ".click", ".online", ".live", ".icu", ".biz", ".info"]
suspicious_paths = [
    "login", "verify", "secure", "update", "review", "confirm", "invoice", "track", "claim", "form",
]
short_bases = [
    "https://bit.ly/", "https://tinyurl.com/", "https://t.co/", "https://rb.gy/", "https://rebrand.ly/",
]


def rand_name() -> str:
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def rand_ref(prefix: str) -> str:
    return f"{prefix}-{random.randint(100000, 999999)}"


def random_amount() -> str:
    return random.choice(
        [
            f"${random.randint(200, 9500):,}",
            f"${random.randint(10000, 250000):,}",
            f"{random.randint(1, 7)}.{random.randint(0, 9)} BTC",
            f"{random.randint(5, 25)} ETH",
        ]
    )


def legit_url() -> str:
    base = random.choice(legit_url_bases).rstrip("/")
    if random.random() < 0.65:
        return base
    return f"{base}/{random.choice(legit_paths)}"


def suspicious_url() -> str:
    domain = (
        f"{random.choice(suspicious_left)}-"
        f"{random.choice(suspicious_right)}-"
        f"{random.randint(11, 999)}"
        f"{random.choice(suspicious_tlds)}"
    )
    path = random.choice(suspicious_paths)
    token = "".join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(6, 10)))
    if random.random() < 0.55:
        return f"https://{domain}/{path}?token={token}"
    return f"https://{domain}/{path}/{token}"


def short_url() -> str:
    slug = "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 9)))
    return f"{random.choice(short_bases)}{slug}"


def spam_url() -> str:
    r = random.random()
    if r < 0.62:
        return suspicious_url()
    if r < 0.87:
        return short_url()
    return legit_url()


def ham_url() -> str:
    return legit_url() if random.random() < 0.93 else short_url()


def compose_body(mandatory: list[str], optional: list[str], min_sent: int = 2, max_sent: int = 8) -> str:
    optional_copy = optional[:]
    random.shuffle(optional_copy)
    max_extra = min(len(optional_copy), max_sent - len(mandatory))
    min_extra = max(0, min_sent - len(mandatory))
    if max_extra < min_extra:
        max_extra = min_extra
    extra_count = random.randint(min_extra, max_extra) if max_extra > 0 else 0
    sentences = mandatory + optional_copy[:extra_count]
    return " ".join(sentences)


def gen_phishing(difficulty: str, include_url: bool) -> tuple[str, str]:
    brand = random.choice(["Microsoft 365", "Google Workspace", "Outlook", "Apple ID", "Payroll Portal", "Student SSO"])
    issue = random.choice([
        "an unusual sign-in attempt", "a failed multi-factor challenge", "a password reset request",
        "a new device authorization", "a mailbox sync from an unrecognized IP",
    ])
    window = random.choice(["15 minutes", "30 minutes", "1 hour", "today"])
    subject = random.choice([
        f"{brand} security alert: verify recent activity",
        f"Action required for your {brand} account",
        f"Unusual activity detected on {brand}",
        "Complete account verification to keep access",
    ])

    mandatory = [
        f"We detected {issue} from {random.choice(cities)} on your {brand} account.",
    ]
    if difficulty == "easy":
        mandatory.append(f"Your access may be suspended unless you confirm your credentials within {window}.")
    elif difficulty == "medium":
        mandatory.append(f"Please complete the verification step within {window} to prevent temporary restrictions.")
    else:
        mandatory.append("As part of a routine identity review, confirm your active session credentials.")

    optional = [
        f"Reference number: {rand_ref('SEC')}.",
        "If this was not you, update your password after the review.",
        "Failure to complete the check may limit mailbox functions.",
    ]
    if include_url:
        optional.append(f"Continue here: {spam_url()}.")
    else:
        optional.append("Open the security center and complete the verification checklist.")

    return subject, compose_body(mandatory, optional)


def gen_job_scam(difficulty: str, include_url: bool) -> tuple[str, str]:
    role = random.choice(roles)
    company = random.choice(companies)
    recruiter = rand_name()
    pay = random.choice([f"${random.randint(600, 1800)}/week", f"${random.randint(2500, 7000)}/month", f"${random.randint(35, 90)}/hour"])
    slots = random.randint(2, 25)

    subject = random.choice([
        f"Remote {role} opening - immediate start",
        f"Shortlisted for {role} ({pay})",
        f"Recruiter follow-up: {role} role with {company}",
        f"Urgent hiring: {role} ({slots} seats)",
    ])

    mandatory = [
        f"Hi, this is {recruiter} from {company}; your profile on {random.choice(platforms)} matches our remote {role} position.",
    ]
    if difficulty == "easy":
        mandatory.append(f"No interview is required and you can start this week with compensation around {pay}.")
    elif difficulty == "medium":
        mandatory.append(f"We have {slots} openings, and onboarding closes within {random.choice(['24 hours', '48 hours', 'two business days'])}.")
    else:
        mandatory.append("The client requested a quick onboarding confirmation before assigning project credentials.")

    optional = [
        "Please share your preferred mobile number and current location to complete screening.",
        f"Candidate reference: {rand_ref('JOB')}.",
        "Selected applicants receive orientation details the same day.",
    ]
    if difficulty == "easy":
        optional.append(f"A refundable setup deposit of {random.choice(['$39', '$59', '$79'])} is required after acceptance.")
    if include_url:
        optional.append(f"Submit your details using this application form: {spam_url()}.")
    else:
        optional.append("Reply with your availability window so we can issue your onboarding packet.")

    return subject, compose_body(mandatory, optional)


def gen_impersonation(difficulty: str, include_url: bool) -> tuple[str, str]:
    mode = random.choice(["bank", "university", "hr", "government", "executive"])

    if mode == "bank":
        entity = random.choice(banks)
        subject = random.choice([
            f"{entity}: account ownership confirmation",
            f"Important notice from {entity}",
            "Transaction hold requires verification",
        ])
        mandatory = [
            f"This is an automated notice from {entity} regarding a recent transaction review.",
            "A temporary hold has been placed until ownership confirmation is completed.",
        ]
    elif mode == "university":
        entity = random.choice(universities)
        subject = random.choice([
            f"{entity} portal notice: identity validation",
            "Student mailbox update required",
            "Academic records access review",
        ])
        mandatory = [
            f"The IT office at {entity} flagged your account during a scheduled access audit.",
            "Confirm your credentials to retain access to class systems and library resources.",
        ]
    elif mode == "hr":
        entity = random.choice(companies)
        subject = random.choice([
            "HR compliance update: payroll profile check",
            f"{entity} HR action required",
            "Benefits enrollment confirmation pending",
        ])
        mandatory = [
            "Human Resources is finalizing compliance records for this pay cycle.",
            "Please verify your profile details to avoid payroll processing delays.",
        ]
    elif mode == "government":
        entity = random.choice(agencies)
        subject = random.choice([
            f"Official message from {entity}",
            "Action needed: unresolved filing record",
            "Government notice: account verification",
        ])
        mandatory = [
            f"You are receiving this message from the {entity} concerning your recent filing status.",
            "Your record requires immediate identity confirmation before final processing.",
        ]
    else:
        entity = random.choice(companies)
        subject = random.choice([
            "Confidential: request from executive office",
            "From CFO: urgent vendor payment request",
            "CEO office follow-up needed today",
        ])
        mandatory = [
            f"I am contacting you from the executive office at {entity} and need your immediate assistance.",
            "This request is confidential and should be handled before end-of-day cutoff.",
        ]

    if difficulty == "easy":
        mandatory.append("Respond now to avoid account suspension or compliance penalties.")
    elif difficulty == "medium":
        mandatory.append("Complete the confirmation process as soon as possible to prevent service interruption.")
    else:
        mandatory.append("Please handle this before the reconciliation cycle closes this afternoon.")

    optional = [
        f"Reference: {rand_ref('OFFICIAL')}.",
        "Keep this communication internal until verification is complete.",
        "Failure to respond may trigger additional control checks.",
    ]
    if include_url:
        optional.append(f"Use this secure response portal: {spam_url()}.")
    else:
        optional.append("Reply to this message with confirmation once the action is complete.")

    return subject, compose_body(mandatory, optional)


def gen_financial_investment(difficulty: str, include_url: bool) -> tuple[str, str]:
    scenario = random.choice(["crypto", "investment", "lottery", "inheritance"])

    if scenario == "crypto":
        subject = random.choice([
            "Private crypto allocation invitation",
            "Early access to high-yield trading pool",
            "Digital asset account activation",
        ])
        mandatory = [
            "Our private desk opened a limited digital asset allocation for selected participants.",
            f"Projected payout is {random.choice(['12%', '18%', '26%', '35%'])} per cycle based on current momentum.",
        ]
    elif scenario == "investment":
        subject = random.choice([
            "Guaranteed return opportunity this quarter",
            "Managed portfolio offer with fixed payout",
            "Capital growth invitation",
        ])
        mandatory = [
            "A new managed portfolio window is available for a small group of external clients.",
            f"Minimum contribution is {random.choice(['$500', '$1,000', '$2,500'])} with expected weekly returns.",
        ]
    elif scenario == "lottery":
        subject = random.choice([
            "Prize release notice for selected participant",
            "Lottery claim instruction",
            "You were matched to an unclaimed award",
        ])
        mandatory = [
            f"Your address was included in a regional draw and matched to a pending award of {random_amount()}.",
            "Submit verification details to process transfer and tax clearance.",
        ]
    else:
        subject = random.choice([
            "Inheritance file awaiting beneficiary response",
            "Estate claim processing notice",
            "Final beneficiary confirmation required",
        ])
        mandatory = [
            f"A legal office is processing an estate file listing you as beneficiary for assets valued at {random_amount()}.",
            "Identity confirmation is required before the transfer certificate can be issued.",
        ]

    if difficulty == "easy":
        mandatory.append("Act today to avoid cancellation of this offer.")
    elif difficulty == "medium":
        mandatory.append("Priority processing is available if you complete the intake form promptly.")
    else:
        mandatory.append("We can lock your allocation once compliance checks are completed.")

    optional = [
        f"Tracking code: {rand_ref('FIN')}.",
        "Please keep this opportunity confidential until onboarding is complete.",
        "Reply with your preferred transfer method for settlement.",
    ]
    if include_url:
        optional.append(f"Complete your registration here: {spam_url()}.")
    else:
        optional.append("Reply to this email to receive the next compliance step.")

    return subject, compose_body(mandatory, optional)


def gen_bec(difficulty: str, include_url: bool) -> tuple[str, str]:
    vendor = random.choice(companies)
    amount = random.choice([f"${random.randint(1200, 9900):,}", f"${random.randint(10000, 85000):,}"])
    cutoff = random.choice(["2:00 PM", "3:30 PM", "4:00 PM", "end of day"])
    subject = random.choice([
        f"Invoice update needed before {cutoff}",
        "Urgent transfer request from finance",
        f"Payment instruction for {vendor}",
        f"Vendor settlement approval: {amount}",
    ])

    mandatory = [
        f"Hi, we need to process a payment to {vendor} for {amount} before {cutoff}.",
    ]
    if difficulty == "easy":
        mandatory.append("Please handle this immediately and send confirmation once done.")
    elif difficulty == "medium":
        mandatory.append("The original account details changed during reconciliation, so use the updated instructions.")
    else:
        mandatory.append("Please keep this discreet until the executive review packet is finalized.")

    optional = [
        f"Invoice ID: {rand_ref('INV')}.",
        "The finance lead is currently in transit, so email confirmation is sufficient.",
        "Do not delay this request because the cutoff window is strict.",
    ]
    if include_url:
        optional.append(f"Updated remittance details: {spam_url()}.")
    else:
        optional.append("Reply once the transfer is completed so I can close the ledger item.")

    return subject, compose_body(mandatory, optional)


def gen_delivery_service(difficulty: str, include_url: bool) -> tuple[str, str]:
    courier = random.choice(couriers)
    tracking = f"{random.choice(string.ascii_uppercase)}{random.randint(1000000, 9999999)}{random.choice(string.ascii_uppercase)}"
    service = random.choice(["streaming", "cloud backup", "device protection", "premium workspace", "mailbox archive"])

    if random.random() < 0.55:
        subject = random.choice([
            f"{courier} delivery exception for package {tracking}",
            "Package held due to incomplete address",
            "Action required: reschedule delivery",
        ])
        mandatory = [
            f"Your parcel was held at the regional {courier} hub due to an address validation issue.",
            f"Tracking number {tracking} requires confirmation before redelivery can be scheduled.",
        ]
    else:
        subject = random.choice([
            f"Subscription renewal failed for {service}",
            "Payment method check required to avoid interruption",
            "Service continuity notice",
        ])
        mandatory = [
            f"We could not process the renewal for your {service} plan because billing details need review.",
            "Update payment information to keep the service active without interruption.",
        ]

    if difficulty == "easy":
        mandatory.append("Complete this now to avoid cancellation.")
    elif difficulty == "medium":
        mandatory.append("Please resolve this within the next few hours to prevent additional fees.")
    else:
        mandatory.append("This can be cleared quickly using the verification workflow.")

    optional = [
        f"Case reference: {rand_ref('SRV')}.",
        "Customer support volume is high, so self-service processing is recommended.",
        "If no action is taken, your request may be archived.",
    ]
    if include_url:
        optional.append(f"Manage this request here: {spam_url()}.")
    else:
        optional.append("Reply to this message if you need manual assistance.")

    return subject, compose_body(mandatory, optional)


def gen_social_engineering(difficulty: str, include_url: bool) -> tuple[str, str]:
    event = random.choice([
        "executive training cohort",
        "priority grant shortlist",
        "restricted partner network",
        "beta vendor approval window",
        "leadership mentoring program",
    ])
    authority = random.choice([
        "program office", "selection committee", "compliance board", "regional coordination unit", "executive administration",
    ])
    spots = random.randint(3, 30)

    subject = random.choice([
        f"Final confirmation required: {event}",
        "Official notice: response window closing",
        f"Limited spots remaining ({spots})",
        "Priority action requested by administration",
    ])

    mandatory = [
        f"You were pre-selected by the {authority} for the {event}.",
    ]
    if difficulty == "easy":
        mandatory.append(f"Only {spots} slots remain, so confirm immediately to avoid losing your place.")
    elif difficulty == "medium":
        mandatory.append("The confirmation window closes soon, and late responses are moved to waitlist.")
    else:
        mandatory.append("A quick acknowledgement is needed before your invitation is escalated to standby candidates.")

    optional = [
        f"Notice ID: {rand_ref('AUTH')}.",
        "This invitation is non-transferable and tied to your contact profile.",
        "Please keep this message private until enrollment is finalized.",
    ]
    if include_url:
        optional.append(f"Secure confirmation form: {spam_url()}.")
    else:
        optional.append("Reply with CONFIRM to reserve your place.")

    return subject, compose_body(mandatory, optional)


spam_generators = {
    "phishing": gen_phishing,
    "job_scams": gen_job_scam,
    "impersonation": gen_impersonation,
    "financial_investment": gen_financial_investment,
    "bec": gen_bec,
    "delivery_service": gen_delivery_service,
    "social_engineering": gen_social_engineering,
}


def gen_workplace(include_url: bool) -> tuple[str, str]:
    project = random.choice(projects)
    subject = random.choice([
        f"Update on {project}",
        f"Action items for {project}",
        "Project status and next steps",
        "Follow-up from today's sync",
    ])
    mandatory = [
        f"Hi team, I updated the {project} draft based on today's discussion.",
        f"Please review and share feedback by {random.choice(['Tuesday afternoon', 'end of day Wednesday', 'tomorrow noon', 'Friday morning'])}.",
    ]
    optional = [
        "I'll summarize decisions in the next standup.",
        "Let me know if any dependency timelines need adjustment.",
        f"Reference ID: {rand_ref('WK')}.",
    ]
    if include_url:
        optional.append(f"Document link: {ham_url()}.")
    return subject, compose_body(mandatory, optional)


def gen_meeting(include_url: bool) -> tuple[str, str]:
    subject = random.choice([
        "Meeting invite: weekly planning",
        "Rescheduled sync for product review",
        "Agenda for tomorrow's check-in",
        "Calendar update for stakeholder call",
    ])
    mandatory = [
        f"I moved our meeting to {random.choice(['10:30 AM', '1:00 PM', '3:00 PM', '4:15 PM'])} to accommodate the client call.",
        "The agenda includes status updates, risks, and ownership for next steps.",
    ]
    optional = [
        "Please add any discussion points before the session.",
        "I'll keep the meeting to 30 minutes unless we need deeper review.",
        "Thanks for confirming your availability.",
    ]
    if include_url:
        optional.append(f"Calendar event: {ham_url()}.")
    return subject, compose_body(mandatory, optional)


def gen_academic(include_url: bool) -> tuple[str, str]:
    uni = random.choice(universities)
    subject = random.choice([
        "Course reminder and assignment timeline",
        "Seminar reading list update",
        "Office hours availability this week",
        "Research group meeting note",
    ])
    mandatory = [
        f"Hello, this is a reminder from {uni} about upcoming coursework and deadlines.",
        f"Please submit your draft by {random.choice(['Monday', 'Wednesday', 'Friday'])} so I can provide feedback before grading.",
    ]
    optional = [
        "Office hours are open for students who want to discuss methodology questions.",
        "If you need an extension, send a brief request with your progress summary.",
        "Thank you for staying on schedule this term.",
    ]
    if include_url:
        optional.append(f"Course portal: {ham_url()}.")
    return subject, compose_body(mandatory, optional)


def gen_friendly(include_url: bool) -> tuple[str, str]:
    subject = random.choice([
        "Quick check-in",
        "Weekend plan update",
        "Thanks again for your help",
        "Catching up soon?",
    ])
    mandatory = [
        "Hey, just wanted to check in and see how your week is going.",
        f"I'm around {random.choice(['Saturday afternoon', 'Sunday evening', 'after work tomorrow'])} if you want to catch up.",
    ]
    optional = [
        "No rush on replying, just thought I'd send a quick note.",
        "I finally tried that place you recommended and it was great.",
        "Hope everything is going smoothly on your side.",
    ]
    if include_url:
        optional.append(f"I found this and thought of you: {ham_url()}.")
    return subject, compose_body(mandatory, optional)


def gen_newsletter(include_url: bool) -> tuple[str, str]:
    product = random.choice(products)
    subject = random.choice([
        f"{product} weekly highlights",
        "Community roundup and product updates",
        "What's new this week",
        "Monthly digest",
    ])
    mandatory = [
        f"Welcome to this week's {product} update with product improvements and community news.",
        "We included release notes, upcoming events, and a few recommended resources.",
    ]
    optional = [
        "You can adjust notification preferences at any time.",
        "Thanks for reading and sharing feedback with the team.",
        "We'll be back next week with another roundup.",
    ]
    if include_url:
        optional.append(f"Read more: {ham_url()}.")
    return subject, compose_body(mandatory, optional)


ham_generators = {
    "workplace": gen_workplace,
    "meeting": gen_meeting,
    "academic": gen_academic,
    "friendly": gen_friendly,
    "newsletter": gen_newsletter,
}

labels = ["spam"] * add_spam + ["ham"] * add_ham
random.shuffle(labels)

remaining_spam_rows = add_spam
remaining_ham_rows = add_ham
remaining_spam_urls = spam_url_target
remaining_ham_urls = ham_url_target

with dataset_path.open("a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for label in labels:
        if label == "spam":
            include_url = should_include_url(remaining_spam_rows, remaining_spam_urls)
            category = pick_category(spam_category_remaining)
            difficulty = random.choices(["easy", "medium", "hard"], weights=[0.30, 0.40, 0.30], k=1)[0]
            subject, body = spam_generators[category](difficulty, include_url)
            writer.writerow(["spam", subject, body])
            remaining_spam_rows -= 1
            if include_url:
                remaining_spam_urls -= 1
        else:
            include_url = should_include_url(remaining_ham_rows, remaining_ham_urls)
            category = pick_category(ham_category_remaining)
            subject, body = ham_generators[category](include_url)
            writer.writerow(["ham", subject, body])
            remaining_ham_rows -= 1
            if include_url:
                remaining_ham_urls -= 1

final_total = 0
final_spam = 0
final_ham = 0
final_url_rows = 0

with dataset_path.open("r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        final_total += 1
        label = (row.get("label") or "").strip().lower()
        if label == "spam":
            final_spam += 1
        elif label == "ham":
            final_ham += 1
        if has_url(f"{row.get('subject', '')} {row.get('body', '')}"):
            final_url_rows += 1

print(
    f"Appended {rows_to_add} rows. Final total={final_total}, spam={final_spam}, ham={final_ham}, "
    f"url_rows={final_url_rows} ({(final_url_rows / final_total) * 100:.2f}%)."
)
