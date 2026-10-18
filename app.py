import sqlite3
from datetime import date, datetime, time
from pathlib import Path

import streamlit as st
from PIL import Image

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "food_donations.db"

st.set_page_config(
    page_title="Smart Food Waste Management System",
    page_icon="🥗",
    layout="wide",
)

# -------------------- Database --------------------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                food_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                location TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'Available',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

def add_donation(data):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO donations
            (donor_name, contact, food_name, category, quantity, unit,
             location, expiry_date, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?)
            """,
            (
                data["donor_name"], data["contact"], data["food_name"],
                data["category"], data["quantity"], data["unit"],
                data["location"], data["expiry_date"], data["notes"],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()

def get_donations(status=None):
    with get_connection() as conn:
        if status and status != "All":
            rows = conn.execute(
                """SELECT id, donor_name, contact, food_name, category, quantity,
                          unit, location, expiry_date, notes, status, created_at
                   FROM donations WHERE status = ? ORDER BY id DESC""",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, donor_name, contact, food_name, category, quantity,
                          unit, location, expiry_date, notes, status, created_at
                   FROM donations ORDER BY id DESC"""
            ).fetchall()
    columns = [
        "ID", "Donor", "Contact", "Food", "Category", "Quantity", "Unit",
        "Location", "Expiry", "Notes", "Status", "Created at"
    ]
    return [dict(zip(columns, row)) for row in rows]

def update_status(donation_id, status):
    with get_connection() as conn:
        conn.execute(
            "UPDATE donations SET status = ? WHERE id = ?",
            (status, donation_id),
        )
        conn.commit()

def delete_donation(donation_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM donations WHERE id = ?", (donation_id,))
        conn.commit()

init_db()

# -------------------- AI image classifier --------------------
@st.cache_resource(show_spinner=False)
def load_classifier():
    # Downloads the model on first use; internet is required for this step.
    from transformers import pipeline
    return pipeline("image-classification", model="nateraw/food")

def classify_food(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    with st.spinner("Loading the AI model and classifying the image..."):
        classifier = load_classifier()
        results = classifier(image, top_k=3)
    return image, results

# -------------------- Layout --------------------
st.title("Smart Food Waste Management System")
st.caption("Manage surplus food, support donations, and explore AI-powered food image classification.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Choose a page",
        ["Dashboard", "AI Food Classifier", "Add Donation", "Available Food", "Manage Donations"],
    )
    st.divider()
    st.caption("Academic prototype. Confirm food quality, storage, and safety separately before donation.")

if page == "Dashboard":
    donations = get_donations()
    available = [d for d in donations if d["Status"] == "Available"]
    collected = [d for d in donations if d["Status"] == "Collected"]
    expired = [
        d for d in available
        if d["Expiry"] and d["Expiry"] < datetime.now().isoformat(timespec="minutes")
    ]
    total_available = sum(float(d["Quantity"]) for d in available)

    st.subheader("Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total listings", len(donations))
    c2.metric("Available listings", len(available))
    c3.metric("Collected listings", len(collected))
    c4.metric("Available quantity", f"{total_available:g}")

    st.info("Expiry times are entered by donors. This app does not inspect food safety or guarantee that food is suitable for consumption.")
    st.subheader("Recent donations")
    if donations:
        st.dataframe(
            [
                {k: d[k] for k in ["ID", "Food", "Category", "Quantity", "Unit", "Location", "Expiry", "Status"]}
                for d in donations[:10]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No donations have been added yet. Open **Add Donation** to create your first listing.")

elif page == "AI Food Classifier":
    st.subheader("AI Food Image Classifier")
    st.write("Upload an image to get the model's best food-label predictions.")
    uploaded = st.file_uploader("Choose a food image", type=["jpg", "jpeg", "png", "webp"])

    if uploaded:
        try:
            image, results = classify_food(uploaded)
            left, right = st.columns([1, 1])
            with left:
                st.image(image, caption="Uploaded image", use_container_width=True)
            with right:
                st.markdown("**Top predictions**")
                for result in results:
                    label = result["label"].replace("_", " ").title()
                    st.write(f"**{label}** — {result['score']:.1%}")
                st.caption("Predictions may be wrong. Check the label before using it in a donation listing.")
                top_label = results[0]["label"].replace("_", " ").title() if results else ""
                if st.button("Use top prediction in donation form"):
                    st.session_state["suggested_food_name"] = top_label
                    st.session_state["suggested_category"] = "AI-predicted"
                    st.success("Prediction saved for this session. Open Add Donation and review the suggested food name.")
        except Exception as exc:
            st.error("The AI model could not be loaded or run.")
            st.write("Check your internet connection and installed packages, then try again.")
            st.caption(f"Technical detail: {exc}")
    else:
        st.write("Tip: use a clear image with one main food item for a better prediction.")

elif page == "Add Donation":
    st.subheader("Add a surplus food donation")
    st.write("Enter the details below. Fields marked with * are required.")

    with st.form("donation_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            donor_name = st.text_input("Donor name *")
            contact = st.text_input("Contact number or email *")
            food_name = st.text_input(
                "Food name *",
                value=st.session_state.get("suggested_food_name", ""),
            )
            category = st.selectbox(
                "Food category *",
                ["Cooked meal", "Fruit", "Vegetable", "Bakery", "Packaged food", "Grains", "Other", "AI-predicted"],
                index=7 if st.session_state.get("suggested_category") == "AI-predicted" else 0,
            )
        with c2:
            quantity = st.number_input("Quantity *", min_value=0.1, value=1.0, step=0.5)
            unit = st.selectbox("Quantity unit *", ["kg", "servings", "packets", "boxes", "litres"])
            location = st.text_input("Pickup location *")
            expiry_day = st.date_input("Use-by / pickup deadline date *", min_value=date.today())
            expiry_time = st.time_input("Deadline time *", value=time(18, 0))
        notes = st.text_area("Additional notes (optional)", placeholder="Storage details, allergens, pickup instructions, etc.")
        submitted = st.form_submit_button("Save donation", type="primary")

    if submitted:
        missing = []
        if not donor_name.strip(): missing.append("donor name")
        if not contact.strip(): missing.append("contact")
        if not food_name.strip(): missing.append("food name")
        if not location.strip(): missing.append("pickup location")
        expiry = datetime.combine(expiry_day, expiry_time).isoformat(timespec="minutes")
        if expiry < datetime.now().isoformat(timespec="minutes"):
            st.error("Please choose a future deadline.")
        elif missing:
            st.error("Please fill in: " + ", ".join(missing) + ".")
        else:
            add_donation({
                "donor_name": donor_name.strip(),
                "contact": contact.strip(),
                "food_name": food_name.strip(),
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "location": location.strip(),
                "expiry_date": expiry,
                "notes": notes.strip(),
            })
            st.success("Donation saved successfully!")
            st.session_state.pop("suggested_food_name", None)
            st.session_state.pop("suggested_category", None)

elif page == "Available Food":
    st.subheader("Available food donations")
    available = get_donations("Available")
    if not available:
        st.info("There are no available listings yet.")
    else:
        search = st.text_input("Search by food or location")
        filtered = [
            d for d in available
            if search.lower() in d["Food"].lower() or search.lower() in d["Location"].lower()
        ]
        for item in filtered:
            with st.container(border=True):
                st.markdown(f"### {item['Food']}  ·  {item['Quantity']:g} {item['Unit']}")
                st.write(f"**Category:** {item['Category']}  |  **Pickup location:** {item['Location']}")
                st.write(f"**Deadline:** {item['Expiry']}")
                st.write(f"**Donor:** {item['Donor']}  |  **Contact:** {item['Contact']}")
                if item["Notes"]:
                    st.write(f"**Notes:** {item['Notes']}")
                st.caption("Contact the donor to coordinate collection. Confirm food safety and storage before accepting.")

elif page == "Manage Donations":
    st.subheader("Manage donation records")
    all_donations = get_donations()
    if not all_donations:
        st.info("No donation records are available.")
    else:
        st.dataframe(
            [
                {k: d[k] for k in ["ID", "Donor", "Food", "Quantity", "Unit", "Location", "Expiry", "Status"]}
                for d in all_donations
            ],
            use_container_width=True,
            hide_index=True,
        )
        ids = [d["ID"] for d in all_donations]
        selected_id = st.selectbox("Select donation ID", ids)
        selected = next(d for d in all_donations if d["ID"] == selected_id)
        st.write(f"Selected: **{selected['Food']}** — currently **{selected['Status']}**")
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox("Change status to", ["Available", "Reserved", "Collected", "Cancelled"])
            if st.button("Update status", type="primary"):
                update_status(selected_id, new_status)
                st.success("Donation status updated.")
                st.rerun()
        with c2:
            confirm_delete = st.checkbox("I understand this permanently deletes the selected record")
            if st.button("Delete selected donation", disabled=not confirm_delete):
                delete_donation(selected_id)
                st.success("Donation deleted.")
                st.rerun()

st.divider()
st.caption("Smart Food Waste Management System · Student project prototype")
